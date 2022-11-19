import itertools
from shutil import copyfileobj
from os import path
import subprocess as sp
import zipfile
from datetime import datetime
from packaging.version import Version
import re
from glob import glob

import winreg
import os


from ._config import Config
from ._download_helper import download_info

home_url = "https://www.gyan.dev/ffmpeg/builds"

asset_type = (
    "application/x-zip-compressed"  # 'content_type': 'application/octet-stream' for .7z
)

asset_names = {
    "essentials_build": "essentials",
    "full_build": "full",
    "shared": "full-shared",
}

# last one gets picked
asset_priority = ["full-shared", "full", "essentials"]

def are_assets_options():
    return True

def get_latest_version(proxy=None, retries=None, timeout=None):
    return Version(
        download_info(
            f"{home_url}/ffmpeg-release-essentials.7z.ver",
            {"Accept": "text/plain"},
            proxy=proxy,
            retries=retries,
            timeout=timeout,
        ).text
    )


def get_latest_snapshot(proxy=None, retries=None, timeout=None):
    ver = download_info(
        f"{home_url}/ffmpeg-git-essentials.7z.ver",
        {"Accept": "text/plain"},
        proxy=proxy,
        retries=retries,
        timeout=timeout,
    ).text

    config = Config()
    snapshot = config.snapshot
    if ver not in snapshot:
        assets, eol = retrieve_releases_page(1, ver, 10, proxy, retries, timeout)
        if eol:
            raise ValueError(f"Assets for snapshot {ver} could not be located.")
        config = Config()
        config.snapshot = {ver: assets}

    return ver


def check_rate_limit(proxy=None, retries=None, timeout=None):
    try:
        r = download_info(
            "https://api.github.com/rate_limit",
            {"Accept": "application/vnd.github+json"},
            proxy=proxy,
            retries=retries,
            timeout=timeout,
        )
        status = r.json()["resources"]["core"]
        assert status["remaining"] == 0
        return f"You've reached the access rate limit on GitHub. Wait till {datetime.fromtimestamp(status['reset'])} and try again."
    except:
        return 0


def retrieve_releases_page(
    page, snapshot=None, per_page=100, proxy=None, retries=None, timeout=None
):

    headers = {"Accept": "application/vnd.github+json"}
    url = "https://api.github.com/repos/GyanD/codexffmpeg/releases"

    r = download_info(
        url,
        headers=headers,
        params={"page": page, "per_page": per_page},
        proxy=proxy,
        retries=retries,
        timeout=timeout,
    )

    if r.status_code != 200:
        raise ConnectionRefusedError(
            check_rate_limit(proxy=proxy, retries=retries, timeout=timeout)
            or "Failed to retrieve data from GitHub"
        )

    info = r.json()

    extract_assets = lambda itm: {
        asset_names.get(
            elm["name"].rsplit(".", 1)[0].rsplit("-", 1)[-1], elm["name"]
        ): {k: elm[k] for k in ("name", "browser_download_url", "content_type", "size")}
        for elm in itm
        if elm["content_type"] == asset_type
    }

    if snapshot:
        return next(
            (
                extract_assets(rel["assets"])
                for rel in info
                if rel["tag_name"] == snapshot
            ),
            None,
        ), not len(info)
    else:
        
        return {
            tag: url
            for tag, url in (
                (Version(rel["tag_name"]), extract_assets(rel["assets"]))
                for rel in info if re.match(r'\d+\.\d+(?:\.\d+)?$', rel['tag_name'])
            )
            if tag
        }, not len(info)


def update_releases_info(force=None, proxy=None, retries=None, timeout=None):

    config = Config()
    releases = {} if force else config.releases
    changed = False

    # update the release list
    for page in itertools.count(1):
        # process the release data found on the page
        reldata, eol = retrieve_releases_page(
            page, proxy=proxy, retries=retries, timeout=timeout
        )

        # check if any info is already in the config
        found = next((rel in releases for rel in reldata), False)

        # update the release data in the config
        if len(reldata):
            releases.update(reldata)
            changed = True

        # if any is already in or no more data, exit the loop
        if found or eol:
            break

    # update the releases data in the config
    if changed:
        config.releases = releases
        config.dump()


def version_sort_key(version):
    v, o = version
    k = v.major * 10000 + v.minor * 1000 + v.micro * 10 if type(v) == Version else 0
    return k + asset_priority.index(o)


def get_download_info(version, option):
    asset = getattr(Config(), "releases" if type(version) == Version else "snapshot")[
        version
    ][option]
    return [
        [
            asset["name"],
            asset["browser_download_url"],
            asset["content_type"],
            int(asset["size"]),
        ]
    ]


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
                f'setx {k} {bindir if v == "path" else get_binpath(bindir, v)}',
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


def parse_version(ver_line, basedir):
    m = re.match(r"ffmpeg version (.+)-www\.gyan\.dev", ver_line)
    if m:
        ver, opt = m[1].rsplit("-", 1)
        try:
            ver = Version(ver)
        except:
            pass

        if opt == "full_build" and len(
            glob(path.join(basedir, "ffmpeg", "bin", "av*.dll"))
        ):
            opt = "shared"

        return ver, asset_names[opt]
    else:
        return None
