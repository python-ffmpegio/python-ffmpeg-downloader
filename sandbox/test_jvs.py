from pprint import pprint

from ffmpeg_downloader._providers.johnvansickle import gather_builds

jsonfile = "sandbox/btbn.json"

pprint(gather_builds())
