import ffmpeg_downloader as ffdl


def test():
    assert ffdl.installed('ffmpeg')
    assert ffdl.installed('ffprobe')
