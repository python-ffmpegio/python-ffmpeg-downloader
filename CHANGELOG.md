# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/) and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.5.3] - 2026-8-11

### Fixed

- Pre-v0.5 backward compatibility fix

## [0.5.2] - 2026-06-03

### Fixed

- a bug which prevented to install a specific version
- require packaging>=26.2 to use the Version class for typing

### Changed

- console message during install to specify both version and build type
- bypass jvs release gathering if failed to retrieve data

## [0.5.1] - 2026-05-19

### Fixed

- a bug in updating the config file in old format <0.5.0
- removed debug print message at the end of install command

## [0.5.0] - 2026-05-17

### Added

- Support to install the latest git master snapshot and old releases
- Architecture auto-detection
- Two new providers: BtBN and OSXExperts (arm64 support)

### Changed

- Revamped provider/configuration data handling
- ``ffdl.ffmpeg_version`` returns ``Version``, provider string, and build type string if installed

## [0.4.1] - 2025-11-14

### Fixed

- (PR#9 by @ucordia) Fix dst argument to accept a single value instead of list

## [0.4.0] - 2025-02-10

### Changed

- `ffdl.installed` can return the path with new optional argument `return_path=True`
- `ffdl.ffxxx_path` attributes returns None if the binary is not installed

### Fixed

- `main` - allows no input argument (display the help text)

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

[Unreleased]: https://github.com/python-ffmpegio/python-ffmpegio/compare/v0.5.3...HEAD
[0.5.3]: https://github.com/python-ffmpegio/python-ffmpegio/compare/v0.5.2...v0.5.3
[0.5.2]: https://github.com/python-ffmpegio/python-ffmpegio/compare/v0.5.1...v0.5.2
[0.5.1]: https://github.com/python-ffmpegio/python-ffmpegio/compare/v0.5.0...v0.5.1
[0.5.0]: https://github.com/python-ffmpegio/python-ffmpegio/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/python-ffmpegio/python-ffmpegio/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/python-ffmpegio/python-ffmpegio/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/python-ffmpegio/python-ffmpegio/compare/v0.1.4...v0.2.0
[0.1.4]: https://github.com/python-ffmpegio/python-ffmpegio/compare/v0.1.3...v0.1.4
[0.1.3]: https://github.com/python-ffmpegio/python-ffmpegio/compare/v0.1.2...v0.1.3
[0.1.2]: https://github.com/python-ffmpegio/python-ffmpegio/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/python-ffmpegio/python-ffmpegio/compare/94bbcc4...v0.1.1
