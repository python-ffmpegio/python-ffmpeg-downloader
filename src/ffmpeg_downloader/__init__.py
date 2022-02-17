__version__ = "0.0.0"

import sys

if sys.platform in ("win32", "cygwin"):
    from ._win32 import download_n_install, get_version
elif sys.platform == "darwin":
    from ._macos import download_n_install, get_version
else:
    from ._linux import download_n_install, get_version
