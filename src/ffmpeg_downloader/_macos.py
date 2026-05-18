from __future__ import annotations

import os
import zipfile
from os import path
from shutil import copyfileobj
from typing import Literal

from packaging.version import Version
from typing_extensions import LiteralString  # <3.11

from ._config import Build, ConfigBase, SingletonMeta
from ._download_helper import chmod
from ._providers import evermeet, osxexperts

home_url = ""


def detect_version(
    ver_str: str,
) -> tuple[Version | Literal["snapshot"], LiteralString, LiteralString] | None:
    """detect version, provider, and build type

    :param ver_str: `ffmpeg -version` output string
    :return: a tuple of version, provider, and build type or None if no match found
    """

    print("detect_version")
    print(ver_str)

    return evermeet.detect_version(ver_str)


class Config(ConfigBase, metaclass=SingletonMeta):
    @property
    def providers(self) -> list[LiteralString]:
        """Default build type keyed by provider name"""
        return [evermeet.provider, osxexperts.provider]

    @property
    def default_provider(self) -> LiteralString:
        """Default provider name"""
        return osxexperts.provider

    @property
    def build_types(self) -> dict[LiteralString, list[LiteralString]]:
        """Default build type keyed by provider name"""
        return {
            osxexperts.provider: osxexperts.build_types,
            evermeet.provider: evermeet.build_types,
        }

    @property
    def default_build_type(self) -> dict[LiteralString, LiteralString]:
        """Default build type keyed by provider name"""
        return {
            evermeet.provider: evermeet.default_build,
            osxexperts.provider: osxexperts.default_build,
        }

    def _gather_builds(
        self, need_releases: bool = False, need_nightly: bool = False
    ) -> tuple[list[Build], list[Build]]:
        """gather Linux build info

        :param need_releases: True to require release info to be retrieved, defaults to False
        :param need_nightly: True to require nightly info to be retrieved (if available), defaults to False
        :return release_catalog: list of release build info objects
        :return nightly_catalog: list of nightly build info objects

        """

        osxexperts_releases, _ = osxexperts.gather_builds(
            osxexperts.os_arch(), True, self._requests_kws
        )

        try:
            # evermeet.cx (amd64 only)
            evermeet_releases, nightly = evermeet.gather_builds(
                evermeet.os_arch(), False, self._requests_kws
            )
        except:
            # arm64 not supported
            evermeet_releases = []
            nightly = []

        return [*evermeet_releases, *osxexperts_releases], nightly


def extract(zippaths, dst, progress=None):

    fzips = []
    try:
        for zippath in zippaths:
            fzips.append(zipfile.ZipFile(zippath, "r"))

        if progress is None:
            for f in fzips:
                f.extractall(dst)
        else:
            progress = progress(
                sum(getattr(i, "file_size", 0) for f in fzips for i in f.infolist())
            )
            for f in fzips:
                for i in f.infolist():
                    if i.filename in ("ffmpeg", "ffprobe", "ffplay"):
                        with (
                            f.open(i) as fi,
                            open(path.join(dst, i.filename), "wb") as fo,
                        ):
                            copyfileobj(progress.io_wrapper(fi), fo)
                        break
    finally:
        for f in fzips:
            f.close()

    # make sure binaries are executable
    for name in ("ffmpeg", "ffprobe", "ffplay"):
        chmod(path.join(dst, name))

    return dst


def set_symlinks(binpaths):
    raise NotImplementedError("--set_symlinks option is not supported on Mac")


def clr_symlinks(symlinks):
    pass


def get_profile():
    file = ".bash_profile" if os.environ["SHELL"] == "/bin/bash" else ".zsh_profile"
    return path.join(path.expanduser("~"), file)


def append_envvar(name, value):
    filename = get_profile()
    with open(filename, "at") as f:
        f.write(f'export {name}="{value}"\n')


def get_envvar(name):
    filename = get_profile()
    print(filename)
    try:
        with open(filename, "rt") as f:
            lines = f.readlines()
    except:
        lines = []
    i = next((i for i, l in enumerate(lines) if l.startswith(f"export {name}=")), -1)
    if i < 0:
        return ""
    value = lines[i].split("=", 1)[1][:-1]
    return value[1:-1] if value[0] == '"' else value


def set_envvar(name, value):
    filename = get_profile()
    try:
        with open(filename, "rt") as f:
            lines = f.readlines()
    except:
        lines = []

    i = next((i for i, l in enumerate(lines) if l.startswith(f"export {name}=")), -1)
    if i >= 0:
        lines.pop(i)
    if value is not None:
        lines.append(f'export {name}="{value}"\n')

    with open(filename, "wt") as f:
        f.writelines(lines)


def set_env_path(dir):

    user_path = get_envvar("PATH")
    dirs = user_path.split(os.pathsep) if user_path else []
    if dir not in dirs:
        dirs = [dir, *dirs]
        if "${PATH}" not in dirs:
            dirs.append("${PATH}")
        set_envvar("PATH", os.pathsep.join(dirs))


def clr_env_path(dir):
    user_path = get_envvar("PATH")
    dirs = user_path.split(os.pathsep) if user_path else []
    if dir in dirs:
        if len(dirs) > 2:
            dirs.remove(dir)
            set_envvar("PATH", os.pathsep.join(dirs))
        else:
            set_envvar("PATH", None)


def set_env_vars(vars, bindir):
    raise NotImplementedError("--set_symlinks option is not supported on Mac")


def clr_env_vars(vars):
    pass


def get_bindir(install_dir):
    return path.join(install_dir, "ffmpeg")


def get_binpath(install_dir, app):
    return path.join(install_dir, "ffmpeg", app)
