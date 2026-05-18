from pprint import pprint

from ffmpeg_downloader._providers.btbn import gather_builds

# import json
# from os import path
# jsonfile = "sandbox/btbn.json"

# if path.exists(jsonfile):
#     with open("sandbox/btbn.json", "rt") as f:
#         release_catalog, nightly_catalog = json.load(f)
#     release_catalog = {
#         Version(k): [Build(**b) for b in v] for k, v in release_catalog.items()
#     }
# else:
release_catalog, nightly_catalog = gather_builds()
#     release_catalog = {
#         str(k): [dataclasses.asdict(b) for b in v] for k, v in release_catalog.items()
#     }
#     with open("sandbox/btbn.json", "wt") as f:
#         json.dump((release_catalog, nightly_catalog), f)

pprint(release_catalog)
pprint(nightly_catalog)

pprint(max(release_catalog.keys()))
