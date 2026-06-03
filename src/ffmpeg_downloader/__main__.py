from __future__ import annotations

import argparse
import os
from collections import defaultdict
from shutil import rmtree
from tempfile import mkdtemp
from typing import Literal

from packaging.version import Version
from tabulate import tabulate
from typing_extensions import LiteralString  # <3.11

from . import _backend as ffdl
from ._progress import DownloadProgress, InstallProgress


def _print_version_table(releases: list[ffdl.Build]):
    if len(releases):
        versions = defaultdict(list)

        for build in releases:
            versions[(str(build.version), build.provider)].append(
                f"{build.build_type}*" if build.cached else build.build_type
            )

        print(
            tabulate(
                [
                    (ver, ", ".join(builds), provider)
                    for (ver, provider), builds in versions.items()
                ],
                headers=[
                    "Version",
                    "Available Builds (*=cached)",
                    "Provider",
                ],
            )
        )
        print("\nTo install specific build, ffdl install <version>@<build_type>")
    else:
        print("No matching version found.")


def list_vers(args):
    releases = ffdl.list(args.force, args.proxy, args.retries, args.timeout)
    _print_version_table(releases)


def search(args):
    releases = ffdl.search(
        args.version, False, args.force, args.proxy, args.retries, args.timeout
    )
    _print_version_table(releases)


def cache_dir(args):
    print(ffdl.cache_dir())


def cache_list(args):
    files = ffdl.cache_list()
    if len(files):
        _print_version_table(files)
    else:
        print("no file in cache")


def cache_remove(args):
    raise NotImplementedError


def cache_purge(args):
    if not args.y:
        ans = input("Delete all previously downloaded ffmpeg files in the cache?")
        if ans and ans.lower() not in ("y", "yes"):
            print("\ncache purge canceled")
            return True

    ffdl.cache_purge()


def download(args):
    # select the version/asset
    build = ffdl.search(
        args.version, True, args.force, args.proxy, args.retries, args.timeout
    )
    if build is None:
        raise RuntimeError(
            f"Version {args.version} of FFmpeg is either invalid or not available prebuilt."
            if args.version
            else "No matching version of FFmpeg is found."
        )

    # if inquire_downloading(build, args):
    #     return  # canceled

    dstpaths = ffdl.download(
        build,
        dst=args.dst,
        no_cache_dir=args.no_cache_dir,
        proxy=args.proxy,
        retries=args.retries,
        timeout=args.timeout,
        progress=DownloadProgress,
    )
    if dstpaths is None:
        # exit if user canceled
        return

    print(f"Downloaded and saved {args.version}:")
    for dstpath in dstpaths:
        print(f"  {dstpath}")


def compose_version_spec(
    version: Version | Literal["snapshot"], option: LiteralString | None = None
):
    return f"{version}@{option}" if option else str(version)


def inquire_downloading(download_info: ffdl.Build, args):

    download_info
    if args.no_cache_dir or not all(entry[-1] for entry in download_info):
        if not args.y:
            ans = input(ffdl.disclaimer_text)
            if ans and ans.lower() not in ("y", "yes"):
                print("\ndownload canceled")
                return True
        print(ffdl.donation_text)
    return False


