import json
import re
from functools import cache

from packaging.version import Version

import ffmpeg_downloader._gh as gh

ffmpeg_url = "https://api.github.com/repos/ffmpeg/ffmpeg"
debug = True


@cache
def get_tags(
    per_page: int | None = None,
    max_pages: int | None = None,
    hash_length: int | None = None,
) -> dict[str, str]:

    from os import path

    json_path = "sandbox/ffmpeg_tags.json"
    if path.exists(json_path):
        with open("sandbox/ffmpeg_tags.json", "rt") as f:
            tags = json.load(f)
    else:
        tags = {
            t["name"]: t["commit"]["sha"]
            for t in gh.iter_tags(ffmpeg_url, per_page, max_pages)
        }

        with open(json_path, "wt") as f:
            json.dump(tags, f)

    if hash_length is not None:
        tags = {k: v[:hash_length] for k, v in tags.items()}

    return tags


def parse_version(tag: str) -> Version | None:
    m = re.fullmatch(r"(?:n|v|ffmpeg-)(\d+\.\d+(?:\.\d+)?)", tag)
    return m and Version(m[1])


def get_releases(hash_length: int | None = None) -> dict[Version, str]:
    releases = {
        ver: v
        for k, v in get_tags(hash_length=hash_length).items()
        if (ver := parse_version(k)) is not None
    }

    return releases


@cache
def compare_commits(commit1, commit2):
    return gh.compare_commits(commit1, commit2, ffmpeg_url)
