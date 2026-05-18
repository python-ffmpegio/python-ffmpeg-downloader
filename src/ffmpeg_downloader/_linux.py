from __future__ import annotations

import os
import tarfile
from shutil import copyfileobj
from typing import Literal

from packaging.version import Version
from typing_extensions import LiteralString  # <3.11

from ._config import Build, ConfigBase, SingletonMeta
from ._download_helper import chmod
from ._providers import btbn
from ._providers import johnvansickle as jvs

home_url = ""


def detect_version(
    ver_str: str,
) -> tuple[Version | Literal["snapshot"], LiteralString, LiteralString] | None:
    """detect version, provider, and build type

    :param ver_str: `ffmpeg -version` output string
    :return: a tuple of version, provider, and build type or None if no match found
    """

    return btbn.detect_version(ver_str) or jvs.detect_version(ver_str)


class Config(ConfigBase, metaclass=SingletonMeta):
    @property
    def providers(self) -> list[LiteralString]:
        """Default build type keyed by provider name"""
        return [btbn.provider, jvs.provider]

    @property
    def default_provider(self) -> LiteralString:
        """Default provider name"""
        return btbn.provider

    @property
    def build_types(self) -> dict[LiteralString, list[LiteralString]]:
        """Default build type keyed by provider name"""
        return {btbn.provider: btbn.build_types, jvs.provider: jvs.build_types}

    @property
    def default_build_type(self) -> dict[LiteralString, LiteralString]:
        """Default build type keyed by provider name"""
        return {btbn.provider: btbn.default_build, jvs.provider: jvs.default_build}

    def _gather_builds(
        self, need_releases: bool = False, need_nightly: bool = False
    ) -> tuple[list[Build], list[Build]]:
        """gather Linux build info

        :param need_releases: True to require release info to be retrieved, defaults to False
        :param need_nightly: True to require nightly info to be retrieved (if available), defaults to False
        :return release_catalog: list of release build info objects
        :return nightly_catalog: list of nightly build info objects

        """

        # johnvansickle.com
        jvs_releases, _ = jvs.gather_builds(jvs.os_arch(), True, self._requests_kws)

        # github.com/BtbN/FFmpeg-Builds
        btbn_releases, nightly = btbn.gather_builds(
            btbn.os_arch(), False, self._requests_kws
        )

        nightly = [b for b in nightly if b.version == "master"]

        return [*jvs_releases, *btbn_releases], nightly


def is_within_directory(directory, target):

    abs_directory = os.path.abspath(directory)
    abs_target = os.path.abspath(target)

    prefix = os.path.commonprefix([abs_directory, abs_target])

    return prefix == abs_directory


def extract(tarpaths, dst, progress=None):

    # expects only 1 file
    assert len(tarpaths) == 1, (
        "Unknown Linux binary provider: more than 1 tarball given."
    )
    tarpath = tarpaths[0]

    with tarfile.open(tarpath, "r") as f:
        sz = 0
        for member in f.getmembers():
            member_path = os.path.join(tarpath, member.name)
            if not is_within_directory(tarpath, member_path):
                raise Exception("Attempted Path Traversal in Tar File")
            sz += member.size

        if progress is None:
            f.extractall(dst)
        else:
            progress = progress(sz)
            for member in f.getmembers():
                if member.isfile():
                    with open(os.path.join(dst, member.name), "wb") as fo:
                        copyfileobj(progress.io_wrapper(f.extractfile(member)), fo)
                else:
                    f.extract(member, dst)

    # grab the extracted folder name
    dstsub = os.listdir(dst)[0]

    # make sure binaries are executable
    for root, _, files in os.walk(os.path.join(dst, dstsub)):
        if "ffmpeg" not in files:
            continue

        chmod(os.path.join(root, "ffmpeg"))
        for name in ("ffprobe", "ffplay"):
            if name in files:
                chmod(os.path.join(root, name))

    return dstsub


def set_symlinks(binpaths):

    user_home = os.path.expanduser("~")
    user_bindirs = [
        os.path.join(user_home, ".local", "bin"),
        os.path.join(user_home, "bin"),
    ]
    d = next(
        (d for d in user_bindirs if os.path.isdir(d)),
        None,
    )
    if d is None:
        d = user_bindirs[0]
        os.makedirs(d, exist_ok=True)
        print(
            "!!!Created ~/.local/bin. Must log out and back in for the setting to take effect (or update .profile or .bashrc).!!!"
        )

    symlinks = {name: os.path.join(d, name) for name in binpaths}
    for name, binpath in binpaths.items():
        err = True
        if os.path.isfile(binpath):  # ffplay is not included
            try:
                os.symlink(binpath, symlinks[name])
                err = False
            except FileExistsError:
                # already symlinked (or file placed by somebody else)
                pass
        if err:
            del symlinks[name]
    return symlinks


def clr_symlinks(symlinks):
    for link in symlinks.values():
        os.unlink(link)


def set_env_path(dir):
    raise NotImplementedError(
        "--add-path option is not supported in Linux (Automatically added via symlink. Use --no-symlinks to disable.)."
    )


def clr_env_path(dir):
    pass


def set_env_vars(vars, bindir):
    raise NotImplementedError("--set-env option is not supported in Linux.")


def clr_env_vars(vars):
    pass


def get_bindir(install_dir: str) -> str:
    ffmpegdir = os.path.join(install_dir, "ffmpeg")
    bindir = os.path.join(ffmpegdir, "bin")
    return bindir if os.path.exists(bindir) else ffmpegdir


def get_binpath(install_dir: str, app: Literal["ffmpeg", "ffprobe", "ffplay"]) -> str:
    binpath = os.path.join(get_bindir(install_dir), app)
    return binpath if os.path.exists(binpath) else ""
