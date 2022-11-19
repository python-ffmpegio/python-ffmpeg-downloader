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

Python `ffmpeg-downloader` package automatically downloads the latest FFmpeg prebuilt binaries for Windows, Linux, & MacOS. 
It's cli interface mimics that of `pip` to install, uninstall, list, search, and download available FFmpeg versions. This package
is ideal for those who:

- Use the git snapshot version of FFmpeg
- Are in Windows environment
 
Those who intend to use a release version in Linux and MacOS are encouraged to install via the OS package manager 
(e.g., `apt-get` for Ubuntu and `brew` for MacOS).

The FFmpeg builds will be downloaded from 3rd party hosts:

=======  ==========================================================================
Windows  `https://www.gyan.dev/ffmpeg/builds <https://www.gyan.dev/ffmpeg/builds>`_
Linux    `https://johnvansickle.com/ffmpeg <https://johnvansickle.com/ffmpeg>`_
MacOS    `https://evermeet.cx/ffmpeg <https://evermeet.cx/ffmpeg>`_
=======  ==========================================================================

If you appreciate their effort to build and host these builds, please consider donating on their websites.

Installation
------------

.. code-block:: bash

   pip install ffmpeg-downloader

Console Commands
----------------

In cli, use `ffdl` command after the package is installed. Alternately, you can call the module by 
`python -m ffmpeg_downloader`. For full help, run:

.. code-block::

  ffdl -h <command>

To download and install FFmpeg binaries
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

  ffdl install

This command downloads and installs the latest FFmpeg **release**. You will see the progress messages
similar to the following:

.. code-block:: bash

   Collecting ffmpeg 
     Using cached ffmpeg-5.1.2-essentials_build.zip (79 MB)
   Installing collected FFmpeg binaries: 5.1.2@essentials
   Successfully installed FFmpeg binaries: 5.1.2@essentials in
     C:\Users\User\AppData\Local\ffmpegio\ffmpeg-downloader\ffmpeg\bin

In Linux, symlinks fo the installed binaries are automatically created in `~/.local/bin` or `~/bin`
so the FFmpeg commands are immediately available (only if one of these directories already exists).

In Windows and MacOS, the binary folder can be added to the system path by `--add-path` option:

.. code-block:: bash

  ffdl install --add-path

The new system paths won't be applied to the current console window. You may need to close and reopen
or possibly log out and log back in for the change to take effect.

To install the latest git master snapshot build:
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

  ffdl install snapshot

To list or search available release versions:
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Use ``list`` and ``search`` commands.

.. code-block:: bash

  ffdl list     # lists all available releases

  ffdl search 5 # lists all v5 releases 


To specify a release version:
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Add version number as the last argument of the command:

.. code-block:: bash

  ffdl install 4.4

Additionally, there are multiple options for each build for the Windows builds:

===============    ===========================================================================
``essentials``     Built only with commonly used third-party libraries (default option)
``full``           Built with the most third-party libraries
``full-shared``    Same as ``full`` but separate shared libraries (DLLs) and development files 
                   (release builds only)
===============    ===========================================================================

Visit `gyan.dev <https://www.gyan.dev/ffmpeg/builds/#about-these-builds>`_ for more information. 
To specify which flavor to install, use ``@``

.. code-block:: bash

   ffdl install snapshot@full   # full build of latest snapshot
   ffdl install 5.2@full-shared # full build of v5.2

To update or change version if available
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Like ``pip``, use ``-U`` or ``--upgrade`` flag 

.. code-block:: bash

  ffdl install -U

To uninstall
^^^^^^^^^^^^

.. code-block:: bash

  ffdl uninstall

In Python
---------

This package has the following useful attributes:

.. code-block:: python
  
  import ffmpeg_downloader as ffdl

  ffdl.ffmpeg_dir     # FFmpeg binaries directory 
  ffdl.ffmpeg_version # version string of the intalled FFmpeg
  ffdl.ffmpeg_path    # full path of the FFmpeg binary
  ffdl.ffprobe_path   # full path of the FFprobe binary
  ffdl.ffplay_path    # full path of the FFplay binary


The ``ffxxx_path`` attributes are useful to call FFxxx command with ``subprocess``:

.. code-block:: python

  # To call FFmpeg via subprocess
  import subprocess as sp

  sp.run([ffdl.ffmpeg_path, '-i', 'input.mp4', 'output.mkv'])

Meanwhile, there are many FFmpeg wrapper packages which do not let you specify the
FFmpeg path or cumbersome to do so. If installing the FFmpeg with ``--add-path`` option is
not preferable, use `ffmpeg_downloader.add_path()` function to make the binaries available
to these packages.
