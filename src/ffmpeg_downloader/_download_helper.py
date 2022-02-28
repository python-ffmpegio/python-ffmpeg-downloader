import os, stat
import requests


def download_base(url, content_type, timeout=None, stream=True):
    response = requests.get(url, timeout=timeout, stream=stream)
    if response.headers.get("content-type", "text/plain") != content_type:
        raise RuntimeError(f'"{url}" is not the expected content type.')
    return response


def download_info(url, content_type, timeout=None):
    response = download_base(url, content_type, timeout, stream=False)
    return response.text


def download_file(outfile, url, content_type, progress=None, timeout=None):

    response = download_base(url, content_type, timeout)

    nbytes = int(response.headers["Content-Length"])

    if progress:
        progress(0, nbytes)

    blksz = nbytes // 32 or 1024 * 1024
    with open(outfile, "wb") as f:
        nread = 0
        for b in response.iter_content(chunk_size=blksz):
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
