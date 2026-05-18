from __future__ import annotations

import os
import subprocess as sp
import winreg
import zipfile
from os import path
from shutil import copyfileobj
from typing import Literal

from packaging.version import Version
from typing_extensions import LiteralString  # <3.11

from ._config import Build, ConfigBase, SingletonMeta
from ._providers import btbn, gyan

home_url = ""


def detect_version(
    ver_str: str,
) -> tuple[Version | Literal["snapshot"], LiteralString, LiteralString] | None:
    """detect version, provider, and build type

    :param ver_str: `ffmpeg -version` output string
    :return: a tuple of version, provider, and build type or None if no match found
    """

    return btbn.detect_version(ver_str) or gyan.detect_version(ver_str)


class Config(ConfigBase, metaclass=SingletonMeta):
    @property
    def providers(self) -> list[LiteralString]:
        """Default build type keyed by provider name"""
        return [btbn.provider, gyan.provider]

    @property
    def default_provider(self) -> LiteralString:
        """Default provider name"""
        return btbn.provider

    @property
    def build_types(self) -> dict[LiteralString, list[LiteralString]]:
        """Default build type keyed by provider name"""
        return {btbn.provider: btbn.build_types, gyan.provider: gyan.build_types}

    @property
    def default_build_type(self) -> dict[LiteralString, LiteralString]:
        """Default build type keyed by provider name"""
        return {btbn.provider: btbn.default_build, gyan.provider: gyan.default_build}

    def _gather_builds(
        self, need_releases: bool = False, need_nightly: bool = False
    ) -> tuple[list[Build], list[Build]]:
        """gather Linux build info

        :param need_releases: True to require release info to be retrieved, defaults to False
        :param need_nightly: True to require nightly info to be retrieved (if available), defaults to False
        :return release_catalog: list of release build info objects
        :return nightly_catalog: list of nightly build info objects

        """

        # github.com/BtbN/FFmpeg-Builds
        btbn_releases, nightly = btbn.gather_builds(
            btbn.os_arch(), False, self._requests_kws
        )

        # gyan.dev | github.com/GyanD/codexffmpeg
        try:
            gyan_releases, _ = gyan.gather_builds(
                gyan.os_arch(), True, self._requests_kws
            )
        except RuntimeError:
            # arm64 not supported
            gyan_releases = []

        return [*gyan_releases, *btbn_releases], nightly


def extract(zippaths, dst, progress=None):
    zippath = zippaths[0]

    with zipfile.ZipFile(zippath, "r") as f:
        if progress is None:
            f.extractall(dst)
        else:
            progress = progress(sum(getattr(i, "file_size", 0) for i in f.infolist()))
            for i in f.infolist():
                if not getattr(i, "file_size", 0):  # directory
                    f.extract(i, dst)
                else:
                    with f.open(i) as fi, open(path.join(dst, i.filename), "wb") as fo:
                        copyfileobj(progress.io_wrapper(fi), fo)

    return os.listdir(dst)[0]


def set_symlinks(binpaths):
    raise NotImplementedError("--set_symlinks option is not supported on Windows")


def clr_symlinks(symlinks):
    pass


env_keys = winreg.HKEY_CURRENT_USER, "Environment"


def get_env(name):
    try:
        with winreg.OpenKey(*env_keys, 0, winreg.KEY_READ) as key:
            return winreg.QueryValueEx(key, name)[0]
    except FileNotFoundError:
        return ""


def set_env_path(dir):
    user_path = get_env("Path")
    if dir not in user_path:
        sp.run(["setx", "Path", user_path + os.pathsep + dir], stdout=sp.DEVNULL)


def clr_env_path(dir):
    user_path = get_env("Path")
    parts = user_path.split(os.pathsep + dir)
    if len(parts) > 1:
        sp.run(["setx", "Path", "".join(parts)], stdout=sp.DEVNULL)


def set_env_vars(vars, bindir):
    for k, v in vars.items():
        if get_env(k) != v:
            sp.run(
                f"setx {k} {bindir if v == 'path' else get_binpath(bindir, v)}",
                stdout=sp.DEVNULL,
            )


def clr_env_vars(vars):
    with winreg.OpenKey(*env_keys, 0, winreg.KEY_ALL_ACCESS) as key:
        for name in vars:
            try:
                winreg.DeleteValue(key, name)
            except FileNotFoundError:
                pass


def get_bindir(install_dir):
    return path.join(install_dir, "ffmpeg", "bin")


def get_binpath(install_dir, app):
    return path.join(install_dir, "ffmpeg", "bin", app + ".exe")
