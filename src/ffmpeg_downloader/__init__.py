__version__ = "0.2.0"

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
    os.environ['PATH'] = os.pathsep.join([os.environ["PATH"],_.ffmpeg_path()])

def installed(bin_name='ffmpeg'):
    """True if FFmpeg binary is installed

    :param bin_name: FFmpeg command name, defaults to 'ffmpeg'
    :type bin_name: 'ffmpeg', 'ffprobe', or 'ffplay', optional
    :return: True if installed
    :rtype: bool
    """    

    return os.path.isfile(_.ffmpeg_path(bin_name))


def __getattr__(name):  # per PEP 562
    try:
        return {
            "ffmpeg_dir": lambda: _.ffmpeg_path(),
            "ffmpeg_path": lambda: _.ffmpeg_path("ffmpeg"),
            "ffprobe_path": lambda: _.ffmpeg_path("ffprobe"),
            "ffplay_path": lambda: _.ffmpeg_path("ffplay"),
            "ffmpeg_version": _.ffmpeg_version,
        }[name]()
    except:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
