from __future__ import annotations

import logging
import platform
import re
from itertools import chain
from typing import Literal, get_args

import requests
from packaging.version import Version
from typing_extensions import LiteralString  # <3.11

from .._config import Build, BuildFile
from .._download_helper import download_info

logger = logging.getLogger(__name__)

provider = "johnvansickle.com"
home_url = "https://johnvansickle.com/ffmpeg"

ArchType = Literal["amd64", "arm64", "i686", "armhf", "armel"]
BuildType = Literal["static"]

build_types = [*get_args(BuildType)]
default_build = get_args(BuildType)[0]

arch_map = {
    "amd64": "x86_64",
    "arm64": "arm64",
    "i686": "i686",
    "armhf": "armhf",
    "armel": "armel",
    "64bit": "x86_64",
    "arm64-64bit": "arm64",
    "armhf-32bit": "armhf",
    "armel-32bit": "armel",
}

asset_type = "application/x-xz"


def detect_version(
    ver_str: str,
) -> tuple[Version | Literal["snapshot"], LiteralString, LiteralString] | None:
    """detect version, provider, and build type

    :param ver_str: `ffmpeg -version` output string
    :return: a tuple of version, provider, and build type or None if no match found
    """

    m = re.match(
        r"ffmpeg version ([.\d]+)-static https://johnvansickle.com/ffmpeg/  Copyright",
        ver_str,
    )
    if not m:
        return None

    # standard version string (followed by -<provider signature>)
    ver_str = m[1]
    if m := re.match(r"N-\d+-g[a-z0-9]+", ver_str):
        ver = "snapshot"
    else:
        ver = Version(ver_str)

    return ver, provider, default_build


def os_arch() -> ArchType:
    """returns arch keyword of gather_builds of the current system"""

    system = platform.system()
    if system != "Linux":
        raise RuntimeError(f"Unsupported OS: {system}")

    machine = platform.machine()
    arch = {
        "x86_64": "amd64",
        "AMD64": "amd64",
        "ARM64": "arm64",
        "arm64": "arm64",
        "aarch64": "arm64",
    }.get(machine, None)
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

    try:
        release_catalog = get_latest_release(arch, requests_kws)
        release_catalog.extend(get_old_releases(arch, requests_kws))
    except requests.exceptions.ConnectTimeout:
        logging.debug(
            "failed to retrieve releases from https://johnvansickle.com/ffmpeg"
        )
        release_catalog = []
    nightly_catalog = [] if skip_nightly else get_latest_snapshot(arch, requests_kws)

    return release_catalog, nightly_catalog


def get_latest_release(
    arch: ArchType | None = None, requests_kws: dict | None = None
) -> list[Build]:

    archs = get_args(ArchType) if arch is None else [arch]

    readme = download_info(
        f"{home_url}/release-readme.txt",
        {"Accept": "text/plain"},
        requests_kws=requests_kws,
    ).text

    rel = re.search(r"version: (\d+\.\d+(?:\.\d+)?)", readme)
    if not rel:
        logger.debug("failed to retrieve https://johnvansickle.com/ffmpeg/readme.txt")
        return []

    ver = Version(rel[1])

    return [
        Build(
            provider=provider,
            build_type="static",
            os="Linux",
            arch=arch_map[arch],
            version=ver,
            files=(
                BuildFile(
                    f"ffmpeg-{ver}-{arch}-static.tar.xz",
                    f"{home_url}/releases/ffmpeg-release-{arch}-static.tar.xz",
                ),
            ),
            mime_type=asset_type,
        )
        for arch in archs
    ]


def get_old_releases(
    arch: ArchType | None = None, requests_kws: dict | None = None
) -> list[Build]:
    url_or = f"{home_url}/old-releases"
    r = download_info(url_or, requests_kws=requests_kws)
    archs = get_args(ArchType) if arch is None else [arch]

    archs = chain(
        *((arch, "64bit" if arch == "amd64" else f"{arch}-64bit") for arch in archs)
    )

    regexp = (
        rf'\<a href="(.+?)"\>ffmpeg-([.\d]+?)-({"|".join(archs)})-static.tar.xz\</a\>'
    )
    matches = re.findall(
        regexp,
        r.text,
    )

    return [
        Build(
            provider=provider,
            build_type="static",
            os="Linux",
            arch=arch_map[arch],
            version=Version(ver),
            files=(BuildFile(f"ffmpeg-{ver}-{arch}-static.tar.xz", f"{url_or}/{url}"),),
            mime_type=asset_type,
        )
        for url, ver, arch in matches
    ]


def get_latest_snapshot(
    arch: ArchType | None = None, requests_kws: dict | None = None
) -> list[Build]:

    archs = get_args(ArchType) if arch is None else [arch]
    readme = download_info(
        f"{home_url}/git-readme.txt",
        {"Accept": "text/plain"},
        requests_kws=requests_kws,
    ).text

    amd64_build = re.search(r"build: (.+)", readme)[1]
    build_date = re.match(r"ffmpeg-(git-\d{8})-amd64-static.tar.xz", amd64_build)[1]

    return [
        Build(
            provider=provider,
            build_type="static",
            os="Linux",
            arch=arch_map[arch],
            version="latest",
            files=(
                BuildFile(
                    f"ffmpeg-{build_date}-{arch}-static.tar.xz",
                    f"{home_url}/builds/ffmpeg-git-{arch}-static.tar.xz",
                ),
            ),
            mime_type=asset_type,
        )
        for arch in archs
    ]
