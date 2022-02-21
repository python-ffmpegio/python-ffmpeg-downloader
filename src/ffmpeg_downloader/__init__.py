__version__ = "0.1.1"
__all__ = [
    "ffmpeg_dir",
    "ffmpeg_version",
    "ffmpeg_path",
    "ffprobe_path",
]

from os import listdir, path, rmdir, name as os_name
from shutil import rmtree
import sys
from appdirs import user_data_dir


if os_name == "nt":
    from ._win32 import (
        download_n_install,
        get_version as get_latest_version,
        get_bindir,
        home_url,
    )
elif sys.platform == "darwin":
    from ._macos import (
        download_n_install,
        get_version as get_latest_version,
        get_bindir,
        home_url,
    )
else:
    from ._linux import (
        download_n_install,
        get_version as get_latest_version,
        get_bindir,
        home_url,
    )

disclaimer_text = f"""
You are about to download the latest FFmpeg release build from {home_url}. 
Proceeding to download the file is done at your own discretion and risk and 
with agreement that you will be solely responsible for any damage to your 
computer system or loss of data that results from such activities. 

Do you wish to proceed to download? [yN] """

donation_text = f"""
Start downloading...

Please remember that to maintain and host the FFmpeg binaries is not free. 
If you appreciate their effort, please consider donating to help them with 
the upkeep of their website via {home_url}.
"""


def get_dir():
    return user_data_dir("ffmpeg_downloader", "ffmpegio")


def _ffmpeg_dir():
    return get_bindir(get_dir())


def _ffmpeg_version():
    try:
        with open(path.join(get_dir(), "VERSION"), "rt") as f:
            return f.read()
    except:
        return None


def __getattr__(name):  # per PEP 562
    try:
        return {
            "ffmpeg_dir": _ffmpeg_dir(),
            "ffmpeg_path": lambda: _ffmpeg_version()
            and path.join(_ffmpeg_dir(), "ffmpeg" if os_name != "nt" else "ffmpeg.exe"),
            "ffprobe_path": lambda: _ffmpeg_version()
            and path.join(
                _ffmpeg_dir(), "ffprobe" if os_name != "nt" else "ffprobe.exe"
            ),
            "ffmpeg_version": _ffmpeg_version,
        }[name]()
    except:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


def has_update():
    current = __getattr__("ffmpeg_version")
    latest = get_latest_version()
    return current != latest


def update(skip_disclaimer=False, progress=None, **options):
    if has_update():

        if not skip_disclaimer:
            ans = input(disclaimer_text)
            if ans.lower() not in ("y", "yes"):
                print("\ndownload canceled")
                return
            print(donation_text)
        download_n_install(get_dir(), progress, **options)
        return False
    return True


def remove(ignore_errors=True):
    dir = get_dir()
    rmtree(dir, ignore_errors=ignore_errors)
    dir = path.dirname(dir)
    if not len(listdir(dir)):
        rmdir(dir)
