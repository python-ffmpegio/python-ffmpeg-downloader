from pprint import pprint

import ffmpeg_downloader._gh_ffmpeg as ffmpeg

ffmpeg_url = "https://api.github.com/repos/ffmpeg/ffmpeg"

tags = ffmpeg.get_releases(hash_length=10)

pprint(tags)