def install(args):
    # validate environmental variable related arguments
    env_vars = {}
    if args.set_env is not None:
        for env_spec in args.set_env:
            name, *var_type = env_spec.split("=", 1)
            if not len(var_type):
                env_vars[name] = "path"
            elif var_type[0] not in ("ffmpeg", "ffprobe", "ffplay"):
                raise ValueError(f"{env_vars} is not a valid set-env value.")
            else:
                env_vars[name] = var_type[0]

    if args.presets is not None:
        env_vars = ffdl.presets_to_env_vars(args.presets, env_vars)

    # find existing version
    ver_info = ffdl.ffmpeg_version()
    if ver_info is None:
        current_version, current_build_type = None, None
        cur_ver_spec = None
    else:
        current_version, _, current_build_type = ver_info
        cur_ver_spec = compose_version_spec(current_version, current_build_type)

    def print_no_need():
        print(
            f"Requirement already satisfied: ffmpeg=={cur_ver_spec} in {ffdl.bin_dir()}"
        )

    if args.version is None and cur_ver_spec is not None and not args.upgrade:
        # neither version or upgrade specified
        print_no_need()
        return

    # select the version/asset
    print(f"Collecting ffmpeg {args.version or ''}")
    build = ffdl.search(
        args.version, True, args.force, args.proxy, args.retries, args.timeout
    )
    version = build and build.version
    if version is None:
        raise RuntimeError(
            f"Version {args.version} of FFmpeg is either invalid or not available prebuilt."
        )
    else:
        ver_spec = compose_version_spec(version, build.build_type)

    if (
        args.version is not None
        and current_version == version
        and build.build_type == current_build_type
    ):
        # version specified and installed version matches the requested
        print_no_need()
        return

    no_cache_dir = args.no_cache_dir

    # filename, url, content_type, size, cache_file, cache_exists
    cached = not no_cache_dir and build.cached
    for entry in build.files:
        sz = entry.size
        if sz is None:
            sz = ""
        else:
            sz = f"({round(sz / 1048576)} MB)"
        action = "Using cached" if cached else "Downloading"
        print(f"  {action} {entry.url} {sz}")

    # show disclaimer if not omitted
    # if inquire_downloading(download_info, args):
    # canceled by user
    # return

    cache_dir = mkdtemp() if no_cache_dir else ffdl.cache_dir()
    try:
        # download the install file(s)
        dstpaths = ffdl.download(
            build,
            dst=cache_dir,
            no_cache_dir=no_cache_dir,
            proxy=args.proxy,
            retries=args.retries,
            timeout=args.timeout,
            progress=DownloadProgress,
        )
        if dstpaths is None:
            # exit if user canceled
            return

        if current_version is not None:
            curr_ver_spec = compose_version_spec(current_version, current_build_type)
            print("Attempting uninstall existing ffmpeg binaries")
            print(f"  Found existing FFmpeg installation: {curr_ver_spec}")
            print(f"  Uninstalling {curr_ver_spec}:")
            ffdl.remove()
            print(f"    Successfully uninstalled  {curr_ver_spec}")

        print(f"Installing collected FFmpeg binaries: {ver_spec}")

        ffdl.install(*dstpaths, progress=InstallProgress)

    finally:
        if args.no_cache_dir:
            rmtree(cache_dir, ignore_errors=True)

    # clear existing env vars if requested
    if args.reset_env:
        print("Clearing previously set environmental variables")
        ffdl.clr_env_vars()

    # set symlinks or env vars
    ffdl.set_env_vars(args.add_path, env_vars, args.no_simlinks)

    print(
        f"Successfully installed FFmpeg binaries: {ver_spec} in\n    {ffdl.ffmpeg_path('ffmpeg')}"
    )


def uninstall(args):
    # find existing version
    ver_info = ffdl.ffmpeg_version()
    if ver_info is None:
        print("\nNo FFmpeg build has been downloaded.")
        return

    current_version, _, current_build_type = ver_info
    cur_ver_spec = compose_version_spec(current_version, current_build_type)

    print(f"Found existing FFmpeg installation: {cur_ver_spec}")
    print("  Would remove:")
    print(f"    {os.path.join(ffdl.get_dir(), 'ffmpeg', '*')}")

    if not args.y and input("Proceed (Y/n)?: ").lower() not in ("y", "yes", ""):
        # aborted by user
        return

    # if env_vars were set, clear them
    ffdl.clr_env_vars()

    # remove the ffmpeg directory
    ffdl.remove(ignore_errors=False)

    print(f"  Successfully uninstalled FFmpeg: {cur_ver_spec}")


def show(args):
    pass


