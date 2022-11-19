from ffmpeg_downloader._macos import (
    get_latest_version,
    get_latest_snapshot,
    update_releases_info,
    get_download_info,
    extract,
    set_env_path,clr_env_path
)
from ffmpeg_downloader._config import Config
from ffmpeg_downloader._download_helper import download_file
from pprint import pprint
from packaging.version import Version
import re
from os import makedirs, path

print(set_env_path('~/test/ffmpeg'))
clr_env_path('~/test/ffmpeg')
exit()
dldir = path.join("tests", "macos")
makedirs(dldir, exist_ok=True)

ver = get_latest_snapshot()
config = Config().snapshot
pprint(ver)
pprint(config)
info = get_download_info(ver, None)
pprint(info)
for name, url, content_type, _ in info:
    try:
        download_file(path.join(dldir, name), url, headers={"Accept": content_type})
    except:
        pass

print(extract((path.join(dldir, name) for name, *_ in info), "tests/install"))


ver = get_latest_version()
update_releases_info()
info = get_download_info(ver, None)

for name, url, content_type, _ in info:
    try:
        download_file(path.join(dldir, name), url, headers={"Accept": content_type})
    except:
        pass
