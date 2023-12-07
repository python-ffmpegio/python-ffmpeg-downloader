import typing
from PyQt6 import QtCore
from PyQt6.QtCore import QObject, QThread, pyqtSignal, pyqtSlot
import sys
from PyQt6.QtWidgets import QApplication, QWizard
from time import sleep

# Step 1: Create a worker class class Worker(QObject):
class Worker(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal(int)

    def run(self):
        """Long-running task."""
        for i in range(5):
            sleep(1)
            self.progress.emit(i + 1)
        self.finished.emit()


class Window(QWizard):
    def __init__(self):
        super().__init__()

        # Step 2: Create a QThread object
        self.worker_thread = QThread()
        # Step 3: Create a worker object
        self.worker = Worker()
        # Step 4: Move worker to the thread
        self.worker.moveToThread(self.worker_thread)
        # Step 5: Connect signals and slots
        self.worker_thread.started.connect(self.tstarted)
        self.worker_thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.worker_thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)
        self.worker.progress.connect(self.reportProgress)
        self.worker.finished.connect(self.finished)
        self.worker_thread.finished.connect(self.tfinished)
        # Step 6: Start the thread
        self.worker_thread.start()

    @pyqtSlot(int)
    def reportProgress(self, p: int):
        print(p)

    @pyqtSlot()
    def finished(self):
        print('work finished')

    @pyqtSlot()
    def tstarted(self):
        print('thread started')

    @pyqtSlot()
    def tfinished(self):
        print('thread finished')

app = QApplication(sys.argv)
wizard = Window()
# wizard.runLongTask()
wizard.show()
sys.exit(app.exec())
