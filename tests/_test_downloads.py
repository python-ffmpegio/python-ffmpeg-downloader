from ffmpeg_downloader import _win32, _macos, _linux
import tempfile,os

with tempfile.TemporaryDirectory() as dir:

    for mod in (_win32,_macos,_linux):
        mname = mod.__name__
        dstdir = os.path.join(dir,mname)
        os.mkdir(dstdir)
        print(dstdir)
        print(mod.get_version())
        mod.download_n_install(dstdir)
