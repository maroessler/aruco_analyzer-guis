import os
import sys
import logging
import time
import yaml
from threading import Event
from PySide2.QtWidgets import QWidget, QFileDialog, QMessageBox
from PySide2.QtCore import Signal, Slot, QFile, QSaveFile, QTextStream, QObject, QThread, QWaitCondition, QMutex
from PySide2.QtUiTools import QUiLoader

class AutomatedTestWidget(QWidget):
    config = None
    thread = None
    logger = logging.getLogger('aruco_analyzer.gui.AutomatedTestWidget')

    def __init__(self, broadcaster, acs_control_widget, recorder_widget, parent=None):
        QWidget.__init__(self, parent)

        base_dir = os.path.dirname(os.path.realpath(__file__))
        fileName = os.path.join(base_dir, 'forms', 'automated_test_widget.ui')
        file = QFile(fileName)
        file.open(QFile.ReadOnly)
        loader = QUiLoader()
        self.widget = loader.load(file, self)
        file.close()

        self.setMinimumSize(300, 180)
        self.setMaximumSize(16777215, 180)

        self.widget.pbLoadConfiguration.clicked.connect(self.onLoadConfigurationClicked)
        self.widget.pbStart.clicked.connect(self.onStartClicked)

        self.broadcaster = broadcaster
        self.acs_control_widget = acs_control_widget
        self.recorder_widget = recorder_widget

    @Slot()
    def onLoadConfigurationClicked(self):
        base_dir = os.path.dirname(os.path.realpath(sys.argv[0]))
        conf_dir = os.path.join(base_dir, 'adcs_gui', 'config')
        fileName, _ = QFileDialog.getOpenFileName(self, "Open File", conf_dir, "yaml (*.yaml)")
        try:
            file = open(fileName)
            self.config = yaml.load(file)
            self.widget.pbStart.setEnabled(True)
            file.close()
            self.logger.info(self.config)
        except IOError as ioe:
            self.logger.error(ioe)

    @Slot()
    def onStartClicked(self):
        if self.broadcaster.tracked_object == '' or self.broadcaster.tracked_object is None:
            QMessageBox.critical(self, 'Error', 'No object selected for tracking!', QMessageBox.Ok)
            return
        self.widget.pbStart.setEnabled(False)
        self.widget.pbLoadConfiguration.setEnabled(False)
        self.thread = TestThread(self.config, self.acs_control_widget, self.recorder_widget, self)
        self.broadcaster.recordingStopped.connect(self.thread.wake)
        self.recorder_widget.recordingStarted.connect(self.thread.recordingStarted)
        self.thread.startRecording.connect(self.recorder_widget.onRecordClicked)
        self.thread.updateProgress.connect(self.widget.prbProgress.setValue)
        self.thread.testFinished.connect(self.enableLoadButton)
        self.thread.start()

    @Slot()
    def enableLoadButton(self):
        self.widget.pbLoadConfiguration.setEnabled(True)

    def resizeEvent(self, event):
        self.widget.resize(event.size())

class TestThread(QThread):
    startRecording = Signal()
    updateProgress = Signal(int)
    testFinished = Signal()
    logger = logging.getLogger('aruco_analyzer.gui.AutomatedTestWidget')

    def __init__(self, config, acs_control_widget, recorder_widget, parent=None):
        QThread.__init__(self, parent)
        self.config = config
        self.acs_control_widget = acs_control_widget
        self.recorder_widget = recorder_widget
        self.recordingStopped = Event()
        self.recordingStartedEvent = Event()

    @Slot()
    def wake(self):
        self.recordingStopped.set()

    @Slot()
    def recordingStarted(self):
        self.recordingStartedEvent.set()

    def run(self):
        self.logger.info('starting...')
        base_dir = os.path.dirname(os.path.realpath(sys.argv[0]))
        out_path = os.path.join(base_dir, 'out')
        series_dir = os.path.join(base_dir, '1')

        samples = self.config['samples']
        timeout = self.config['timeout']
        angles = self.config['angles']

        start = self.config['start']
        end = self.config['end']
        step = self.config['step']
        angles = range(start, end+step, step)

        self.recorder_widget.setSamples(samples)
        self.recorder_widget.setTimeout(timeout)

        self.acs_control_widget.onOpenPortClicked()

        for i, angle in enumerate(angles):
            self.logger.info('angle {}'.format(angle))

            fileName = os.path.join(series_dir, str(angle))
            self.acs_control_widget.setTargetAngle(angle)
            self.acs_control_widget.onSetTargetAngleClicked()
            time.sleep(1)
            self.startRecording.emit()
            if self.recordingStartedEvent.wait(1):
                self.recordingStopped.clear()
                self.logger.info('wait for recording to stop')
                self.recordingStopped.wait()
                self.recordingStartedEvent.clear()
                self.logger.info('saving data to {}'.format(fileName))
                self.recorder_widget.saveToFile(fileName)
            else:
                self.logger.info('timeout')
                self.testFinished.emit()
                return

            self.updateProgress.emit(99*(i+1)/len(angles))


        self.acs_control_widget.setTargetAngle(0)
        self.acs_control_widget.onSetTargetAngleClicked()
        time.sleep(10)
        self.logger.info('thread end')
        self.updateProgress.emit(100)
        self.testFinished.emit()