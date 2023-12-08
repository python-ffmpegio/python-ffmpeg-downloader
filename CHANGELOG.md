# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/) and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.0] - 2023-12-07

### Added

- Support for aarch64
- Qt QWizard subclass InstallFFmpegWizard
- Run wizard with command `ffdl-gui`
- Switched to using platformdirs package from appdirs

### Fixed

- uninstall command argument processing
- uninstall clear env vars
- linux clr_symlinks()
- downloader no longer try to copy again to cache dir
- [win32] error finding snapshot assets 

## [0.2.0] - 2022-11-19

### Changed

- Completely reworked CLI commands to mimic pip: install, uninstall, download, list, search

### Added

- Support to install the latest git master snapshot and old releases
- `--add-path` CLI option to insert FFmpeg path to system user path
- `add_path()` Python function to add FFmpeg path to process path 
- Other CLI options


## [0.1.4] - 2022-02-27

### Changed

- Switched from `urllib` to `requests` package for HTTP interface
## [0.1.3] - 2022-02-22

### Fixed

- Fixed `ffmpeg_dir` attribute

## [0.1.2] - 2022-02-20

### Fixed

- PyPI description not shown

## [0.1.1] - 2022-02-20

- First release via GitHub Action

[Unreleased]: https://github.com/python-ffmpegio/python-ffmpegio/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/python-ffmpegio/python-ffmpegio/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/python-ffmpegio/python-ffmpegio/compare/v0.1.4...v0.2.0
[0.1.4]: https://github.com/python-ffmpegio/python-ffmpegio/compare/v0.1.3...v0.1.4
[0.1.3]: https://github.com/python-ffmpegio/python-ffmpegio/compare/v0.1.2...v0.1.3
[0.1.2]: https://github.com/python-ffmpegio/python-ffmpegio/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/python-ffmpegio/python-ffmpegio/compare/94bbcc4...v0.1.1
