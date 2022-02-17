from tempfile import TemporaryDirectory
from ._download_helper import download_info, download_file, chmod
import re, ssl, tarfile, os, shutil
from os import path

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE


def get_version():

    return re.search(
        r"version: (\d+\.\d+(?:\.\d+)?)",
        download_info(
            "https://johnvansickle.com/ffmpeg/release-readme.txt",
            "text/plain",
            ctx,
        ),
    )[1]


def download_n_install(install_dir, progress=None, arch=None):
    archs = ("amd64", "i686", "arm64", "armhf", "armel")
    if arch is None:
        arch = archs[0]
    elif arch not in archs:
        raise ValueError(f"Invalid arch specified. Must be one of {arch}")

    with TemporaryDirectory() as tmpdir:
        tarpath = path.join(tmpdir, "ffmpeg_linux.tar.xz")
        url = f"https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-{arch}-static.tar.xz"

        with TemporaryDirectory() as tmpdir:
            download_file(tarpath, url, "application/x-xz", ctx, progress=progress)

        with tarfile.open(tarpath, "r") as f:
            f.extractall(tmpdir)

        _, (src_dir_name, *_), _ = next(os.walk(tmpdir))
        src_dir_path = path.join(tmpdir, src_dir_name)

        with open(path.join(src_dir_path, "VERSION"), "wt") as f:
            f.write(get_version())

        try:
            shutil.rmtree(install_dir)
        except:
            pass

        shutil.move(src_dir_path, install_dir)

    ffmpegpath = path.join(install_dir, "ffmpeg")
    ffprobepath = path.join(install_dir, "ffprobe")
    chmod(ffmpegpath)
    chmod(ffprobepath)

    return ffmpegpath, ffprobepath
