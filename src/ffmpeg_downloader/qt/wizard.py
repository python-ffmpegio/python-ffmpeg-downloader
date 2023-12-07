import logging

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

from tempfile import mkdtemp
from shutil import rmtree
from tqdm.utils import CallbackIOWrapper
from typing import Optional, Any
from os import path

from .. import _backend as ffdl
from .qt_compat import QtCore, QtWidgets, QtGui

from PyQt6.QtWidgets import QWizard

QObject = QtCore.QObject
QThread = QtCore.QThread
pyqtSignal = QtCore.pyqtSignal
pyqtSlot = QtCore.pyqtSlot
Qt = QtCore.Qt

QPixmap = QtGui.QPixmap

QWidget = QtWidgets.QWidget
# QWizard = QtWidgets.QWizard
QWizardPage = QtWidgets.QWizardPage
QVBoxLayout = QtWidgets.QVBoxLayout
QLabel = QtWidgets.QLabel
QProgressBar = QtWidgets.QProgressBar
QLineEdit = QtWidgets.QLineEdit


class DownloadProgress(QObject):
    def __init__(self, parent: QObject, diff: bool, progress) -> None:
        QObject.__init__(self, parent)
        self.diff = diff
        self.last = 0
        self.size = 0
        self.progress = progress

    def set_size(self, sz):
        logger.debug(f"progress: {sz} bytes total")
        self.size = sz

    def update(self, nread):
        if self.diff:
            self.last += nread
        else:
            self.last = nread
        logger.debug(f"progress: read {self.last}/{self.size}")
        self.progress.emit(self.last)

    def done(self):
        logger.debug(f"progress: done")
        self.progress.emit(self.size)


class InstallProgress(DownloadProgress):
    def io_wrapper(self, fi):
        return CallbackIOWrapper(self.update, fi)


class FFmpegInstaller(QObject):
    found_installed_version = pyqtSignal(str, bool)
    """version/done"""
    found_latest_version = pyqtSignal(tuple, bool)
    """version/done, if bool=False, wait for response via queue"""
    server_error = pyqtSignal(str)
    """str-exception message"""
    download_maximum = pyqtSignal(int)
    """download progress maximum"""
    download_progress = pyqtSignal(int)
    """download progress current"""
    install_maximum = pyqtSignal(int)
    """install progress maximum"""
    install_progress = pyqtSignal(int)
    """install progress current"""

    installed = pyqtSignal()
    """install finished"""

    finished = pyqtSignal()
    """emitted when there is no more task"""

    @pyqtSlot(bool, dict)
    def search(self, upgrade: bool, request_kws: dict[str, Any]):
        logger.debug("search: Begin searching for FFmpeg version")

        # first, check currently installed version
        current_version = ffdl.ffmpeg_version()
        already_exists = current_version is not None and not upgrade

        self.found_installed_version.emit(
            str(current_version[0]) if current_version else "", already_exists
        )

        if already_exists:
            logger.info("search: FFmpeg already installed")
            self.finished.emit()
            return

        try:
            version = ffdl.search(
                version_spec=None, auto_select=True, force=True, **request_kws
            )
            if version is None:
                raise RuntimeError("Could not find a suitable FFMpeg version.")
        except Exception as e:
            self.server_error.emit(str(e))
            self.finished.emit()
            return

        # check for a need to update
        already_exists = current_version is not None and (
            current_version[0] == version[0]
        )

        self.found_latest_version.emit(version, already_exists)
        if already_exists:
            self.finished.emit()

    @pyqtSlot(tuple, bool, dict)
    def install(self, version: tuple, exists: bool, request_kws: dict):
        # import debugpy
        # debugpy.debug_this_thread()
        logger.debug(f"install: begin installing v{version[0]}")

        download_info = ffdl.gather_download_info(*version, no_cache_dir=True)

        dl_mon = DownloadProgress(self, False, self.download_progress)
        in_mon = InstallProgress(self, True, self.install_progress)

        def downloadProgress(sz):
            self.download_maximum.emit(sz)
            dl_mon.set_size(sz)
            return dl_mon

        def installProgress(sz):
            self.install_maximum.emit(sz)
            in_mon.set_size(sz)
            return in_mon

        cache_dir = mkdtemp()
        try:
            # download
            dstpaths = ffdl.download(
                download_info,
                dst=cache_dir,
                progress=downloadProgress,
                no_cache_dir=True,
                **request_kws,
            )
            dl_mon.done()

            if exists:
                ffdl.remove()

            # install
            ffdl.install(*dstpaths, progress=installProgress)

            # all done
            in_mon.done()
            self.installed.emit()

        except Exception as e:
            self.server_error.emit(str(e))

        finally:
            rmtree(cache_dir, ignore_errors=True)
            self.finished.emit()


