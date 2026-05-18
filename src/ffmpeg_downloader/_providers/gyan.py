from __future__ import annotations

import platform
import re
from typing import Literal, get_args

from packaging.version import Version
from typing_extensions import LiteralString  # <3.11

from .. import _gh as gh
from .._config import Build, BuildFile

provider = "gyan"

BuildType = Literal["full", "full-shared", "essential"]

build_types = [*get_args(BuildType)]
default_build = get_args(BuildType)[0]

ArchType = Literal["amd64"]


asset_names = {
    "essentials_build": "essentials",
    "full_build": "full",
    "shared": "full-shared",
}


home_url = "https://www.gyan.dev/ffmpeg/builds"
base_url = "https://www.gyan.dev/ffmpeg/builds"
api_url = "https://api.github.com/repos/GyanD/codexffmpeg"
gh_url = "https://github.com/GyanD/codexffmpeg/releases/download/"  # 8.1.1/ffmpeg-8.1.1-full_build.zip"

asset_type = "application/x-zip-compressed"

re_latest_name = re.compile(r"ffmpeg-.+?-(full|essentials)_build.zip")
re_name = re.compile(r"ffmpeg-([.\d]+?)-(full|essentials)_build(-shared)?.zip")


def detect_version(
    ver_str: str,
) -> tuple[Version | Literal["snapshot"], LiteralString, LiteralString] | None:
    """detect version, provider, and build type

    :param ver_str: `ffmpeg -version` output string
    :return: a tuple of version, provider, and build type or None if no match found
    """

    ver_line, config_lines = ver_str.split("\n", 1)

    # BtbN version string ends with a 10-digit git commit hash followed by a date code
    m = re.match(
        r"ffmpeg version (.+?)-(full|essentials)_build-www.gyan.dev Copyright", ver_line
    )
    if m is None:
        return None

    # resolve the version
    ver = m[1]
    build_type = m[2]
    if m := re.match(r"([.\d]+)$", ver):
        # a release branch build, use post## protocol to specify the n-th commit of the branch
        ver = Version(m[1])
    elif m := re.match(r"([2-9]\d{3}-[01]\d-[0-3]\d-git-[a-f\d]{10}$", ver):
        # a master branch build
        ver = "snapshot"
    else:
        raise ValueError(f"Unknown gyan.dev version string found: {ver_line}")

    # check if built with shared libs
    if " --enable-shared " in config_lines:
        build_type += "-shared"

    return ver, provider, build_type


def os_arch() -> ArchType:
    """returns arch keyword of gather_builds of the current system"""

    system = platform.system()
    if system != "Windows":
        raise RuntimeError(f"Unsupported OS: {system}")

    machine = platform.machine()
    arch = {"x86_64": "amd64", "AMD64": "amd64"}.get(machine, None)
    if arch is None:
        raise RuntimeError(f"Unsupported machine: {machine}")

    return arch


def gather_builds(
    arch: ArchType | None = None,
    skip_nightly: bool = False,
    requests_kws: dict | None = None,
) -> tuple[list[Build], list[Build]]:
    """'johnvansickle.com' releases contain the builds of all active branches for all target os_arch and licenses

    :param os_arch: string identifying the os and CPU architecture, defaults to "linux64"
    :param skip_nightly: If True, returned nightly_catalog will be empty, defaults to False
    :param requests_kws: keywords for html requests call, defaults to None
    :return release_catalog: list of release build info objects
    :return nightly_catalog: list of nightly build info objects
    """

    assert arch == "amd64"

    nightly_catalog = []  # latest nightly builds
    release_catalog = []  # latest release branches

    # create an iterator of GitHub releases
    for rel in gh.iter_releases(api_url, requests_kws=requests_kws):
        if rel["name"].startswith("ffmpeg git "):
            if len(nightly_catalog):
                # already populated
                continue

            for asset in rel["assets"]:
                if asset["content_type"] != asset_type:
                    continue

                # ffmpeg-2026-05-06-git-f2e5eff3ff-essentials_build.zip
                m = re_latest_name.fullmatch(asset["name"])
                if m:
                    nightly_catalog.append(
                        Build(
                            provider=provider,
                            build_type=m[1],
                            os="Windows",
                            arch="amd64",
                            version="master",
                            files=(
                                BuildFile(
                                    asset["name"],
                                    asset["browser_download_url"],
                                    asset["size"],
                                ),
                            ),
                            mime_type=asset["content_type"],
                        )
                    )
        elif rel["name"].startswith("ffmpeg "):
            for asset in rel["assets"]:
                if asset["content_type"] != asset_type:
                    continue

                m = re_name.fullmatch(asset["name"])
                if m:
                    build_type = m[2]
                    if m[3]:
                        build_type += "-shared"

                    release_catalog.append(
                        Build(
                            provider=provider,
                            build_type=build_type,
                            os="Windows",
                            arch="amd64",
                            version=Version(m[1]),
                            files=(
                                BuildFile(
                                    asset["name"],
                                    asset["browser_download_url"],
                                    asset["size"],
                                ),
                            ),
                            mime_type=asset["content_type"],
                        )
                    )

    return release_catalog, nightly_catalog
