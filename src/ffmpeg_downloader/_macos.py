from tempfile import TemporaryDirectory
from os import path
import json, os, zipfile
from ._download_helper import download_info, download_file, chmod


def get_version():
    return json.loads(
        download_info(
            "https://evermeet.cx/ffmpeg/info/ffmpeg/release", "application/json"
        )
    )["version"]


def download_n_install(install_dir, progress=None):

    with TemporaryDirectory() as tmpdir:
        zipffmpegpath = path.join(tmpdir, "ffmpeg_macos.zip")
        download_file(
            zipffmpegpath,
            "https://evermeet.cx/ffmpeg/getrelease/ffmpeg/zip",
            "application/zip",
            progress=progress,
        )
        zipffprobepath = path.join(tmpdir, "ffprobe_macos.zip")
        download_file(
            zipffprobepath,
            "https://evermeet.cx/ffmpeg/getrelease/ffprobe/zip",
            "application/zip",
            progress=progress,
        )

        with zipfile.ZipFile(zipffmpegpath, "r") as f:
            f.extractall(tmpdir)
        with zipfile.ZipFile(zipffprobepath, "r") as f:
            f.extractall(tmpdir)

        dst_ffmpeg = path.join(install_dir, "ffmpeg")
        try:
            os.remove(dst_ffmpeg)
        except:
            pass
        os.rename(path.join(tmpdir, "ffmpeg"), dst_ffmpeg)
        chmod(dst_ffmpeg)

        dst_ffprobe = path.join(install_dir, "ffprobe")
        try:
            os.remove(dst_ffprobe)
        except:
            pass
        os.rename(path.join(tmpdir, "ffprobe"), dst_ffprobe)
        chmod(dst_ffprobe)

        with open(path.join(install_dir, "VERSION"), "wt") as f:
            f.write(get_version())

    return dst_ffmpeg, dst_ffprobe
