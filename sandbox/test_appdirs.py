import appdirs

# get current version
# get current paths (ffmpeg/ffprobe)
# delete current version
# copy

app = "ffmpeg-downloader", "python-ffmpegio"

print(appdirs.user_data_dir(*app))
