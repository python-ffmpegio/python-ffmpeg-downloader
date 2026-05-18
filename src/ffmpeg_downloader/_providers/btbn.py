from __future__ import annotations

import platform
import re
from typing import Literal, get_args

from packaging.version import Version
from typing_extensions import LiteralString  # <3.11

from .. import _gh as gh
from .. import _gh_ffmpeg as ffmpeg
from .._config import Build, BuildFile

provider = "btbn"

BuildType = Literal["gpl", "lgpl", "gpl-shared", "lgpl-shared"]  # = "gpl"

build_types = [*get_args(BuildType)]
default_build = get_args(BuildType)[0]

OSArchType = Literal["linux64", "linuxarm64", "win64", "winarm64"]
os_arch_map = {
    "linux64": ("Linux", "x86_64"),
    "linuxarm64": ("Linux", "arm64"),
    "win64": ("Windows", "AMD64"),
    "winarm64": ("Windows", "ARM64"),
}

releases_url = "https://api.github.com/repos/BtbN/FFmpeg-Builds/releases"

asset_types = ["application/x-xz", "application/zip"]


base_url = "https://api.github.com/repos/BtbN/FFmpeg-Builds"


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
        r"ffmpeg version (.+?)-g[0-9a-f]{10}-[2-9]\d{3}[01][\d][0-3][\d] Copyright",
        ver_line,
    )
    if m is None:
        return None

    # resolve the version
    ver = m[1]
    if ver.startswith("N-"):
        # a master branch build
        ver = "snapshot"
    elif m := re.match(r"n([.\d]+)-(\d+)$", ver):
        # a release branch build, use post## protocol to specify the n-th commit of the branch
        ver = Version.from_parts(
            release=tuple(int(v) for v in m[1].split(".")), post=int(m[2])
        )
    else:
        raise ValueError(f"Unknown BtbN version string found: {ver_line}")

    enable_gpl = " --enable-gpl " in config_lines
    enable_shared = " --enable-shared " in config_lines

    return (
        ver,
        provider,
        {
            (False, False): "lgpl",
            (False, True): "lgpl-shared",
            (True, False): "gpl",
            (True, True): "gpl-shared",
        }[(enable_gpl, enable_shared)],
    )


def os_arch() -> OSArchType:
    """return os_arch keyword

    :return: _description_
    """

    system = platform.system()
    os = {"Linux": "linux", "Windows": "win"}.get(system, None)
    if os is None:
        raise RuntimeError(f"Unsupported OS: {system}")

    machine = platform.machine()
    arch = {
        "x86_64": "64",
        "AMD64": "64",
        "ARM64": "arm64",
        "arm64": "arm64",
        "aarch64": "arm64",
    }.get(machine, None)
    if arch is None:
        raise RuntimeError(f"Unsupported machine: {machine}")

    return os + arch


def gather_builds(
    os_arch: OSArchType | None = None,
    skip_nightly: bool = False,
    requests_kws: dict | None = None,
) -> tuple[list[Build], list[Build]]:
    """BtbN/FFmpeg-Builds' releases contain the builds of all active branches for all target os_arch and licenses

    :param os_arch: string identifying the os and CPU architecture, defaults to "linux64"'
    :param skip_nightly: If True, returned nightly_catalog will be empty, defaults to False
    :param requests_kws: keywords for html requests call, defaults to None
    :return release_catalog: list of release build info objects
    :return nightly_catalog: list of nightly build info objects
    """

    fixed_os_arch = os_arch is not None
    if fixed_os_arch:
        os, arch = os_arch_map[os_arch]

    re_latest_name = re.compile(
        rf"ffmpeg-(.+?)-latest-{os_arch or '(.+?)'}-(.+?).(?:tar.xz|zip)"
    )
    re_name = re.compile(
        rf"ffmpeg-(n.+?)-(\d+?)-g.+?-{os_arch or '(.+?)'}-(.+?)-\d+\.\d+\.(?:tar.xz|zip)"
    )

    nightly_catalog = []  # latest nightly builds
    release_catalog = []  # latest release branches
    found_ver = {}
    found_releases = set()

    # create an iterator of GitHub releases (latest first)
    it = gh.iter_releases(base_url, requests_kws=requests_kws)

    # latest release first (always the latest release)
    rel = next(it)

    if not skip_nightly:
        for asset in rel["assets"]:
            if asset["content_type"] not in asset_types:
                continue

            m = re_latest_name.fullmatch(asset["name"])
            if m:
                if fixed_os_arch:
                    branch, build_type = m[1], m[2]
                else:
                    branch, os_arch, build_type = m[1], m[3], m[4]
                    os, arch = os_arch_map[os_arch]

                nightly_catalog.append(
                    Build(
                        provider=provider,
                        build_type=build_type,
                        os=os,
                        arch=arch,
                        version=branch,
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

    # only grab the latest release of each branch
    for rel in it:
        for asset in rel["assets"]:
            if asset["content_type"] not in asset_types:
                continue

            m = re_name.fullmatch(asset["name"])
            if (
                m
                and (ver := ffmpeg.parse_version(m[1]))
                and (ver not in found_ver or found_ver[ver] == m[2])
            ):
                found_ver[ver] = m[2]
                if m[2] != "0":
                    ver = Version.from_parts(release=ver.release, post=int(m[2]))

                if fixed_os_arch:
                    branch, build_type = m[1], m[3]
                else:
                    branch, build_type, os_arch = m[1], m[2], m[3]
                    os, arch = os_arch_map[os_arch]

                if (ver, build_type) not in found_releases:
                    found_releases.add((ver, build_type))
                    release_catalog.append(
                        Build(
                            provider=provider,
                            build_type=build_type,
                            os=os,
                            arch=arch,
                            version=ver,
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
