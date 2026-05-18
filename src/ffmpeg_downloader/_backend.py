from __future__ import annotations

import subprocess as sp
import sys
from os import getcwd, makedirs, path
from os import name as os_name
from shutil import copyfile, move, rmtree
from tempfile import TemporaryDirectory, mkdtemp
from typing import Literal

from packaging.version import Version
from platformdirs import user_data_dir
from typing_extensions import LiteralString  # <3.11

from ._config import Build, ConfigBase
from ._download_helper import download_file

list_ = list

if os_name == "nt":
    from . import _win32 as _
elif sys.platform == "darwin":
    from . import _macos as _
else:
    from . import _linux as _

home_url = _.home_url

disclaimer_text = f"""
You are about to download the latest FFmpeg release build from {home_url}. 
Proceeding to download the file is done at your own discretion and risk and 
with agreement that you will be solely responsible for any damage to your 
computer system or loss of data that results from such activities. 

Do you wish to proceed to download? [Yn] """

donation_text = f"""Please remember that to maintain and host the FFmpeg binaries is not free. 
If you appreciate their effort, please consider donating to help them with 
the upkeep of their website via {home_url}.
"""

preset_env_vars = {
    "imageio": {"IMAGEIO_FFMPEG_EXE": "ffmpeg"},
    "moviepy": {"FFMPEG_BINARY": "ffmpeg"},
}


def parse_version(
    version_spec: str | Literal["release", "snapshot"],
) -> tuple[Version | Literal["snapshot"], bool, str | None]:
    """get requested version and optionally build type

    :param version_spec: version string, possibly prefixed with "=" for the
        exact version requested and suffixed with "@<build type>". If "release"
        the latest version string is returned. If "snapshot", it is returned as is.
        Both "release" and "snapshot" may also have "@<build_type>" suffix
    :return version: version object or 'snapshot'
    :return exact: look for the exact version
    :return build_type: optional build type specified
    """
    # 5.1.2 or 5.1.2@essential

    ver, *opts = version_spec.split("@", 1)
    if not ver:
        ver = "release"
    opt = opts[0] if len(opts) else None
    exact = version_spec.startswith("=")
    if exact:
        ver = ver[1:]

    if ver == "snapshot":
        return ver, exact, opt

    config = _.Config()

    if ver == "release":
        ver = config.latest_release_version
    elif ver:
        ver = Version(ver)
    return ver, exact, opt


def setup(
    proxy: str | None = None,
    retries: int | None = None,
    timeout: int | None = None,
    **kwargs,
) -> ConfigBase:

    if proxy is not None:
        kwargs["proxies"] = {"http": proxy, "https": proxy}
    if retries is not None:
        kwargs["max_retries"] = retries
    if timeout is not None:
        kwargs["timeout"] = timeout

    return _.Config(**kwargs)


def list(
    force: bool = False,
    proxy: str | None = None,
    retries: int | None = None,
    timeout: int | None = None,
    **kwargs,
) -> list_[Build]:
    """list all available builds

    :param force: True to retrieve fresh listing from the providers, defaults to False
    :return: chronologically sorted list of Build dataclass objects sorted
    """
    config = setup(proxy, retries, timeout, **kwargs)
    if force:
        config.force_expiration()

    results = sorted(config.releases, key=lambda b: (b.version, b.build_type, b.arch))

    config.dump()

    return results


