from urllib import request
from contextlib import contextmanager
import os, stat, ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE


@contextmanager
def download_base(url, content_type, timeout=None):
    with request.urlopen(url, timeout=timeout or 5.0, context=ctx) as response:
        # pprint(response.headers.get_content_type())
        if response.headers.get_content_type() != content_type:
            raise RuntimeError(f'"{url}" is not the expected content type.')
        try:
            nbytes = int(response.getheader("content-length"))
        except:
            nbytes = 0
        yield response, nbytes


def download_info(url, content_type, timeout=None):
    with download_base(url, content_type, timeout) as (response, nbytes):
        info = response.read().decode("utf-8")
    return info


def download_file(outfile, url, content_type, progress=None, timeout=None):

    with download_base(url, content_type, timeout) as (response, nbytes):
        if progress:
            progress(0, nbytes)

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

    return nbytes


def chmod(binfile):
    # Set bits for execution and read for all users.
    exe_bits = stat.S_IXOTH | stat.S_IXUSR | stat.S_IXGRP
    read_bits = stat.S_IRUSR | stat.S_IRGRP | stat.S_IXGRP
    write_bits = stat.S_IWUSR | stat.S_IWGRP | stat.S_IWGRP
    os.chmod(binfile, exe_bits | read_bits | write_bits)
