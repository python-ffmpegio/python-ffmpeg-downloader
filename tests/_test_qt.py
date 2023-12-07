# if __name__ == "__main__":
import logging

logging.basicConfig(level=logging.DEBUG)

import sys
from PyQt6.QtWidgets import QApplication
from ffmpeg_downloader.qt.wizard import InstallFFmpegWizard

app = QApplication(sys.argv)
wizard = InstallFFmpegWizard()
wizard.show()
sys.exit(app.exec())
