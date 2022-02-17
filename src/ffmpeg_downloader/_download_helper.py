from urllib import request
from contextlib import contextmanager
import os, stat


@contextmanager
def download_base(url, content_type, ctx=None):
    with request.urlopen(url, timeout=1.0, context=ctx) as response:
        # pprint(response.headers.get_content_type())
        if response.headers.get_content_type() != content_type:
            raise RuntimeError(f'"{url}" is not the expected content type.')
        try:
            nbytes = int(response.getheader("content-length"))
        except:
            nbytes = 0
        yield response, nbytes


def download_info(url, content_type, ctx=None):
    with download_base(url, content_type, ctx) as (response, nbytes):
        info = response.read().decode("utf-8")
    return info


def download_file(outfile, url, content_type, ctx=None, progress=None):

    if progress:
        progress(0, 1)

    with download_base(url, content_type, ctx) as (response, nbytes):

        blksz = nbytes // 32 or 1024 * 1024
        with open(outfile, "wb") as f:
            nread = 0
            while True:
                b = response.read(blksz)
                if not b:
                    break
                f.write(b)
                nread += len(b)
                if progress:
                    progress(nread, nbytes)

    return outfile


def chmod(binfile):
    # Set bits for execution and read for all users.
    exe_bits = stat.S_IXOTH | stat.S_IXUSR | stat.S_IXGRP
    read_bits = stat.S_IRUSR | stat.S_IRGRP | stat.S_IXGRP
    write_bits = stat.S_IWUSR | stat.S_IWGRP | stat.S_IWGRP
    os.chmod(binfile, exe_bits | read_bits | write_bits)
