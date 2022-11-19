from pprint import pprint
import ffmpeg_downloader._win32 as _

_.retrieve_releases_page(1)


ver = _.get_latest_version()
release_assets = _.find_release_assets(ver)

# find asset of the latest snapshot
snapshot = _.get_latest_snapshot()
snapshot_assets = _.find_snapshot_assets(snapshot)

print(f"release v{ver}")
pprint(release_assets)
print(f"snapshot {snapshot}")
pprint(snapshot_assets)

