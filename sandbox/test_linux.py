from pprint import pprint

import ffmpeg_downloader._linux as linux

config = linux.Config()

config._gather_builds()

pprint(config.releases)
pprint(config.nightly)
