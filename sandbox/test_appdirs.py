import platformdirs

# get current version
# get current paths (ffmpeg/ffprobe)
# delete current version
# copy

app = "ffmpeg-downloader", "python-ffmpegio"

print(platformdirs.user_data_dir(*app))
