import os
import shutil
from ._download_helper import download_info, download_file
from tempfile import TemporaryDirectory
from os import path
import zipfile

home_url = "https://www.gyan.dev/ffmpeg/builds"


def get_version():
    return download_info(
        f"{home_url}/ffmpeg-release-essentials.zip.ver",
        "text/plain",
    )


def download_n_install(install_dir, progress=None, build_type=None):

    build_types = ("essentials", "full", "full-shared")
    if build_type is None:
        build_type = build_types[0]
    elif build_type not in build_types:
        raise ValueError(f"Invalid build_type specified. Must be one of {build_types}")

    with TemporaryDirectory() as tmpdir:
        zippath = path.join(tmpdir, "ffmpeg_win32.zip")
        url = f"{home_url}/ffmpeg-release-{build_type}.zip"
        download_file(zippath, url, "application/zip", progress=progress)

        with zipfile.ZipFile(zippath, "r") as f:
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


def get_bindir(install_dir):
    return path.join(install_dir, "bin")
