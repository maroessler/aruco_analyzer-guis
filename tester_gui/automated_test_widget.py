import os
import sys
import time
import yaml
from PySide2.QtWidgets import QWidget, QFileDialog
from PySide2.QtCore import Signal, Slot, QFile, QSaveFile, QTextStream, QObject, QThread, QWaitCondition, QMutex
from PySide2.QtUiTools import QUiLoader


class AutomatedTestWidget(QWidget):
    config = None


    def __init__(self, acs_control_widget, aruco_tester_widget, parent=None):
        QWidget.__init__(self, parent)

        base_dir = os.path.dirname(os.path.realpath(__file__))
        fileName = os.path.join(base_dir, 'forms', 'automated_test_widget.ui')
        file = QFile(fileName)
        file.open(QFile.ReadOnly)
        loader = QUiLoader()
        self.widget = loader.load(file, self)
        file.close()

        self.widget.pbLoadConfiguration.clicked.connect(self.onLoadConfigurationClicked)
        self.widget.pbStart.clicked.connect(self.onStartClicked)

        self.acs_control_widget = acs_control_widget
        self.aruco_tester_widget = aruco_tester_widget

    @Slot()
    def onLoadConfigurationClicked(self):
        base_dir = os.path.dirname(os.path.realpath(__file__))
        fileName, _ = QFileDialog.getOpenFileName(self, "Open File", base_dir, "yaml (*.yaml)")
        try:
            file = open(fileName)
            self.config = yaml.load(file)
            self.widget.pbStart.setEnabled(True)
            file.close()
            print(self.config)
        except IOError as ioe:
            print(ioe)

    @Slot()
    def onStartClicked(self):
        self.widget.pbStart.setEnabled(False)
        self.thread = TestThread(self.config, self.aruco_tester_widget, self.acs_control_widget.controller, self)
        self.aruco_tester_widget.broadcaster.recordingStopped.connect(self.thread.wake)
        self.thread.start()

class TestThread(QThread):
    startRecording = Signal()

    def __init__(self, config, aruco_tester_widget, acs_control, parent=None):
        QThread.__init__(self, parent)
        self.config = config
        self.aruco_tester_widget = aruco_tester_widget
        self.image_miner = aruco_tester_widget.image_miner
        self.acs_control = acs_control

        self.startRecording.connect(self.aruco_tester_widget.onRecordClicked)

        self.recordingStopped = QWaitCondition()
        self.mutex = QMutex()

    @Slot()
    def wake(self):
        self.recordingStopped.wakeAll()
        pass

    def run(self):
        print('starting...')
        base_dir = os.path.dirname(os.path.realpath(__file__))
        config = self.config['config']
        angles = self.config['angles']
        j = 0
            
        self.image_miner.set_video_capture_property('CAP_PROP_BRIGHTNESS', 50.5/100.)
        self.image_miner.set_video_capture_property('CAP_PROP_CONTRAST', 50.5/100.)
        self.image_miner.set_video_capture_property('CAP_PROP_SATURATION', 50.5/100.)

        prop = 'CAP_PROP_BRIGHTNESS'

        print(prop)
        start = config[prop]['start']
        end = config[prop]['end']
        step = config[prop]['step']
        for i in range(start, end+1, step):
            print(i)
            self.image_miner.set_video_capture_property(prop, i/100.)
            series_dir = os.path.join(base_dir, str(prop), str(i), str(self.aruco_tester_widget.use_board))
            j += 1
            
            for angle in angles:
                fileName = os.path.join(series_dir, str(angle))
                print(angle)
                self.acs_control.pa(angle)
                time.sleep(5)
                self.mutex.lock()
                self.startRecording.emit()
                print('wait for recording to stop')
                self.recordingStopped.wait(self.mutex)
                print('saving data to {}'.format(fileName))
                self.aruco_tester_widget.broadcaster.saveToFile(fileName)
                self.mutex.unlock()

            self.acs_control.pa(0)
            time.sleep(10)
