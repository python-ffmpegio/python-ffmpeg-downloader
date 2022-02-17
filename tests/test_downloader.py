from os import makedirs, path, system
from ffmpeg_downloader import download_n_install, get_version


def test_download():

    print(get_version())

    install_dir = path.join("tests", "ffmpeg-downloader")
    makedirs(install_dir, exist_ok=True)
    ffmpeg_path, ffprobe_path = download_n_install(install_dir)
    ret = system(f"{ffmpeg_path} -version")
    assert ret == 0
    ret = system(f"{ffprobe_path} -version")
    assert ret == 0
