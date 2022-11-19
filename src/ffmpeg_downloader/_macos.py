from os import path
import re, os, zipfile

from shutil import copyfileobj
from packaging.version import Version

from ._download_helper import download_info, chmod
from ._config import Config

home_url = "https://evermeet.cx"


def are_assets_options():
    return False


def get_latest_version(proxy=None, retries=None, timeout=None):

    return Version(
        download_info(
            f"{home_url}/ffmpeg/info/ffmpeg/release",
            {"Accept": "application/json"},
            proxy=proxy,
            retries=retries,
            timeout=timeout,
        ).json()["version"]
    )


def get_latest_snapshot(proxy=None, retries=None, timeout=None):

    json = download_info(
        f"{home_url}/ffmpeg/info/ffmpeg/snapshot",
        {"Accept": "application/json"},
        proxy=proxy,
        retries=retries,
        timeout=timeout,
    ).json()

    ver = json["version"]

    config = Config()
    snapshot = config.snapshot
    if ver not in snapshot:
        get_asset = lambda json: {
            "name": path.basename(json["download"]["zip"]["url"]),
            "url": json["download"]["zip"]["url"],
            "size_str": f"{round(json['download']['zip']['size']//(1024**2))}M",
        }
        assets = {"ffmpeg": get_asset(json)}
        config.snapshot = {ver: assets}

        for app in ("ffprobe", "ffplay"):
            assets[app] = get_asset(
                download_info(
                    f"{home_url}/ffmpeg/info/{app}/snapshot",
                    {"Accept": "application/json"},
                    proxy=proxy,
                    retries=retries,
                    timeout=timeout,
                ).json()
            )

    return ver


def retrieve_release_list(app, proxy=None, retries=None, timeout=None):
    base_url = f"{home_url}/pub/{app}"
    r = download_info(
        base_url,
        {"Accept": "text/html"},
        proxy=proxy,
        retries=retries,
        timeout=timeout,
    )
    return base_url, re.findall(
        rf'\<a href="({app}-(\d+\.\d+(?:\.\d+)?).zip)"\>\1\</a\>.+?(\d+M)', r.text
    )


def update_releases_info(force=None, proxy=None, retries=None, timeout=None):

    config = Config()
    releases = {} if force else config.releases

    base_url, assets = retrieve_release_list(
        "ffmpeg", proxy=proxy, retries=retries, timeout=timeout
    )

    if all(Version(ver) in releases for file, ver, size_str in assets):
        return releases

    # update the release list
    releases = {
        ver: {
            "ffmpeg": {"name": file, "url": f"{base_url}/{file}", "size_str": size_str}
        }
        for file, ver, size_str in assets
    }

    for app in ("ffprobe", "ffplay"):
        base_url, assets = retrieve_release_list(
            app, proxy=proxy, retries=retries, timeout=timeout
        )
        for file, ver, size_str in assets:
            # update the release list
            releases[ver][app] = {
                "name": file,
                "url": f"{base_url}/{file}",
                "size": size_str,
            }

    # convert the version strings to Version object
    releases = {Version(ver): asset for ver, asset in releases.items()}

    # update the releases data in the config
    config.releases = releases
    config.dump()


def version_sort_key(version):
    v, _ = version
    return v


def get_download_info(version, option):
    assets = getattr(Config(), "releases" if type(version) == Version else "snapshot")[
        version
    ]
    return [[v["name"], v["url"], "application/zip", None] for v in assets.values()]


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
                    if getattr(i, "file_size", 0):  # file
                        with f.open(i) as fi, open(
                            path.join(dst, i.filename), "wb"
                        ) as fo:
                            copyfileobj(progress.io_wrapper(fi), fo)
                    else:
                        f.extract(i, dst)
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
    file = ".bash_profile" if os.environ['SHELL'] == "/bin/bash" else ".zsh_profile"
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


def parse_version(ver_line, basedir):
    m = re.match(r"ffmpeg version (.+)-tessus", ver_line)
    if m:
        ver = m[1]
        try:
            ver = Version(ver)
        except:
            m = re.match(r"N-(.{6}-g[a-z0-9]{10})", ver)
            try:
                ver = m[1]
            except:
                print(f'Unknown version "{ver}" found')

        return ver, None
    else:
        return None
