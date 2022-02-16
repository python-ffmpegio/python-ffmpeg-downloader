from os import path
from urllib import request
import re
from os import path
from contextlib import contextmanager
import ssl
import json

# download binary
# download version info

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

@contextmanager
def download_base(url, content_type, ctx=None):
    with request.urlopen(url, timeout=1.0, context=ctx) as response:
        # pprint(response.headers.get_content_type())
        if response.headers.get_content_type() != content_type:
            raise RuntimeError(f'"{url}" is not the expected content type.')
        try:
            nbytes = int(response.getheader("content-length"))
        except:
            nbytes = 0
        yield response, nbytes


def download_info(url, content_type, ctx=None):
    with download_base(url, content_type, ctx) as (response, nbytes):
        info = response.read().decode("utf-8")
    return info


def get_version_win32():
    return download_info(
        "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip.ver",
        "text/plain",
    )




def get_version_macos():
    return json.loads(
        download_info(
            "https://evermeet.cx/ffmpeg/info/ffmpeg/release", "application/json"
        )
    )["version"]


def get_version_linux():

    return re.search(
        r"version: (\d+\.\d+(?:\.\d+)?)",
        download_info(
            "https://johnvansickle.com/ffmpeg/release-readme.txt",
            "text/plain",
            ctx,
        ),
    )[1]


def download_file(outfile, url, content_type, ctx=None, progress=None):

    if progress:
        progress(0, 1)

    with download_base(url, content_type, ctx) as (response, nbytes):

        blksz = nbytes // 32 or 1024 * 1024
        with open(outfile, "wb") as f:
            nread = 0
            while True:
                b = response.read(blksz)
                if not b:
                    break
                f.write(b)
                nread += len(b)
                if progress:
                    progress(nread, nbytes)

    return outfile


# if sys.platform == 'win32':
#     def


def download_win32(download_dir, build_type=None, progress=None):
    build_types = ("essentials", "full", "full-shared")
    if build_type is None:
        build_type = build_types[0]
    elif build_type not in build_types:
        raise ValueError(f"Invalid build_type specified. Must be one of {build_types}")

    zippath = path.join(download_dir, "ffmpeg_win32.zip")
    url = f"https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-{build_type}.zip"
    download_file(zippath, url, "application/zip", progress=progress)
    return (zippath,)


def download_macos(download_dir, progress=None):
    zipffmpegpath = path.join(download_dir, "ffmpeg_macos.zip")
    download_file(
        zipffmpegpath,
        "https://evermeet.cx/ffmpeg/getrelease/ffmpeg/zip",
        "application/zip",
        progress=progress,
    )
    zipffprobepath = path.join(download_dir, "ffprobe_macos.zip")
    download_file(
        zipffprobepath,
        "https://evermeet.cx/ffmpeg/getrelease/ffprobe/zip",
        "application/zip",
        progress=progress,
    )
    return zipffmpegpath, zipffprobepath


def download_linux(download_dir, arch=None, progress=None):
    archs = ("amd64", "i686", "arm64", "armhf", "armel")
    if arch is None:
        arch = archs[0]
    elif arch not in archs:
        raise ValueError(f"Invalid arch specified. Must be one of {arch}")
    zippath = path.join(download_dir, "ffmpeg_linux.tar.xz")
    url = (
        f"https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-{arch}-static.tar.xz"
    )

    download_file(zippath, url, "application/x-xz", ctx, progress=progress)
    return zippath


print(get_version_win32(), get_version_macos(), get_version_linux())

download_dir = "tests"
download_win32(download_dir)
download_macos(download_dir)
download_linux(download_dir)
