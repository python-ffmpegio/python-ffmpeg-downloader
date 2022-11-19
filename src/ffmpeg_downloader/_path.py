from os import path
from appdirs import user_data_dir

def get_dir():
    return user_data_dir("ffmpeg-downloader", "ffmpegio")

def get_cache_dir():
    return path.join(get_dir(),'cache')

def get_bin_dir():
    return path.join(get_dir(),'cache')
