from os import path
from shutil import which
import ffmpeg_downloader as ffdl


def test():
    def test_update():
        ffdl.update(skip_disclaimer=True)
        assert ffdl.has_update() is False
        assert which(ffdl.ffmpeg_path) is not None
        assert which(ffdl.ffprobe_path) is not None
        assert ffdl.ffmpeg_version is not None

    def test_remove():
        ffdl.remove()
        assert ffdl.ffmpeg_path is None
        assert ffdl.ffprobe_path is None
        assert ffdl.ffmpeg_version is None
        assert ffdl.has_update()

    if ffdl.ffmpeg_path is None:
        test_update()
        test_remove()
    else:
        test_remove()
        test_update()
