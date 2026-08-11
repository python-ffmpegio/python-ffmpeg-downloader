from __future__ import annotations

import abc
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from os import path
from pickle import dump, load
from typing import Literal

from packaging.version import Version
from typing_extensions import (
    LiteralString,  # <3.11
    TypedDict,  # <3.12
)

from ._path import get_cache_dir, get_dir


def _config_file():
    return path.join(get_dir(), "config.data")


@dataclass(frozen=True, slots=True)
class BuildFile:
    name: str
    url: str
    size: int | None = None


@dataclass(frozen=True, slots=True)
class Build:
    provider: Literal["gyan", "btbn", "johnvansickle", "evermeet", "osxexperts"]
    build_type: LiteralString | None
    os: Literal["Linux", "Windows", "Darwin"]
    arch: Literal["x86_64", "AMD64", "ARM64", "arm64", "aarch64"]
    version: Version | Literal["latest"]
    files: tuple[BuildFile]
    mime_type: str

    @property
    def cached(self) -> bool:
        return all(
            os.path.exists(os.path.join(get_cache_dir(), file.name))
            for file in self.files
        )


class InstallSetup(TypedDict):
    set_path: bool
    env_vars: str
    symlinks: str


class SingletonMeta(abc.ABCMeta):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            # Construct and initialize the object only once
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]


class ConfigBase(metaclass=abc.ABCMeta):
    """class protocol to manage various builds available to download"""

    _releases: list[Build]
    last_updated: datetime

    _nightly: list[Build]

    install_setup: InstallSetup

    dirty: bool
    cached: set[Build]
    _max_retries: int | None
    _requests_kws: dict

    def __init__(self, max_retries: int | None = None, **requests_kws):
        """
        :param **requests_kws: keyword arguments to be sent to requests html transaction
        """
        self._releases = []
        self._nightly = []
        self.last_updated = datetime.fromtimestamp(0)
        self.cached = set()
        self.install_setup = {}
        self.dirty = False
        self._max_retries = max_retries
        self._requests_kws = requests_kws

        # create the app data directory
        os.makedirs(get_dir(), exist_ok=True)

        # load saved data
        self.revert()

    @property
    @abc.abstractmethod
    def providers(self) -> list[LiteralString]:
        """Default build type keyed by provider name"""

    @property
    @abc.abstractmethod
    def default_provider(self) -> LiteralString:
        """Default provider name"""

    @property
    @abc.abstractmethod
    def build_types(self) -> dict[LiteralString, list[LiteralString]]:
        """Default build type keyed by provider name"""

    @property
    @abc.abstractmethod
    def default_build_type(self) -> dict[LiteralString, LiteralString]:
        """Default build type keyed by provider name"""

    @property
    def releases(self) -> list[Build]:
        """all release builds available"""
        self.update_builds(need_releases=True)
        return self._releases

    @property
    def latest_releases(self) -> list[Build]:
        """builds of the latest releases"""
        ver = self.latest_release_version
        return [r for r in self.releases if r.version == ver]

    @property
    def latest_release_version(self) -> Version:
        """latest release version"""

        return max(r.version for r in self.releases)

    @property
    def latest_snapshot(self) -> list[Build]:
        """list of all builds of the latest snapshot (nightly)"""

        if not self._nightly:
            # get releases too if stale
            self.update_builds(need_nightly=True)

        return self._nightly

    def update_builds(
        self,
        need_releases: bool = False,
        need_nightly: bool = False,
        forced: bool = False,
    ):
        """update build info

        :param need_releases: True to require release info to be retrieved, defaults to False
        :param need_nightly: True to require nightly info to be retrieved (if available), defaults to False
        :param requests_kws: keyword arguments to be sent to requests html transaction, defaults to None

        updates self._releases and/or self._nightly lists of builds
        """

        update = forced or self.is_stale()

        if update:
            # set aside the cached
            cached_releases = set(b for b in self._releases if b.cached)

            releases, nightly = self._gather_builds(
                need_releases=need_releases, need_nightly=need_nightly
            )

            if releases:
                self._releases = list(cached_releases | set(releases))
                self.last_updated = datetime.now()

            if nightly:
                self._nightly = nightly

            self.dirty = True

    @abc.abstractmethod
    def _gather_builds(
        self, need_releases: bool = False, need_nightly: bool = False
    ) -> tuple[list[Build], list[Build]]:
        """(abstract) gather build info (OS dependent)

        :param need_releases: True to require release info to be retrieved, defaults to False
        :param need_nightly: True to require nightly info to be retrieved (if available), defaults to False
        :param requests_kws: keyword arguments to be sent to requests html transaction, defaults to None
        :return releases: list of release builds
        :return nightly: list of nightly builds
        """

    def get_download_info(
        self,
        version: Version | Literal["snapshot"],
        build_type: LiteralString | None = None,
    ) -> Build:
        """find build information

        :param version: FFmpeg version or 'snapshot' to retrieve the latest nightly build
        :param build_type: Provider's build type, defaults to use the default
        :return: Build information dataclass
        """

        try:
            builds = self.nightly if version == "snapshot" else self.releases[version]
        except KeyError as e:
            raise ValueError(f"{version=} is not available.") from e

        btype = self.default_build_type if build_type is None else build_type

        try:
            return next(b for b in builds if b.build_type == btype)
        except StopIteration as e:
            raise ValueError(f"{build_type=} is not available.") from e

    def revert(self):
        """load config from the saved file"""
        try:
            with open(_config_file(), "rb") as f:
                data = load(f)

            # version check
            if isinstance(data["releases"], dict):
                # incompatible old release format
                data["last_updated"] = None
                data["releases"] = []
                data["nightly"] = []

        except (ModuleNotFoundError, FileNotFoundError):
            data = {
                "last_updated": None,
                "releases": [],
                "nightly": [],
                "install_setup": {},
            }

        self.last_updated = data["last_updated"]
        self._releases = data["releases"]
        self._nightly = data["nightly"]
        self.install_setup = data.get("install_setup", None)
        self.dirty = False

    def dump(self):
        """dump current config to file"""
        if not self.dirty:
            return

        data = {
            "last_updated": self.last_updated,
            "releases": self._releases,
            "nightly": self._nightly,
            "install_setup": self.install_setup,
        }

        with open(_config_file(), "wb") as f:
            dump(data, f)
        self.dirty = False

    def is_stale(self, stale_in=1):
        try:
            return datetime.now() - timedelta(stale_in) > self.last_updated
        except:
            return True

    def force_expiration(self):
        """nullify the last update and trigger for another"""
        self.last_updated = datetime.fromtimestamp(0)
