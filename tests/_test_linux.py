from ffmpeg_downloader._linux import (
    get_latest_version,
    get_latest_snapshot,
    update_releases_info,
    get_download_info,
    extract,
)
from ffmpeg_downloader._config import Config
from ffmpeg_downloader._download_helper import download_file
from pprint import pprint
from packaging.version import Version
import re
from os import makedirs, path

dldir = path.join("tests", "linux")
makedirs(dldir, exist_ok=True)

update_releases_info(True)

# ver = get_latest_snapshot()
# config = Config().snapshot
# pprint(ver)
# pprint(config)
# info = get_download_info(ver, None)
# pprint(info)
# for name, url, content_type, _ in info:
#     dst = path.join(dldir, name)
#     if path.exists(dst):
#         continue
#     try:
#         download_file(dst, url, headers={"Accept": content_type})
#     except Exception as e:
#         print('errored', type(e),name,url)
#         pass

# print(extract([path.join(dldir, name) for name, *_ in info], "tests/install"))

pprint(Config().releases)

ver = get_latest_version()
print(ver)
info = get_download_info(ver, None)
print(info)

# for name, url, content_type, _ in info:
#     print(name,url)
#     try:
#         download_file(path.join(dldir, name), url, headers={"Accept": content_type})
#     except:
#         pass
