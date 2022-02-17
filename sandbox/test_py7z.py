from py7zlib import Archive7z

#setup
with open(filename, 'rb') as fp:
    archive = Archive7z(fp)
    filenames = archive.getnames()
    for filename in filenames:
        cf = archive.getmember(filename)
        try:
            cf.checkcrc()
        except:
            raise RuntimeError(f"crc failed for {filename}")

        b = cf.read()
        try:
            assert len(b)==cf.uncompressed
        except:
            raise RuntimeError(f"incorrect uncompressed file size for {filename}")

