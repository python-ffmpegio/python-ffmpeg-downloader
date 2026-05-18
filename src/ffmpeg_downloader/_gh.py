import re
import sys
from datetime import datetime
from typing import Iterator, Literal

from packaging.version import Version

from ._download_helper import download_info


def get_release_asset_info(
    browser_download_url: str,
    requests_kws: dict | None = None,
    max_retries: int | None = None,
) -> str:
    return Version(
        download_info(
            browser_download_url,
            {"Accept": "text/plain"},
            requests_kws=requests_kws,
            max_retries=max_retries,
        ).text
    )


def check_rate_limit(
    requests_kws: dict | None = None,
    max_retries: int | None = None,
) -> Literal[0]:

    try:
        r = download_info(
            "https://api.github.com/rate_limit",
            {"Accept": "application/vnd.github+json"},
            requests_kws=dict(requests_kws),
            max_retries=max_retries,
        )
        status = r.json()["resources"]["core"]
        assert status["remaining"] == 0
        return f"You've reached the access rate limit on GitHub. Wait till {datetime.fromtimestamp(status['reset'])} and try again."
    except:
        return 0


def iter_pages(
    url: str,
    per_page: int | None = None,
    max_pages: int | None = None,
    requests_kws: dict | None = None,
    max_retries: int | None = None,
) -> Iterator[list | dict]:

    headers = {"Accept": "application/vnd.github+json"}
    params = {"per_page": per_page or 100}

    page = 1
    if max_pages is None:
        max_pages = sys.maxsize

    while page <= max_pages:
        r = download_info(
            url,
            headers=headers,
            params=params,
            requests_kws=requests_kws,
            max_retries=max_retries,
        )
        if r.status_code != 200:
            raise ConnectionRefusedError(
                check_rate_limit(requests_kws) or "Failed to retrieve data from GitHub"
            )

        for rel in r.json():
            yield rel

        page += 1
        params["page"] = page

        if page == 2:
            if "link" in r.headers:
                link_header = r.headers["link"]
                last_url = re.search(
                    r'(?<=<)([\S]*)(?=>; rel="last")', link_header, re.I
                )[0]
                max_pages = min(
                    max_pages, int(re.search(r"[?&]page=(\d+)", last_url, re.I)[1])
                )
            else:
                max_pages = 1


def iter_releases(
    base_url: str,
    per_page: int | None = None,
    max_pages: int | None = None,
    requests_kws: dict | None = None,
    max_retries: int | None = None,
) -> Iterator[list | dict]:
    for r in iter_pages(
        f"{base_url}/releases",
        per_page,
        max_pages,
        requests_kws,
        max_retries=max_retries,
    ):
        yield r


def iter_tags(
    base_url: str,
    per_page: int | None = None,
    max_pages: int | None = None,
    requests_kws: dict | None = None,
    max_retries: int | None = None,
) -> Iterator[list | dict]:
    for tag in iter_pages(
        f"{base_url}/tags", per_page, max_pages, requests_kws, max_retries=max_retries
    ):
        yield tag


def find_tag(
    tag_or_hash,
    base_url,
    per_page=None,
    max_pages=None,
    requests_kws=None,
    max_retries: int | None = None,
):

    for tag in iter_tags(
        base_url, per_page, max_pages, requests_kws, max_retries=max_retries
    ):
        if tag["name"] == tag_or_hash or tag["commit"]["hash"].startswith(tag_or_hash):
            return tag


def compare_commits(
    commit1,
    commit2,
    base_url,
    requests_kws=None,
    max_retries: int | None = None,
):
    url = f"{base_url}/compare/{commit1}...{commit2}"
    headers = {"Accept": "application/vnd.github+json"}

    r = download_info(
        url, headers=headers, requests_kws=requests_kws, max_retries=max_retries
    )
    if r.status_code != 200:
        raise ConnectionRefusedError(
            check_rate_limit(requests_kws) or "Failed to retrieve data from GitHub"
        )

    return r.json()
