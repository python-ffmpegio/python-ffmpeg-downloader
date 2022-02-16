from os import path
from posixpath import relpath
import sys
from urllib import request, parse
import shutil
from glob import glob
import re
from os import path
from contextlib import contextmanager


import ssl
from pprint import pprint

import tarfile, zipfile

download_dir = "tests"

with zipfile.ZipFile(path.join(download_dir,'ffmpeg_win32.zip'),'r') as f:
    f.extractall(download_dir)
with zipfile.ZipFile(path.join(download_dir,'ffmpeg_macos.zip'),'r') as f:
    f.extractall(download_dir)
with zipfile.ZipFile(path.join(download_dir,'ffprobe_macos.zip'),'r') as f:
    f.extractall(download_dir)
with tarfile.open(path.join(download_dir,'ffmpeg_linux.tar.xz'),'r') as f:
    f.extractall(download_dir)
