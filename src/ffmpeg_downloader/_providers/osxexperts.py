from __future__ import annotations

import platform
import re
from collections import defaultdict
from os import path
from typing import Literal, get_args

from packaging.version import Version
from typing_extensions import LiteralString  # <3.11

from .._config import Build, BuildFile
from .._download_helper import download_info

provider = "osxexperts.net"
home_url = "https://osxexperts.net"

ArchType = Literal["amd64", "arm64"]
BuildType = Literal["static"]

build_types = [*get_args(BuildType)]
default_build = get_args(BuildType)[0]

asset_type = "application/zip"


def detect_version(
    ver_str: str,
) -> tuple[Version | Literal["snapshot"], LiteralString, LiteralString] | None:
    """detect version, provider, and build type

    :param ver_str: `ffmpeg -version` output string
    :return: a tuple of version, provider, and build type or None if no match found
    """

    # standard version string (followed by -<provider signature>)
    m = re.match(
        r"ffmpeg version ([.\d]+) Copyright",
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
    if system != "Darwin":
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
    """'evermeet.cx' releases contain the builds of all active branches for all target os_arch and licenses

    :param os_arch: string identifying the os and CPU architecture, defaults to "linux64"
    :param skip_nightly: If True, returned nightly_catalog will be empty, defaults to False
    :param requests_kws: keywords for html requests call, defaults to None
    :return release_catalog: list of release build info objects
    :return nightly_catalog: list of nightly build info objects
    """

    return get_releases(arch, requests_kws), []


def get_releases(
    arch: ArchType | None, requests_kws: dict | None = None
) -> list[Version]:

    r = download_info(
        f"{home_url}",
        {"Accept": "text/html"},
        requests_kws=requests_kws,
    )

    def to_version(ver_str: str) -> Version:
        return Version.from_parts(release=tuple(int(s) for s in ver_str))

    files = defaultdict(list)
    for m in re.finditer(
        r'\<a href="(https://www.osxexperts.net/(ffmpeg|ffprobe|ffplay)(\d+)(intel|arm)\.zip)"',
        r.text,
    ):
        a = {"intel": "amd64", "arm": "arm64"}[m[4]]
        if arch is not None and arch != a:
            continue

        files[(to_version(m[3]), a)].append(m[1])

    return [
        Build(
            provider=provider,
            build_type="static",
            os="Darwin",
            arch=a,
            version=v,
            files=tuple(BuildFile(path.basename(url), url) for url in urls),
            mime_type=asset_type,
        )
        for (v, a), urls in files.items()
    ]


# <a href="https://www.osxexperts.net/ffmpeg81arm.zip"
