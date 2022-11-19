from tqdm import tqdm
from tqdm.utils import CallbackIOWrapper


class DownloadProgress:
    def __init__(self, nbytes) -> None:
        self.tqdm = tqdm(desc="downloading", total=nbytes, unit=" bytes", leave=False)
        self.last = 0

    def update(self, nread):
        self.tqdm.update(nread - self.last)
        self.last = nread

    def close(self):
        self.tqdm.close()


class InstallProgress:
    def __init__(self, sz) -> None:
        self.tqdm = tqdm(
            desc="installing",
            unit="B",
            unit_scale=True,
            unit_divisor=1024,
            total=sz,
            leave=False,
        )

    def io_wrapper(self, fi):
        return CallbackIOWrapper(self.tqdm.update, fi)

    def close(self):
        self.tqdm.close()