class InstallFFmpegWizard(QWizard):
    req_search = pyqtSignal(bool, dict)
    req_install = pyqtSignal(tuple, bool, dict)

    default_labels = {
        "search_current": "Searching for a local copy of the FFmpeg, a multimedia processing library...",
        "press_next": f"""Press Next to download the latest FFmpeg release build from 
<a href="{ffdl.home_url}">{ffdl.home_url}</a>.

Disclaimer: Proceeding to download the file is done at your own 
discretion and risk and with agreement that you will be solely 
responsible for any damage to your computer system or loss of data that results from
such activities.""",
        "current_ver": "Existing FFmpeg Version: v{}",
        "not_found": "Existing FFmpeg: Not Found",
        "exists": "FFmpeg already installed.",
        "search_latest": f'Searching for the latest FFmpeg version at <a href="{ffdl.home_url}">{ffdl.home_url}</a>...',
        "latest_ver": "Latest FFmpeg Version: v{}",
        "latest_installed": "The latest version already installed.",
        "dl_progress": "Download Progress",
        "ins_progress": "Install Progress",
        "ins_folder": "Installation Folder:",
        "ins_success": "Installation success",
    }

    def __init__(
        self,
        upgrade: bool = False,
        wizard_style: Optional[QWizard.WizardStyle] = None,
        wizard_pixmaps: Optional[dict[QWizard.WizardPixmap, QPixmap]] = None,
        window_title: Optional[str] = None,
        window_size: Optional[tuple[int, int]] = None,
        custom_labels: Optional[dict[str, str]] = None,
        parent: Optional[QWidget] = None,
        flags: Optional[Qt.WindowType] = None,
        proxy: Optional[str] = None,
        retries: Optional[int] = None,
        timeout: Optional[float | tuple[float, float]] = None,
    ):
        QWizard.__init__(self, parent)

        self.upgrade: bool = upgrade
        self.request_kws: dict = {
            "proxy": proxy,
            "retries": retries,
            "timeout": timeout,
        }
        self.old_ver_exists: bool = False
        self.version: tuple = None  # set by Page1, used by Page2
        self.install_finished: bool = False

        self.setWindowTitle(window_title or "FFmpeg Download & Install Wizard")
        if window_size is not None:
            self.resize(*window_size)

        if flags is not None:
            self.setWindowFlags(flags)

        self.setWizardStyle(wizard_style or QWizard.WizardStyle.ModernStyle)

        if wizard_pixmaps is None:
            wizard_pixmaps = {}
        if QWizard.WizardPixmap.WatermarkPixmap not in wizard_pixmaps:
            svgfile = path.join(path.dirname(__file__), "assets", "FFmpeg_icon.svg")
            wizard_pixmaps[QWizard.WizardPixmap.WatermarkPixmap] = QPixmap(svgfile)

        for which, pixmap in wizard_pixmaps.items():
            self.setPixmap(which, pixmap)

        self.setOptions(
            QWizard.WizardOption.NoBackButtonOnStartPage
            | QWizard.WizardOption.NoBackButtonOnLastPage
        )

        self.installer = FFmpegInstaller()
        self.installer_thread = QThread()
        self.installer.moveToThread(self.installer_thread)
        self.installer_thread.started.connect(self._thread_started)
        self.req_search.connect(self.installer.search)
        self.req_install.connect(self.installer.install)
        self.installer.finished.connect(self.installer_thread.quit)
        self.installer.finished.connect(self.installer.deleteLater)
        self.installer.finished.connect(self.installer_finished)
        self.installer_thread.finished.connect(self.installer_thread.deleteLater)
        self.installer_thread.finished.connect(self._thread_finished)
        self.installer.found_latest_version.connect(self._found_latest_version)
        self.installer.found_installed_version.connect(self._found_installed_version)

        labels = {**self.default_labels}
        if custom_labels:
            labels.update(custom_labels)

        self.page1 = self.addPage(Page1(self, labels))
        self.page2 = self.addPage(Page2(self, labels))

        self.installer_thread.start()

    @pyqtSlot()
    def _thread_started(self):
        logger.debug("thread started")

    def _thread_finished(self):
        logger.debug("thread finished")

    @pyqtSlot()
    def installer_finished(self):
        logger.debug("installer finished")

    def emit_search_request(self):
        self.req_search.emit(self.upgrade, self.request_kws)

    @pyqtSlot(str, bool)
    def _found_installed_version(self, ver: str, done: bool):
        self.old_ver_exists = bool(ver)
        if done:
            self.install_finished = True

    @pyqtSlot(tuple, bool)
    def _found_latest_version(self, ver: tuple, done: bool):
        self.version = ver
        if done:
            self.install_finished = True

    def emit_install_request(self):
        self.req_install.emit(self.version, self.old_ver_exists, self.request_kws)

    def nextId(self) -> int:
        return -1 if self.install_finished else super().nextId()