def search(
    version_spec: Literal["release", "snapshot"] | LiteralString | None = None,
    auto_select: bool = False,
    force: bool = False,
    proxy: str | None = None,
    retries: int | None = None,
    timeout: int | None = None,
    **kwargs,
) -> Build | list_[Build] | None:
    """find ffmpeg available versions that matches the criteria

    :param version_spec: If None, searches the latest version. If literal string,
        it must start with one of the following format:
            - 'release' (default): latest released version (or latest snapshot of the latest branch)
            - 'snapshot': latest master branch snapshot
            - 'x': all releases of major version x
            - 'x.y': all releases of major version x and minor version y
            - 'x.y.z': all release of major version x, minor version y, and micro version z
            - 'x.y.zpostNNN': post release NNN of version x.y.z
        Optionally, the version string can have a suffix `'@<build_type>'` where `<build_type>`
        is the available build type of the specified version.
    :param auto_select: True to return the latest build among matched, defaults
        to False, returning all the matched builds
    :param force: True to retrieve fresh listing from the providers, defaults to False
    :param proxy: _description_, defaults to None
    :param retries: _description_, defaults to None
    :param timeout: _description_, defaults to None
    :return: list of matching FFmpeg build info dataclass objects if `auto_select=False`.
        Else the latest build with the default build type (if not included, the
        first build type available.)
    """
    config = setup(proxy, retries, timeout, **kwargs)

    # look for release versions which satisfies the condition
    v0, exact, option = parse_version(version_spec or "release")

    if isinstance(v0, Version):
        if force:
            config.force_expiration()

        releases = config.releases

        if exact or v0.is_postrelease:  # exact match
            results = [b for b in releases if b.version == v0]
        else:  # starting with the given version string
            n = len(v0.release)
            if n == 1:  # major only
                v1 = Version.from_parts(release=(v0.major + 1,))
            elif n == 2:  # major.minor
                v1 = Version.from_parts(release=(v0.major, v0.minor + 1))
            else:
                assert n == 3  # major.minor.micro
                v1 = Version.from_parts(release=(v0.major, v0.minor, v0.micro + 1))

            results = [b for b in releases if b.version >= v0 and b.version < v1]

    else:  # snapshot
        results = config.latest_snapshot
        # latest info has already been retrieved by parse_version()

    # save if data downloaded
    config.dump()

    if option is not None:
        # specific build type requested
        results = [b for b in results if b.build_type == option]

    if auto_select:
        # if auto_select and len(results):
        #     # keep only the latest version
        #     v = max(results, key=lambda b: b.version).version
        #     results = [b for b in results if b.version == v]
        if len(results):
            if len(results) > 1:
                # select the latest version
                v_latest = max(b.version for b in results)
                results = [b for b in results if b.version == v_latest]

                # select the default build type (if avialable)
                if option is None:
                    default_type = config.default_build_type[results[0].provider]
                    try:
                        return next(b for b in results if b.build_type == default_type)
                    except StopIteration:
                        pass
            # select first build type available
            return results[0]
        else:
            # no match
            return None
    else:
        return results


def get_dir() -> str:
    return user_data_dir("ffmpeg-downloader", "ffmpegio")


def cache_dir() -> str:
    return path.join(get_dir(), "cache")


def bin_dir() -> str:
    return _.get_bindir(get_dir())


def cache_list() -> list_[Build]:
    config = setup()
    return [b for b in config.releases if b.cached]


def cache_purge():
    """delete all files in the cache dir"""

    dir = cache_dir()
    rmtree(dir, True)
    makedirs(dir, exist_ok=True)


def get_cache_paths(info: Build) -> dict[str, str]:
    """Returns the paths of cached download if build is found in the cache dir or None if not found"""

    cdir = cache_dir()
    return {file.name: path.join(cdir, file.name) for file in info.files}


def gather_download_info(rel, asset, no_cache_dir=None):
    # get filename, url, content_type, & size of each install files
    info = _.Config().get_download_info(rel, asset)
    if no_cache_dir:
        return info

    # check if already in cache
    return [
        (*item, path.exists(item[-1]))
        for item in (((*entry, path.join(cache_dir(), entry[0]))) for entry in info)
    ]


def inquire_downloading(info: Build, args):
    config = _.Config()
    config.providers[info.provider]

    download_info
    if args.no_cache_dir or not all(entry[-1] for entry in info):
        if not args.y:
            ans = input(_.disclaimer_text)
            if ans and ans.lower() not in ("y", "yes"):
                print("\ndownload canceled")
                return True
        print(_.donation_text)
    return False


