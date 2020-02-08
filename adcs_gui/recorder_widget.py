import os
import sys
import time
from PySide2.QtWidgets import QWidget, QFileDialog, QMessageBox
from PySide2.QtCore import Qt, Signal, Slot, QFile
from PySide2.QtUiTools import QUiLoader
from PySide2.QtGui import QIntValidator

class RecorderWidget(QWidget):
    recordingStarted = Signal()

    def __init__(self, broadcaster, parent=None):
        super(RecorderWidget, self).__init__(parent)

        base_dir = os.path.dirname(os.path.realpath(__file__))
        form_dir = os.path.join(base_dir, 'forms', 'recorder_widget.ui')
        file = QFile(form_dir)
        file.open(QFile.ReadOnly)
        loader = QUiLoader()
        self.widget = loader.load(file, self)
        file.close()

        self.setMinimumSize(300, 220)
        self.setMaximumSize(16777215, 220)
        
        self.broadcaster = broadcaster

        self.widget.pbRecord.clicked.connect(self.onRecordClicked)
        self.widget.pbSaveToFile.clicked.connect(self.onSaveToFileClicked)
        self.broadcaster.recordingStopped.connect(self.enableRecordButton)
        self.broadcaster.recordingProgress.connect(self.updateRecordProgress)

    def resizeEvent(self, event):
        self.widget.resize(event.size())

    @Slot()
    def onRecordClicked(self):
        samples = self.widget.sbSamples.value()
        timeout = self.widget.sbTimeout.value() * 1000
        if self.broadcaster.startRecording(samples, timeout):
            self.widget.pbRecord.setEnabled(False)
            self.widget.pbRecord.setText('Recording...')
            self.recordingStarted.emit()
        else:
            QMessageBox.critical(self, 'Error', 'No object selected for tracking!', QMessageBox.Ok)

    @Slot()
    def onSaveToFileClicked(self):
        base_dir = sys.path[0]
        out_path = os.path.join(base_dir, 'out')
        if not os.path.exists(out_path):
            os.mkdir(out_path)
        fileName = os.path.join(out_path, 'out.csv')
        fileName, _ = QFileDialog.getSaveFileName(self, 'Save data', fileName, 'csv (*.csv)')
        self.saveToFile(fileName)

    def saveToFile(self, fileName):
        if fileName != '':
            self.broadcaster.saveToFile(fileName)
            self.widget.pbSaveToFile.setEnabled(False)

    @Slot()
    def enableRecordButton(self):
        self.widget.pbRecord.setEnabled(True)
        self.widget.pbRecord.setText('Record')
        self.widget.pbSaveToFile.setEnabled(True)

    @Slot()
    def updateRecordProgress(self, samples, max_samples):
        self.widget.prProgress.setValue(samples)
        self.widget.prProgress.setMaximum(max_samples)

    def setSamples(self, samples):
        self.widget.sbSamples.setValue(samples)

    def setTimeout(self, timeout):
        self.widget.sbTimeout.setValue(timeout)
