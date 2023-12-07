import sys
from PyQt6.QtWidgets import QApplication
from ffmpeg_downloader.qt.wizard import InstallFFmpegWizard


def main():
    app = QApplication(sys.argv)
    wizard = InstallFFmpegWizard()
    wizard.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
