from shutil import copyfileobj
from packaging.version import Version
import re, tarfile, os
from os import path
import platform


from ._config import Config
from ._download_helper import download_info, chmod

home_url = "https://johnvansickle.com/ffmpeg"

# last one gets picked
asset_priority = ["amd64", "i686", "arm64", "armhf", "armel"]

# place the matching cpu arch first (need test)
arch = platform.machine()
try:
    # TODO - adjust as feedback for different architecture is provided
    i = asset_priority.index(arch)
    if i:
        asset_priority = [
            asset_priority[i],
            *asset_priority[:i],
            *asset_priority[i + 1 :],
        ]
except:
    pass


def are_assets_options():
    return False


def get_latest_version(proxy=None, retries=None, timeout=None):
    readme = download_info(
        f"{home_url}/release-readme.txt",
        {"Accept": "text/plain"},
        proxy=proxy,
        retries=retries,
        timeout=timeout,
    ).text
    return Version(re.search(r"version: (\d+\.\d+(?:\.\d+)?)", readme)[1])


def get_latest_snapshot(proxy=None, retries=None, timeout=None):

    readme = download_info(
        f"{home_url}/git-readme.txt",
        {"Accept": "text/plain"},
        proxy=proxy,
        retries=retries,
        timeout=timeout,
    ).text

    hash_str = re.search(r"version: (.+)", readme)[1][:10]
    amd64_build = re.search(r"build: (.+)", readme)[1]
    build_date = re.match(r"ffmpeg-(git-\d{8})-amd64-static.tar.xz", amd64_build)[1]

    config = Config()
    snapshot = config.snapshot
    if hash_str not in snapshot:

        config.snapshot = {
            hash_str: {
                arch: {
                    "name": f"ffmpeg-{build_date}-{arch}-static.tar.xz",
                    "url": f"{home_url}/builds/ffmpeg-git-{arch}-static.tar.xz",
                }
                for arch in asset_priority
            }
        }

    return hash_str


def retrieve_old_releases(proxy=None, retries=None, timeout=None):
    url_or = f"{home_url}/old-releases"
    r = download_info(
        url_or,
        # {"Accept": "text/plain"},
        proxy=proxy,
        retries=retries,
        timeout=timeout,
    )
    matches = re.findall(
        rf'\<a href="(.+?)"\>ffmpeg-(.+?)(?:-64bit|-({"|".join(asset_priority)})(?:-64bit)?)-static.tar.xz\</a\>',
        r.text,
    )
    releases = {}
    for url, ver, arch in matches:
        ver = Version(ver)
        rel = releases.get(ver, None)
        if rel is None:
            releases[ver] = {arch or "amd64": {"name": url, "url": f"{url_or}/{url}"}}
        else:
            rel[arch or "amd64"] = {"name": url, "url": f"{url_or}/{url}"}
    return releases


def update_releases_info(force=None, proxy=None, retries=None, timeout=None):

    config = Config()
    releases = {} if force else config.releases

    ver = get_latest_version(proxy, retries, timeout)
    if ver in releases:
        return

    # update the release list
    releases = {
        ver: {
            arch: {
                "name": f"ffmpeg-{ver}-{arch}-static.tar.xz",
                "url": f"{home_url}/releases/ffmpeg-release-{arch}-static.tar.xz",
            }
            for arch in asset_priority
        },
        **retrieve_old_releases(proxy=proxy, retries=retries, timeout=timeout),
    }

    # update the releases data in the config
    config.releases = releases
    config.dump()


def version_sort_key(version):
    v, o = version
    k = v.major * 10000 + v.minor * 1000 + v.micro * 10 if type(v) == Version else 0
    return k


def get_download_info(version, option):
    asset = getattr(Config(), "releases" if type(version) == Version else "snapshot")[
        version
    ][option or asset_priority[0]]
    return [
        [
            asset["name"],
            asset["url"],
            "application/x-xz",
            None,
        ]
    ]


def is_within_directory(directory, target):

    abs_directory = path.abspath(directory)
    abs_target = path.abspath(target)

    prefix = path.commonprefix([abs_directory, abs_target])

    return prefix == abs_directory


def extract(tarpaths, dst, progress=None):

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
                    with open(path.join(dst, member.name), "wb") as fo:
                        copyfileobj(progress.io_wrapper(f.extractfile(member)), fo)
                else:
                    f.extract(member, dst)

    # grab the extracted folder name
    dstsub = os.listdir(dst)[0]

    # make sure binaries are executable
    for name in ("ffmpeg", "ffprobe"):
        chmod(path.join(dst, dstsub, name))

    return dstsub


def set_symlinks(binpaths):

    user_home = path.expanduser("~")
    user_bindirs = [path.join(user_home, ".local", "bin"), path.join(user_home, "bin")]
    d = next(
        (d for d in user_bindirs if path.isdir(d)),
        None,
    )
    if d is None:
        d = user_bindirs[0]
        os.makedirs(d, exist_ok=True)
        print(
            "!!!Created ~/.local/bin. Must log out and back in for the setting to take effect (or update .profile or .bashrc).!!!"
        )

    symlinks = {name: path.join(d, name) for name in binpaths}
    for name, binpath in binpaths.items():
        if path.isfile(binpath):  # ffplay is not included
            try:
                os.symlink(binpath, symlinks[name])
            except FileExistsError:
                # already symlinked (or file placed by somebody else)
                pass
    return symlinks


def clr_symlinks(symlinks):
    for link in symlinks:
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


def get_bindir(install_dir):
    return path.join(install_dir, "ffmpeg")


def get_binpath(install_dir, app):
    return path.join(install_dir, "ffmpeg", app)


def parse_version(ver_line, basedir):
    m = re.match(r"ffmpeg version N-.{5}-g([a-z0-9]{10})", ver_line)
    if m:
        return (m[1], None)
    else:
        m = re.match(r"ffmpeg version (.+?)-", ver_line)
        ver = m[1]
        try:
            ver = Version(ver)
        except:
            pass
        return (ver, None)
    return None