def download(
    info: Build,
    dst: str | None = None,
    progress=None,
    no_cache_dir=False,
    proxy: str | None = None,
    retries: int | None = None,
    timeout: int | None = None,
    **kwargs,
):
    """download specified FFmpeg build

    :param info: build information
    :param dst: destination directory to place the downloaded file, defaults to None
    :param progress: downlaod progress display callback function, defaults to None
    :param no_cache_dir: True to always download, ignore previously downloaded
        file in the cache, defaults to False
    :param proxy: _description_, defaults to None
    :param retries: _description_, defaults to None
    :param timeout: _description_, defaults to None
    :return: _description_
    """

    if dst is None:
        # save to the current working directory
        dst = getcwd()

    # get cache info
    cachedir = cache_dir()
    cache_paths = {} if no_cache_dir else get_cache_paths(info)

    # create cache dir if not already exists
    if not no_cache_dir:
        makedirs(cachedir, exist_ok=True)

    with TemporaryDirectory() as tmpdir:

        def do(filename, url, content_type):
            # download

            dstpath = path.join(dst, filename)
            cache_path = cache_paths.get(filename, "")

            if no_cache_dir or not path.exists(cache_path):
                # run downloader
                zippath = path.join(tmpdir, filename)
                download_file(
                    zippath,
                    url,
                    headers={"Accept": content_type},
                    params={},
                    progress=progress,
                    max_retries=retries,
                    requests_kws=dict(
                        timeout=timeout,
                        proxies=proxy and {"http": proxy, "https": proxy},
                    ),
                )

                # move the downloaded file to the final destination
                move(zippath, dst)

                # if caching is not disabled, copy the file to cache dir
                if not no_cache_dir and dst != cachedir:
                    # cache the zip file for future use
                    copyfile(dstpath, cache_path)

            elif cachedir != dst:
                # if not downloading to the cache dir, copy the file
                copyfile(cache_path, dstpath)

            return dstpath

        return [do(file.name, file.url, info.mime_type) for file in info.files]


def install(*install_files, progress=None):
    dir = path.join(get_dir(), "ffmpeg")
    tmpdir = mkdtemp()
    failed = True
    try:
        # extract files in temp dir
        mvdir = _.extract(install_files, tmpdir, progress)
        # delete existing install
        if path.exists(dir):
            rmtree(dir, ignore_errors=True)
        # move the file to the final destination
        move(path.join(tmpdir, mvdir) if mvdir else tmpdir, dir)
        failed = False
    except Exception as e:
        if failed:
            rmtree(tmpdir, ignore_errors=True)
        raise e


def remove(remove_all=False, ignore_errors=True):
    dir = get_dir()
    if not remove_all:
        dir = path.join(dir, "ffmpeg")
    rmtree(dir, ignore_errors=ignore_errors)


def validate_env_vars(env_vars):
    # inspect
    values = ("path", "ffmpeg", "ffprobe", "ffplay")
    for k, v in env_vars.items():
        if not isinstance(k, str) or v not in values:
            raise ValueError(f"Environmental variable value must be one of {values}")


def presets_to_env_vars(presets, env_vars=None):
    if presets is not None:
        env_vars = {} if env_vars is None else {**env_vars}
        for preset in presets:
            try:
                env_vars.update(preset_env_vars[preset])
            except:
                raise ValueError(f"preset '{preset}' is invalid")
    return env_vars


def get_env_vars():
    config = _.Config()
    return config.install_setup


def set_env_vars(set_path=None, env_vars={}, no_symlinks=False):
    # if binaries are in a subdirectory, update dir
    bindir = _.get_bindir(get_dir())

    if set_path:
        _.set_env_path(bindir)

    if len(env_vars):
        _.set_env_vars(env_vars, bindir)

    symlinks = None
    if not no_symlinks:
        try:
            symlinks = _.set_symlinks(
                {
                    bintype: ffmpeg_path(bintype)
                    for bintype in ("ffmpeg", "ffprobe", "ffplay")
                }
            )
        except NotImplementedError:
            pass

    # store the environmental variable set
    config = _.Config()
    config.install_setup = {
        "set_path": bool(set_path),
        "env_vars": env_vars,
        "symlinks": symlinks,
    }
    config.dump()


def clr_env_vars():
    # get the environmental variable set
    config = _.Config()
    setup = config.install_setup
    if setup is None:
        return

    if "set_path" in setup:
        _.clr_env_path(_.get_bindir(get_dir()))

    if "env_vars" in setup:
        _.clr_env_vars(setup["env_vars"])

    if "symlinks" in setup:
        _.clr_symlinks(setup["symlinks"])

    config.install_setup = None
    config.dump()


def ffmpeg_version() -> (
    tuple[Version | Literal["snapshot"], LiteralString, LiteralString] | None
):
    """detect version, provider, and build type of currently installed ffmpeg

    :return: a tuple of version, provider, and build type or None if no match found
    """

    try:
        ver_str = sp.run(
            [_.get_binpath(get_dir(), "ffmpeg"), "-version"],
            stdout=sp.PIPE,
            stderr=sp.STDOUT,
            universal_newlines=True,
        ).stdout
    except (FileNotFoundError, PermissionError):
        return None

    return _.detect_version(ver_str)


def ffmpeg_path(type=None):
    if type:
        return _.get_binpath(get_dir(), type)
    else:
        return _.get_bindir(get_dir())
