from os import path
from posixpath import relpath
import sys
from urllib import request, parse
import shutil
from glob import glob
import re
from os import path


import ssl

sources = {
    "win32": {
        "url": "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-{build_type}.7z",
        "build_type": ("essentials", "full", "full-shared"),
        "content_type": "application/x-7z-compressed",
    },
    "darwin": {
        "url": "https://evermeet.cx/ffmpeg/getrelease/{app_name}/7z",
        "app_name": ("ffmpeg", "ffprobe"),
        "content_type": "application/x-7z-compressed",
        "download_all": True,
    },
    "linux": {
        "url": "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-{arch}-static.tar.xz",
        "arch": ("amd64", "i686", "arm64", "armhf", "armel"),
        "content_type": "application/x-xz",
        "need_ctx": True,
    },
}


def download(dstpath, platform=sys.platform, **opts):
    src = sources[platform]

    if src.get("need_ctx", False):
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
    else:
        ctx = None

    url = src["url"]
    m = re.search(r"\{(.+?)\}", url)
    while m:
        key = m[1]
        val = opts.pop(key, src[key][0])
        if val not in src[key]:
            raise ValueError(f"Unknown value ({val}) specified for {key}.")
        url = url[: m.start()] + val + url[m.end() :]
        m = re.search(r"\{(.+?)\}", url)

    zippath = path.join(dstpath, path.basename(url))
    if not path.exists(zippath):
        with request.urlopen(url, context=ctx) as response:
            # pprint(response.headers.__dict__)
            if response.headers.get_content_type() != src["content_type"]:
                raise RuntimeError(f'"{url}" is not the expected content type.')
            try:
                nbytes = int(response.getheader("content-length"))
            except:
                nbytes = 0
            blksz = nbytes // 32 or 1024 * 1024
            with open(zippath, "wb") as f:
                nread = 0
                while True:
                    b = response.read(blksz)
                    if not b:
                        break
                    f.write(b)
                    nread += len(b)
                    print(f"downloaded: {nread}/{nbytes} bytes")

    return zippath

# --no-check-certificate


from pprint import pprint

download_dir = "tests"

zippath = download(download_dir,platform='linux')

import tarfile
with tarfile.open(zippath) as tar:
    tar.extractall(path='tests')
#
# 


# # import patoolib
# # patoolib.extract_archive(zippath, outdir=download_dir)

# # import os
# # os.system(r'')

# from py7zlib import Archive7z

# # setup
# with open(zippath, "rb") as fp:
#     archive = Archive7z(fp)
#     filenames = archive.getnames()
#     for filename in filenames:
#         cf = archive.getmember(filename)
#         print(f"{filename}: crc={cf.uncompressed:x}")
#         try:
#             cf.checkcrc()
#         except:
#             raise RuntimeError(f"crc failed for {filename}")

#         b = cf.read()
#         try:
#             assert len(b) == cf.uncompressed
#         except:
#             raise RuntimeError(f"incorrect uncompressed file size for {filename}")
