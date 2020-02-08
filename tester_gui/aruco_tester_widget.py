import os
import sys
import time
import threading
from PySide2.QtWidgets import QWidget, QFileDialog
from PySide2.QtCore import Signal, Slot, QFile, QSaveFile, QTextStream, QObject, QTimer, QDir
from PySide2.QtUiTools import QUiLoader
from yaml import load
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

import cv2

# boards = {
#     'board2': {'board_marker_size': 0.0485, 'board_x': 2, 'board_y': 2},
#     'board5': {'board_marker_size': 0.019, 'board_x': 5, 'board_y': 5},
#     'board7': {'board_marker_size': 0.013, 'board_x': 7, 'board_y': 7},
#     'board10': {'board_marker_size': 0.009, 'board_x': 10, 'board_y': 10},
#     'board15': {'board_marker_size': 0.0045, 'board_x': 15, 'board_y': 15},
# }

boards = {
    'board10_4': {'board_marker_size': 0.023, 'board_x': 4, 'board_y': 4, 'board_margin_size': 0.0017},
    'board10_6': {'board_marker_size': 0.0148, 'board_x': 6, 'board_y': 6, 'board_margin_size': 0.0017},
    'board10_8': {'board_marker_size': 0.0105, 'board_x': 8, 'board_y': 8, 'board_margin_size': 0.0017},
    'board10_10': {'board_marker_size': 0.0081, 'board_x': 10, 'board_y': 10, 'board_margin_size': 0.0017},
    'board5_2': {'board_marker_size': 0.0023, 'board_x': 2, 'board_y': 2, 'board_margin_size': 0.0017},
    'board5_4': {'board_marker_size': 0.00111, 'board_x': 4, 'board_y': 4, 'board_margin_size': 0.0017},
    'board5_6': {'board_marker_size': 0.00071, 'board_x': 6, 'board_y': 6, 'board_margin_size': 0.0017},
    'board5_8': {'board_marker_size': 0.0005, 'board_x': 8, 'board_y': 8, 'board_margin_size': 0.0017},
}

class ArUcoTesterWidget(QWidget):

    use_board = 'board10_4'

    def __init__(self, detector_module, image_miner_module, parent=None):
        QWidget.__init__(self, parent)

        base_dir = os.path.dirname(os.path.realpath(__file__))
        form_dir = os.path.join(base_dir, 'forms', 'aruco_tester_widget.ui')
        file = QFile(form_dir)
        file.open(QFile.ReadOnly)
        loader = QUiLoader()
        self.widget = loader.load(file, self)
        file.close()

        self.targetAngle = 0

        # connect signals
        self.widget.pbRecord.clicked.connect(self.onRecordClicked)
        self.widget.pbSaveToFile.clicked.connect(self.onSaveToFileClicked)
        
        board = boards[self.use_board]
        config_dir = os.path.join(base_dir, '..', 'config', 'config.yaml')
        self.aruco_detector = detector_module(load(open(config_dir), Loader=Loader))
        self.image_miner_module = image_miner_module
        self.aruco_detector.set_image_miner(self.image_miner_module)
        self.aruco_detector.launch_detection_workers()

        self.broadcaster = Broadcaster(self)
        self.aruco_detector.launch_analyzer(self.broadcaster)

        self.broadcaster.updateX.connect(self.widget.leX.setText)
        self.broadcaster.updateY.connect(self.widget.leY.setText)
        self.broadcaster.updateZ.connect(self.widget.leZ.setText)

        self.broadcaster.updateYaw.connect(self.widget.leYaw.setText)
        self.broadcaster.updatePitch.connect(self.widget.lePitch.setText)
        self.broadcaster.updateRoll.connect(self.widget.leRoll.setText)

        self.broadcaster.updateTimestamp.connect(self.widget.leTimestamp.setText)

        self.broadcaster.recordingStopped.connect(self.enableRecordButton)

    @Slot()
    def onRecordClicked(self):
        self.widget.pbRecord.setEnabled(False)
        self.widget.pbRecord.setText('Recording...')
        self.broadcaster.startRecording()

    @Slot()
    def onSaveToFileClicked(self):
        self.widget.pbSaveToFile.setEnabled(False)
        base_dir = os.path.dirname(os.path.realpath(__file__))
        fileName = os.path.join(base_dir, str(self.targetAngle))
        fileName, _ = QFileDialog.getSaveFileName(self, 'Save data', fileName)
        self.broadcaster.saveToFile(fileName)

    @Slot()
    def enableRecordButton(self):
        self.widget.pbRecord.setEnabled(True)
        self.widget.pbRecord.setText('Record')
        self.widget.pbSaveToFile.setEnabled(True)

    @Slot()
    def setTargetAngle(self, angle):
        self.targetAngle = angle

