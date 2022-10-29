from tempfile import TemporaryDirectory
from ._download_helper import download_info, download_file, chmod
import re, tarfile, os, shutil
from os import path

home_url = "https://johnvansickle.com/ffmpeg"


def get_version():

    return re.search(
        r"version: (\d+\.\d+(?:\.\d+)?)",
        download_info(f"{home_url}/release-readme.txt", "text/plain", 10),
    )[1]


def download_n_install(install_dir, progress=None, arch=None):
    archs = ("amd64", "i686", "arm64", "armhf", "armel")
    if arch is None:
        arch = archs[0]
    elif arch not in archs:
        raise ValueError(f"Invalid arch specified. Must be one of {arch}")

    with TemporaryDirectory() as tmpdir:
        tarpath = path.join(tmpdir, "ffmpeg_linux.tar.xz")
        url = f"{home_url}/releases/ffmpeg-release-{arch}-static.tar.xz"

        with TemporaryDirectory() as tmpdir:
            download_file(
                tarpath, url, "application/x-xz", progress=progress, timeout=10
            )

        with tarfile.open(tarpath, "r") as f:
            
            import os
            
            def is_within_directory(directory, target):
                
                abs_directory = os.path.abspath(directory)
                abs_target = os.path.abspath(target)
            
                prefix = os.path.commonprefix([abs_directory, abs_target])
                
                return prefix == abs_directory
            
            def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
            
                for member in tar.getmembers():
                    member_path = os.path.join(path, member.name)
                    if not is_within_directory(path, member_path):
                        raise Exception("Attempted Path Traversal in Tar File")
            
                tar.extractall(path, members, numeric_owner=numeric_owner) 
                
            
            safe_extract(f, tmpdir)

        _, (src_dir_name, *_), _ = next(os.walk(tmpdir))
        src_dir_path = path.join(tmpdir, src_dir_name)

        with open(path.join(src_dir_path, "VERSION"), "wt") as f:
            f.write(get_version())

        try:
            shutil.rmtree(install_dir)
        except:
            pass

        # os.makedirs(install_dir, exist_ok=True)
        shutil.move(src_dir_path, install_dir)

    for cmd in ("ffmpeg", "ffprobe"):
        chmod(path.join(install_dir, cmd))


def get_bindir(install_dir):
    return install_dir
