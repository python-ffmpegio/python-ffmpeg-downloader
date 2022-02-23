`ffmpeg-downloader`: Python FFmpeg release build downloader
===========================================================

|pypi| |pypi-status| |pypi-pyvers| |github-license| |github-status|

.. |pypi| image:: https://img.shields.io/pypi/v/ffmpeg-downloader
  :alt: PyPI
.. |pypi-status| image:: https://img.shields.io/pypi/status/ffmpeg-downloader
  :alt: PyPI - Status
.. |pypi-pyvers| image:: https://img.shields.io/pypi/pyversions/ffmpeg-downloader
  :alt: PyPI - Python Version
.. |github-license| image:: https://img.shields.io/github/license/python-ffmpegio/python-ffmpeg-downloader
  :alt: GitHub License
.. |github-status| image:: https://img.shields.io/github/workflow/status/python-ffmpegio/python-ffmpeg-downloader/Run%20Tests
  :alt: GitHub Workflow Status

Python `ffmpeg-downloader` package automatically downloads the latest FFmpeg release binaries for Windows, Linux, & MacOS. Note 
while it supports Linux and MacOS, it is intended for Windows users, for whom there is no installer is currently
available. Linux and MacOS users are encouraged to install via the OS package manager (e.g., `apt-get` for Ubuntu and `brew` for MacOS).

The FFmpeg release builds are downloaded from 3rd party hosts:

=======  ==========================================================================
Windows  `https://www.gyan.dev/ffmpeg/builds <https://www.gyan.dev/ffmpeg/builds>`_
Linux    `https://johnvansickle.com/ffmpeg <https://johnvansickle.com/ffmpeg>`_
MacOS    `https://evermeet.cx/ffmpeg <https://evermeet.cx/ffmpeg>`_
=======  ==========================================================================

If you appreciate their effort to build and host these builds, please consider donating on their websites.

This package is used in `ffmpegio-plugin-downloader <https://github.com/python-ffmpegio/python-ffmpegio-plugin-downloader>`__
to enable automatic detection of the FFmpeg executable.

Installation
------------

.. code-block:: bash

   pip install ffmpeg-downloader

Console Commands
----------------

To download and install FFmpeg binaries
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

  python -m ffmpeg_downloader

To check for a newer release and update if available
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

  python -m ffmpeg_downloader --update

To uninstall
^^^^^^^^^^^^

.. code-block:: bash

  python -m ffmpeg_downloader --remove

In Python
---------

This package exposes the following 4 attributes:

.. code-block:: python
  
  import ffmpeg_downloader as ffdl

  ffdl.ffmpeg_dir     # FFmpeg binaries directory 
  ffdl.ffmpeg_version # version string of the intalled FFmpeg
  ffdl.ffmpeg_path    # full path of the FFmpeg binary
  ffdl.ffprobe_path   # full path of the FFprobe binary