import math

class Broadcaster(QObject):

    updateX = Signal(str)
    updateY = Signal(str)
    updateZ = Signal(str)

    updateYaw = Signal(str)
    updatePitch = Signal(str)
    updateRoll = Signal(str)

    updateTimestamp = Signal(str)

    recordingStopped = Signal()
    stopTimer = Signal()

    sample_counter = 0
    max_samples = 100
    timeout = 5000

    desiredSample = 'C000'

    image = None

    def __init__(self, parent):
        super(Broadcaster, self).__init__()
        self.parent = parent
        self.record = False
        self.recordedSamples = list()
        self.timer = QTimer(self)
        self.timer.setInterval(self.timeout)
        self.timer.timeout.connect(self.stopRecording)
        self.stopTimer.connect(self.timer.stop)

        self.thread = threading.Thread(target=self.showImage, args=[])
        self.thread.daemon = True
        self.thread.start()


    def broadcast(self, target):
        if not target.get_unique_ar_id_string() == self.desiredSample:
            return
        pos = target.position
        ori = list(map(math.degrees, target.euler))
        # cv2.namedWindow('image', cv2.WINDOW_NORMAL)
        # cv2.resizeWindow('image', 1280, 720)
        # cv2.imshow('image', target.image)
        # cv2.waitKey(1)
        self.image = target.image

        self.updateX.emit('{: 5.3f}'.format(pos[0]))
        self.updateY.emit('{: 5.3f}'.format(pos[1]))
        self.updateZ.emit('{: 5.3f}'.format(pos[2]))
        self.updateYaw.emit('{: 5.3f}'.format(ori[0]))
        self.updatePitch.emit('{: 5.3f}'.format(ori[1]))
        self.updateRoll.emit('{: 5.3f}'.format(ori[2]))

        self.updateTimestamp.emit('{: 5.3f}'.format(time.time() - target.timestamp))
        if self.record is True:
            if self.sample_counter < self.max_samples:
                self.sample_counter += 1
                self.recordedSamples.append(target)
            else:
                self.stopTimer.emit()
                self.stopRecording()

    def startRecording(self):
        self.record = True
        self.recordedSamples = list()
        self.sample_counter = 0
        self.timer.start()

    @Slot()
    def stopRecording(self):
        print('{}/{} samples recorded'.format(self.sample_counter, self.max_samples))
        self.record = False
        self.recordingStopped.emit()

    def saveToFile(self, fileName):
        dir_path = os.path.dirname(os.path.realpath(fileName))
        dir = QDir('/')
        dir.mkpath(dir_path)
        file = QSaveFile(fileName)
        if file.open(QFile.WriteOnly):
            out = QTextStream(file)
            for sample in self.recordedSamples:
                out << sample.toCSV() << '\n'
            file.commit()
            self.recordedSamples = list()
        else:
            print('ERROR: failed to open file')
            print(file.error())

    def isRecording(self):
        return self.record

    def showImage(self):
        while True:
            if self.image is not None:
                cv2.imshow('image', self.image)
                self.image = None
            time.sleep(0.001)