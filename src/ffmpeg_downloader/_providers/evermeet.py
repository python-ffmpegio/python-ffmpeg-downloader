from __future__ import annotations

import platform
import re
from os import path
from typing import Literal, get_args

from packaging.version import Version
from typing_extensions import LiteralString  # <3.11

from .._config import Build, BuildFile
from .._download_helper import download_info

provider = "evermeet.cx"
home_url = "https://evermeet.cx/ffmpeg"
pub_url = "https://deolaha.ca/pub"

ArchType = Literal["amd64"]
BuildType = Literal["tessus"]

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
        r"ffmpeg version ([.\d]+)-tessus https://evermeet.cx/ffmpeg/  Copyright",
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

    versions = get_release_versions(requests_kws)

    release_catalog = [
        Build(
            provider=provider,
            build_type="tessus",
            os="Darwin",
            arch="amd64",
            version=ver,
            files=tuple(
                get_file_info(binary, ver, requests_kws)
                for binary in ("ffmpeg", "ffprobe", "ffplay")
            ),
            mime_type=asset_type,
        )
        for ver in versions
    ]
    nightly_catalog = (
        []
        if skip_nightly
        else [
            Build(
                provider=provider,
                build_type="tessus",
                os="Darwin",
                arch="amd64",
                version="snapshot",
                files=tuple(
                    get_file_info(binary, "snapshot", requests_kws)
                    for binary in ("ffmpeg", "ffprobe", "ffplay")
                ),
                mime_type=asset_type,
            )
        ]
    )

    return release_catalog, nightly_catalog


def get_file_info(
    binary: Literal["ffmpeg", "ffprobe", "ffplay"],
    version=Version | Literal["snapshot"],
    requests_kws: dict | None = None,
) -> BuildFile:

    json = download_info(
        f"{home_url}/info/{binary}/{version}",
        {"Accept": "application/json"},
        requests_kws=requests_kws,
    ).json()

    return (
        BuildFile(
            path.basename(json["download"]["zip"]["url"]),
            json["download"]["zip"]["url"],
            json["download"]["zip"]["size"],
        ),
    )


def get_release_versions(requests_kws: dict | None = None) -> list[Version]:

    r = download_info(
        f"{pub_url}/ffmpeg",
        {"Accept": "text/html"},
        requests_kws=requests_kws,
    )

    return [
        Version(m[2])
        for m in re.finditer(
            r'\<a href="(ffmpeg-([.\d]+?)\.zip)"\>\1\</a\>',
            r.text,
        )
    ]
