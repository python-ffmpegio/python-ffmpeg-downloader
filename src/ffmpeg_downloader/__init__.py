from __future__ import annotations

__version__ = "0.3.0"

import os
from . import _backend as _


def add_path():
    """Add FFmpeg directory to the process environment path

    .. note::

      The system path is not updated with this command. The FFmpeg path is
      only added during the life of the calling Python process.

      To add to the (per-user) system path, re-install the FFmpeg with `--add-path`
      option in cli:

        ffdl install -U --add-path

    .. note::

      This function does not check if the FFmpeg is installed in the path. Use
      `ffmpeg_downloaer.installed()` to check.

    """
    os.environ["PATH"] = os.pathsep.join([os.environ["PATH"], _.ffmpeg_path()])


def installed(
    bin_name: str = "ffmpeg", *, return_path: bool = False
) -> bool | str | None:
    """True if FFmpeg binary is installed

    :param bin_name: FFmpeg command name, defaults to 'ffmpeg'
    :param return_path: True to return the valid path (or None if not installed),
                        defaults to False
    :return: True if installed
    """

    p = _.ffmpeg_path(bin_name)
    tf = os.path.isfile(p)
    return tf if not return_path else p if tf else None


def __getattr__(name):  # per PEP 562
    try:
        return {
            "ffmpeg_dir": lambda: _.ffmpeg_path(),
            "ffmpeg_path": lambda: installed("ffmpeg", return_path=True),
            "ffprobe_path": lambda: installed("ffprobe", return_path=True),
            "ffplay_path": lambda: installed("ffplay", return_path=True),
            "ffmpeg_version": _.ffmpeg_version,
        }[name]()
    except:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
