import os, stat
import requests
from requests.adapters import HTTPAdapter


def download_info(
    url, headers={}, params={}, stream=False, timeout=None, retries=None, proxy=None
):
    http = requests.Session()
    http.mount("https://", HTTPAdapter(max_retries=5))
    response = http.get(
        url,
        headers=headers,
        params=params,
        timeout=timeout,
        stream=stream,
        proxies=proxy,
    )
    return response


def download_file(
    outfile,
    url,
    headers={},
    params={},
    progress=None,
    timeout=None,
    retries=None,
    proxy=None,
):

    response = download_info(
        url, headers, params, stream=True, timeout=timeout, retries=retries, proxy=proxy
    )

    nbytes = int(response.headers.get("Content-Length", 0))

    if progress:
        progress = progress(nbytes)

    blksz = nbytes // 32 or 1024 * 1024
    with open(outfile, "wb") as f:
        nread = 0
        for b in response.iter_content(chunk_size=blksz):
            if not b:
                break
            f.write(b)
            nread += len(b)
            if progress:
                progress.update(nread)

    return nbytes


def chmod(binfile):
    # Set bits for execution and read for all users.
    exe_bits = stat.S_IXOTH | stat.S_IXUSR | stat.S_IXGRP
    read_bits = stat.S_IRUSR | stat.S_IRGRP | stat.S_IXGRP
    write_bits = stat.S_IWUSR | stat.S_IWGRP | stat.S_IWGRP
    os.chmod(binfile, exe_bits | read_bits | write_bits)
