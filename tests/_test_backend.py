from pprint import pprint

from ffmpeg_downloader import _backend as ffdl


def test_backend_list():

    ffdl.list()
    ffdl.list(force=True)


def test_backend_search():

    # releases = ffdl.search("v7", auto_select=True)
    releases = ffdl.search("=v7.0.2", auto_select=True)
    # releases = ffdl.search("v6.1", auto_select=True)
    # releases = ffdl.search("v6.1", auto_select=True)
    pprint(releases)

    pprint(ffdl.search("snapshot"))


test_backend_search()
