from os import listdir, path, name as os_name, getcwd, makedirs
from shutil import rmtree, move, copyfile
import sys
from appdirs import user_data_dir
from packaging.version import Version
from tempfile import TemporaryDirectory, mkdtemp
import subprocess as sp

from ._config import Config
from ._download_helper import download_file

if os_name == "nt":
    from . import _win32 as _
elif sys.platform == "darwin":
    from . import _macos as _
else:
    from . import _linux as _

disclaimer_text = f"""
You are about to download the latest FFmpeg release build from {_.home_url}. 
Proceeding to download the file is done at your own discretion and risk and 
with agreement that you will be solely responsible for any damage to your 
computer system or loss of data that results from such activities. 

Do you wish to proceed to download? [Yn] """

donation_text = f"""Please remember that to maintain and host the FFmpeg binaries is not free. 
If you appreciate their effort, please consider donating to help them with 
the upkeep of their website via {_.home_url}.
"""

preset_env_vars = {
    "imageio": {"IMAGEIO_FFMPEG_EXE": "ffmpeg"},
    "moviepy": {"FFMPEG_BINARY": "ffmpeg"},
}


def parse_version(version_spec):
    # 5.1.2 or 5.1.2@essential or 5.1.2@arm

    ver, *opts = version_spec.split("@", 1)
    if ver == "snapshot":
        ver = _.get_latest_snapshot()
    elif ver == "release":
        ver = _.get_latest_version()
    elif ver:
        ver = Version(ver)
    return ver, opts[0] if len(opts) else None


def list(force=None, proxy=None, retries=None, timeout=None):
    config = Config()
    if force or config.is_stale():
        _.update_releases_info(force, proxy, retries, timeout)
    return (
        [(rel, asset) for rel, assets in config.releases.items() for asset in assets]
        if _.are_assets_options()
        else [(rel, None) for rel, _ in config.releases.items()]
    )


def search(
    version_spec, auto_select=None, force=None, proxy=None, retries=None, timeout=None
):

    version, option = parse_version(version_spec or "release")
    config = Config()

    if type(version) == Version:
        if force or config.is_stale():
            _.update_releases_info(force, proxy, retries, timeout)
        releases = config.releases

        # return the releases starting with the given version
        results = (
            [
                (rel, asset)
                for rel, assets in releases.items()
                if not version or str(rel).startswith(str(version))
                for asset in assets
                if not option or option == asset
            ]
            if _.are_assets_options()
            else [
                (rel, None)
                for rel, _ in releases.items()
                if not version or str(rel).startswith(str(version))
            ]
            if option is None
            else []
        )
    else:
        releases = config.snapshot
        # latest info has already been retrieved by parse_version()

        # return the releases starting with the given version
        results = (
            [
                (rel, asset)
                for rel, assets in releases.items()
                for asset in assets
                if not option or option == asset
            ]
            if _.are_assets_options()
            else [
                (rel, None)
                for rel, _ in releases.items()
                if not version or str(rel).startswith(str(version))
            ]
            if option is None
            else []
        )

    if auto_select:
        # selects the default
        return sorted(results, key=_.version_sort_key)[-1] if len(results) else None

    return results


def get_dir():
    return user_data_dir("ffmpeg-downloader", "ffmpegio")


def cache_dir():
    return path.join(get_dir(), "cache")


def bin_dir():
    return _.get_bindir(get_dir())


def cache_list():
    d = cache_dir()
    try:
        return listdir(d)
    except FileNotFoundError:
        return []


def gather_download_info(rel, asset, no_cache_dir=None):
    # get filename, url, content_type, & size of each install files
    info = _.get_download_info(rel, asset)
    if no_cache_dir:
        return info

    # check if already in cache
    return [
        (*item, path.exists(item[-1]))
        for item in (((*entry, path.join(cache_dir(), entry[0]))) for entry in info)
    ]


def download(
    info,
    dst=None,
    progress=None,
    no_cache_dir=None,
    proxy=None,
    retries=None,
    timeout=None,
):
    if dst is None:
        # save to the current working directory
        dst = getcwd()

    with TemporaryDirectory() as tmpdir:

        def do(filename, url, content_type, size, *cache_info):
            dstpath = path.join(dst, filename)

            if not no_cache_dir and cache_info[0] != dstpath and path.exists(dstpath):
                raise FileExistsError(f"'{dstpath}' already exists")

            # check if already in cache
            if no_cache_dir or not cache_info[-1]:
                # run downloader
                zippath = path.join(tmpdir, filename)
                download_file(
                    zippath,
                    url,
                    headers={"Accept": content_type},
                    params={},
                    progress=progress,
                    timeout=timeout,
                    retries=retries,
                    proxy=proxy,
                )

                # cache the zip file for future use
                if not no_cache_dir:
                    makedirs(path.dirname(cache_info[0]), exist_ok=True)
                    copyfile(zippath, cache_info[0])

                # move the downloaded file to the final destination
                if cache_info[0] != dstpath:
                    move(zippath, dst)
            elif cache_info[0] != dstpath:
                # if not downloading to the cache dir, copy the file
                copyfile(cache_info[0], dstpath)

            return dstpath

        return [do(*entry) for entry in info]


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
    config = Config()
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
    config = Config()
    config.install_setup = {
        "set_path": bool(set_path),
        "env_vars": env_vars,
        "symlinks": symlinks,
    }
    config.dump()


def clr_env_vars():
    # get the environmental variable set
    config = Config()
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


def ffmpeg_version():
    basedir = get_dir()
    try:
        return _.parse_version(
            sp.run(
                [_.get_binpath(basedir, "ffmpeg"), "-version"],
                stdout=sp.PIPE,
                stderr=sp.STDOUT,
                universal_newlines=True,
            ).stdout.split("\n", 1)[0],
            basedir,
        )
    except:
        return None


def ffmpeg_path(type=None):
    if type:
        return _.get_binpath(get_dir(), type)
    else:
        return _.get_bindir(get_dir())
