from tempfile import TemporaryDirectory
from os import path
import json, os, zipfile, shutil
from ._download_helper import download_info, download_file, chmod, download_base

home_url = "https://evermeet.cx/ffmpeg"


def get_version():
    return json.loads(
        download_info(f"{home_url}/info/ffmpeg/release", "application/json")
    )["version"]


def download_n_install(install_dir, progress=None):

    ntotal = 0

    def get_nbytes(cmd):
        with download_base(f"{home_url}/getrelease/{cmd}/zip", "application/zip") as (
            _,
            nbytes,
        ):
            return nbytes

    nfiles = [get_nbytes(cmd) for cmd in ("ffmpeg", "ffprobe")]
    ntotal = sum(nfiles)
    n1 = nfiles[0]
    prog = (
        lambda nread, nbytes: progress((nread + n1) if nbytes != n1 else nread, ntotal)
        if progress is not None
        else None
    )

    with TemporaryDirectory() as tmpdir:

        for cmd in ("ffmpeg", "ffprobe"):
            zippath = path.join(tmpdir, f"{cmd}.zip")
            download_file(
                zippath,
                f"{home_url}/getrelease/{cmd}/zip",
                "application/zip",
                progress=prog,
            )

            with zipfile.ZipFile(zippath, "r") as f:
                f.extractall(tmpdir)

            dst_path = path.join(install_dir, cmd)
            try:
                os.remove(dst_path)
            except:
                pass
            os.makedirs(install_dir, exist_ok=True)
            shutil.move(path.join(tmpdir, cmd), dst_path)
            chmod(dst_path)

        with open(path.join(install_dir, "VERSION"), "wt") as f:
            f.write(get_version())


def get_bindir(install_dir):
    return install_dir