def main(prog: str = ""):
    # create the top-level parser
    parser = argparse.ArgumentParser(
        prog=prog, description="Download and manage FFmpeg prebuilds"
    )

    parser.add_argument(
        "--proxy",
        type=str,
        nargs=1,
        help="Specify a proxy in the form scheme://[user:passwd@]proxy.server:port",
    )
    parser.add_argument(
        "--retries",
        type=int,
        nargs=1,
        help="Maximum number of retries each connection should attempt (default 5 times).",
        default=5,
    )
    parser.add_argument(
        "--timeout",
        type=float,
        nargs=1,
        help="Set the socket timeout (default 15 seconds).",
        default=15,
    )
    parser.add_argument(
        "--no-cache-dir",
        action="store_true",
        help="Disable the cache.",
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Force updating the version list.",
    )

    subparsers = parser.add_subparsers()

    parser_install = subparsers.add_parser("install", help="Install FFmpeg")
    parser_install.add_argument(
        "--upgrade",
        "-U",
        action="store_true",
        help="Upgrade existing FFmpeg to the newest available version.",
    )
    parser_install.add_argument(
        "-y", action="store_true", help="Don't ask for confirmation of installation."
    )
    parser_install.add_argument(
        "--add-path",
        help="(Windows Only) Add FFmpeg path to user PATH variable.",
        action="store_true",
    )
    parser_install.add_argument(
        "--no-simlinks",
        help="(Linux/macOS) Skip creating symlinks in $HOME/.local/bin (or $HOME/bin).",
        action="store_true",
    )
    # ~/Library/bin # macos
    parser_install.add_argument(
        "--set-env",
        help="(Windows Only) Set user environmental variables. If name only, FFmpeg path is assigned to it. To set binary file name, use name=ffmpeg, name=ffprobe, or name=ffplay",
        nargs="*",
    )
    parser_install.add_argument(
        "--reset-env",
        action="store_true",
        help="(Windows Only) Clear previously set user environmental variables.",
    )
    parser_install.add_argument(
        "--presets",
        help="(Windows Only) Specify target python packages to set user environmental variable for packages.",
        choices=list(ffdl.preset_env_vars),
        nargs="*",
    )
    parser_install.add_argument(
        "version",
        nargs="?",
        help="FFmpeg version to install. If not specified the latest version will be installed.",
        # specify version and build options (version string or 'snapshot') (optional argument), 5.1.2 or 5.1.2@essential or 5.1.2@arm or snapshot
    )
    parser_install.set_defaults(func=install)

    parser_list = subparsers.add_parser("list", help="List FFmpeg build versions.")
    parser_list.set_defaults(func=list_vers)

    parser_search = subparsers.add_parser(
        "search", help="Search matching FFmpeg build versions."
    )
    parser_search.add_argument(
        "version",
        help="FFmpeg release version to search.",
        # specify version and build options (version string or 'snapshot') (optional argument), 5.1.2 or 5.1.2@essential or 5.1.2@arm or snapshot
    )
    parser_search.set_defaults(func=search)

    parser_download = subparsers.add_parser("download", help="Download FFmpeg")
    # specify version and build options (version string or 'snapshot') (optional argument), 5.1.2 or 5.1.2@essential or 5.1.2@arm or snapshot
    parser_download.add_argument(
        "-d", "--dst", help="Download FFmpeg zip/tar file into <DIR>"
    )
    parser_download.add_argument(
        "-y", action="store_true", help="Don't ask for confirmation to download."
    )
    parser_download.add_argument(
        "version",
        nargs="?",
        help="FFmpeg version (@option) to download.",
        # specify version and build options (version string or 'snapshot') (optional argument), 5.1.2 or 5.1.2@essential or 5.1.2@arm or snapshot
    )
    parser_download.set_defaults(func=download)

    parser_uninstall = subparsers.add_parser("uninstall", help="Uninstall FFmpeg.")
    parser_uninstall.add_argument(
        "-y",
        action="store_true",
        help="Don't ask for confirmation of uninstall deletions.",
    )
    parser_uninstall.set_defaults(func=uninstall)

    parser_cache = subparsers.add_parser("cache", help="Inspect cached FFmpeg builds.")
    cache_subparsers = parser_cache.add_subparsers()
    parser_cache_dir = cache_subparsers.add_parser(
        "dir", help="Show the cache directory."
    )
    parser_cache_dir.set_defaults(func=cache_dir)
    parser_cache_list = cache_subparsers.add_parser(
        "list", help="List filenames of FFmpeg versions stored in the cache."
    )
    parser_cache_list.set_defaults(func=cache_list)
    parser_cache_remove = cache_subparsers.add_parser(
        "remove", help="Remove one or more package from the cache."
    )
    parser_cache_remove.add_argument(
        "versions",
        nargs="+",
        help="FFmpeg version (@option) to remove.",
    )
    parser_cache_remove.set_defaults(func=cache_remove)
    parser_cache_purge = cache_subparsers.add_parser(
        "purge", help="Remove all items from the cache."
    )
    parser_cache_purge.add_argument(
        "-y", action="store_true", help="Don't ask for confirmation of cache purging."
    )
    parser_cache_purge.set_defaults(func=cache_purge)

    args = parser.parse_args()

    if "func" in args:
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main("python -m ffmpeg_downloader")
