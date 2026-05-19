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
.. |github-status| image:: https://img.shields.io/github/actions/workflow/status/python-ffmpegio/python-ffmpeg-downloader/test_n_pub.yml?branch=main
  :alt: GitHub Workflow Status

Python `ffmpeg-downloader` package automatically downloads the latest FFmpeg prebuilt binaries for Windows, Linux, & MacOS. 
It's cli interface mimics that of `pip` to install, uninstall, list, search, and download available FFmpeg versions. This package
is ideal for those who:

- Use the git snapshot version of FFmpeg
- Are in Windows environment
 
Those who intend to use a release version in Linux and MacOS are encouraged to install via the OS package manager 
(e.g., `apt-get` for Ubuntu and `brew` for MacOS).

The FFmpeg builds will be downloaded from 3rd party hosts:

===============  ================================================================================
Windows & Linux  `https://github.com/BtbN/FFmpeg-Builds <https://github.com/BtbN/FFmpeg-Builds>`_
Windows          `https://www.gyan.dev/ffmpeg/builds <https://www.gyan.dev/ffmpeg/builds>`_
Linux            `https://johnvansickle.com/ffmpeg <https://johnvansickle.com/ffmpeg>`_
MacOS            `https://osxexperts.net/ <https://osxexperts.net>`_
MacOS            `https://evermeet.cx/ffmpeg <https://evermeet.cx/ffmpeg>`_
===============  ================================================================================

If you appreciate their effort to build and host these builds, please consider donating on their websites.

Note that BtbN and Gyan offer multiple build types. Use the `ffdl.list` command.


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

Use ``list`` and ``search`` commands to see available releases.

The ``list`` command lists all the releases:

.. code-block:: bash

  ffdl list

An example Linux output:

.. code-block:: bash

  Version        Available Builds (*=cached)          Provider
  -------------  -----------------------------------  -----------------
  3.3.4          static                               johnvansickle.com
  3.4.2          static                               johnvansickle.com
  4.0.3          static                               johnvansickle.com
  4.1.4          static                               johnvansickle.com
  4.2.1          static                               johnvansickle.com
  4.2.2          static                               johnvansickle.com
  4.3.1          static                               johnvansickle.com
  4.3.2          static                               johnvansickle.com
  4.4            static                               johnvansickle.com
  4.4.1          static                               johnvansickle.com
  5.0.1          static                               johnvansickle.com
  5.1.1          static                               johnvansickle.com
  5.1.5.post106  gpl, gpl-shared, lgpl, lgpl-shared   btbn
  5.1.6.post16   gpl, gpl-shared, lgpl, lgpl-shared   btbn
  6.0            static                               johnvansickle.com
  6.0.1          static                               johnvansickle.com
  6.1.1.post329  gpl, gpl-shared, lgpl, lgpl-shared   btbn
  6.1.2.post192  gpl, gpl-shared, lgpl, lgpl-shared   btbn
  7.0.1.post221  gpl, gpl-shared, lgpl, lgpl-shared   btbn
  7.0.2          static*                              johnvansickle.com
  7.0.2.post6    gpl, gpl-shared, lgpl, lgpl-shared   btbn
  7.1.post214    gpl, gpl-shared, lgpl, lgpl-shared   btbn
  7.1.1.post57   gpl, gpl-shared, lgpl, lgpl-shared   btbn
  7.1.2.post7    gpl, gpl-shared, lgpl, lgpl-shared   btbn
  7.1.3.post46   gpl, gpl-shared, lgpl, lgpl-shared   btbn
  8.0.post30     gpl, gpl-shared, lgpl, lgpl-shared   btbn
  8.0.1.post66   gpl, gpl-shared, lgpl, lgpl-shared   btbn
  8.1.post11     gpl*, gpl-shared, lgpl, lgpl-shared  btbn
  8.1.1.post1    gpl*, gpl-shared*, lgpl*             btbn
  8.1.1.post2    gpl, gpl-shared, lgpl, lgpl-shared   btbn

  To install specific build, ffdl install <version>@<build_type>

Note: Currently ``-shared`` builds in Linux could not be used in Python


Windows output:

.. code-block:: bash

  Version        Available Builds (*=cached)         Provider
  -------------  ----------------------------------  ----------
  4.4            essentials, full, full-shared       gyan
  4.4.1          essentials, full, full-shared       gyan
  5.0            essentials, full, full-shared       gyan
  5.0.1          essentials, full, full-shared       gyan
  5.1            essentials, full, full-shared       gyan
  5.1.1          essentials, full, full-shared       gyan
  5.1.2          essentials, full, full-shared       gyan
  5.1.5.post106  gpl, gpl-shared, lgpl, lgpl-shared  btbn
  5.1.6.post16   gpl, gpl-shared, lgpl, lgpl-shared  btbn
  6.0            essentials, full, full-shared       gyan
  6.1            essentials, full, full-shared       gyan
  6.1.1          essentials, full, full-shared       gyan
  6.1.1.post329  gpl, gpl-shared, lgpl, lgpl-shared  btbn
  6.1.2.post192  gpl, gpl-shared, lgpl, lgpl-shared  btbn
  7.0            essentials, full, full-shared       gyan
  7.0.1          essentials, full, full-shared       gyan
  7.0.1.post221  gpl, gpl-shared, lgpl, lgpl-shared  btbn
  7.0.2          essentials, full, full-shared       gyan
  7.0.2.post6    gpl, gpl-shared, lgpl, lgpl-shared  btbn
  7.1            essentials, full, full-shared       gyan
  7.1.post214    gpl, gpl-shared, lgpl, lgpl-shared  btbn
  7.1.1          essentials, full, full-shared       gyan
  7.1.1.post57   gpl, gpl-shared, lgpl, lgpl-shared  btbn
  7.1.2.post7    gpl, gpl-shared, lgpl, lgpl-shared  btbn
  7.1.3.post46   gpl, gpl-shared, lgpl, lgpl-shared  btbn
  8.0            essentials, full, full-shared       gyan
  8.0.post30     gpl, gpl-shared, lgpl, lgpl-shared  btbn
  8.0.1          essentials, full, full-shared       gyan
  8.0.1.post66   gpl, gpl-shared, lgpl, lgpl-shared  btbn
  8.1            essentials, full, full-shared       gyan
  8.1.post11     gpl, gpl-shared, lgpl, lgpl-shared  btbn
  8.1.1          essentials, full, full-shared       gyan
  8.1.1.post2    gpl, gpl-shared, lgpl, lgpl-shared  btbn

  To install specific build, ffdl install <version>@<build_type>


For MacOS (arm64), only one file would be listed:
 
.. code-block:: bash

    Version  Available Builds (*=cached)    Provider
  ---------  -----------------------------  --------------
        8.1  static                         osxexperts.net

  To install specific build, ffdl install <version>@<build_type>

 
The ``search`` command lists only the releases that matches the query:

.. code-block:: bash

  ffdl search 7 # lists all v7 releases 
  ffdl search @gpl # list all releases with gpl builds (of btbn)
  ffdl search =7.0.2 # lists only v7.0.2 release, excluding 7.0.2post versions


To specify a release version:
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Add version number as the last argument of the ``install`` command similar as
the ``search`` command:

.. code-block:: bash

  ffdl install 7 # install the latest v7 release
  ffdl install @gpl # install the latest BtBN gpl build of FFmpeg 7
  ffdl install =7.0.2 # install the 7.0.2 release from johnvansickle.com or 
                      # gyan.dev (excludes BtBN post release)

   ffdl install snapshot@full   # full build of latest snapshot
   
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