class Page1(QWizardPage):
    """Confirm"""

    def __init__(self, parent: InstallFFmpegWizard, labels: dict[str, str]):
        super().__init__(parent)

        # TODO - Add update button

        parent.installer.found_installed_version.connect(self._found_installed_version)
        parent.installer.found_latest_version.connect(self._found_latest_version)
        self.complete = False

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.curr_ver_label = label = QLabel(self)
        label.setText(labels["search_current"])
        label.setWordWrap(True)
        layout.addWidget(label)

        self.latest_ver_label = QLabel(self)
        self.latest_ver_label.setTextFormat(Qt.TextFormat.RichText)
        self.latest_ver_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextBrowserInteraction
        )
        self.latest_ver_label.setOpenExternalLinks(True)
        layout.addWidget(self.latest_ver_label)

        self.disclaimer_label = QLabel(self)
        self.disclaimer_label.setTextFormat(Qt.TextFormat.RichText)
        self.disclaimer_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextBrowserInteraction
        )
        self.disclaimer_label.setOpenExternalLinks(True)
        self.disclaimer_label.setText(labels["press_next"])
        self.disclaimer_label.setVisible(False)
        layout.addWidget(self.disclaimer_label)

        self.labels = {
            k: v
            for k, v in labels.items()
            if k
            in (
                "current_ver",
                "not_found",
                "exists",
                "search_latest",
                "latest_ver",
                "latest_installed",
            )
        }

    def isComplete(self) -> bool:
        return self.complete

    @pyqtSlot(str, bool)
    def _found_installed_version(self, ver, done):
        logger.debug("executing _found_installed_version")
        self.complete = done
        self.curr_ver_label.setText(
            self.labels["current_ver"].format(ver) if ver else self.labels["not_found"]
        )
        if done:
            self.latest_ver_label.setText(self.labels["exists"])
            self.setFinalPage(True)
            self.completeChanged.emit()
        else:
            self.latest_ver_label.setText(self.labels["search_latest"])

    @pyqtSlot(tuple, bool)
    def _found_latest_version(self, ver, done):
        self.complete = True
        self.latest_ver_label.setText(self.labels["latest_ver"].format(ver[0]))
        if done:
            self.disclaimer_label.setText(self.labels["latest_installed"])
            self.setFinalPage(True)

        self.disclaimer_label.setVisible(True)
        self.completeChanged.emit()

    @pyqtSlot(str)
    def _server_err(self, err: str):
        logger.critical(err)
        # TODO - display on the wizard ui

    def initializePage(self):
        wiz: InstallFFmpegWizard = self.wizard()
        wiz.emit_search_request()


class Page2(QWizardPage):
    def __init__(self, parent: InstallFFmpegWizard, labels: dict[str, str]):
        super().__init__(parent)

        self._is_installed = False

        parent.installer.download_maximum.connect(self._bar1_set_maximum)
        parent.installer.install_maximum.connect(self._bar2_set_maximum)
        parent.installer.download_progress.connect(self._bar1_value_changed)
        parent.installer.install_progress.connect(self._bar2_value_changed)
        parent.installer.installed.connect(self._installed)

        label1 = QLabel(self)
        label1.setText(labels["dl_progress"])
        self.bar1 = QProgressBar(self)
        label2 = QLabel(self)
        label2.setText(labels["ins_progress"])
        self.bar2 = QProgressBar(self)
        label3 = QLabel(self)
        label3.setText(labels["ins_folder"])
        label4 = QLineEdit(self)
        label4.setText(ffdl.ffmpeg_path())
        label4.setReadOnly(True)
        label5 = QLabel(self)
        label5.setText(labels["ins_success"])
        label5.setVisible(False)
        self.complete_label = label5
        layout = QVBoxLayout()
        layout.addWidget(label1)
        layout.addWidget(self.bar1)
        layout.addWidget(label2)
        layout.addWidget(self.bar2)
        layout.addWidget(label3)
        layout.addWidget(label4)
        layout.addWidget(label5)
        self.setLayout(layout)

    def initializePage(self):
        self.wizard().emit_install_request()

    @pyqtSlot(int)
    def _bar1_set_maximum(self, max: int):
        self.bar1.setMaximum(max)

    @pyqtSlot(int)
    def _bar2_set_maximum(self, max: int):
        self.bar2.setMaximum(max)

    @pyqtSlot(int)
    def _bar1_value_changed(self, value: int):
        self.bar1.setValue(value)

    @pyqtSlot(int)
    def _bar2_value_changed(self, value: int):
        self.bar2.setValue(value)

    @pyqtSlot()
    def _installed(self):
        self._is_installed = True
        self.completeChanged.emit()
        self.complete_label.setVisible(True)

    def isComplete(self) -> bool:
        return self._is_installed
