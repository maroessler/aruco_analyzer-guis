#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import os
import sys
import time
import math
import numpy as np
from yaml import load
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QApplication
from PySide2.QtCore import Qt, Signal, Slot, QTimer, QObject, QFile, QTextStream, QSaveFile, QDir

from aruco_analyzer import ARMarkerDetector, OpenCVImageMiner

from adcs_gui.image_view_widget import ImageViewWidget
from adcs_gui.tracker_widget import TrackerWidget
from adcs_gui.recorder_widget import RecorderWidget

from adcs_gui.acs_control_widget import ACSControlWidget
from adcs_gui.automated_test_widget import AutomatedTestWidget

class Form(QObject):
 
    def __init__(self, parent=None):
        super(Form, self).__init__(parent)

        base_dir = os.path.dirname(os.path.realpath(__file__))
        ui_dir = os.path.join(base_dir, 'adcs_gui', 'forms', 'main_window.ui')
        ui_file = QFile(ui_dir)
        ui_file.open(QFile.ReadOnly)
        loader = QUiLoader()
        self.window = loader.load(ui_file)
        ui_file.close()

        self.image = [None]
        config_dir = os.path.join(base_dir, 'config', 'config.yaml')
        self.aruco_detector = ARMarkerDetector(load(open(config_dir), Loader=Loader))
        self.aruco_detector.set_image_miner(OpenCVImageMiner)
        self.aruco_detector.launch_detection_workers()
        self.broadcaster = Broadcaster(self)
        self.aruco_detector.launch_analyzer(self.broadcaster)

        #ImageViewWidget
        ivw = ImageViewWidget(self.image, self.window)
        self.window.centralwidget.layout().addWidget(ivw, 0, 0, 1, 2)

        # TrackerWidget
        tw = TrackerWidget(self.window)
        self.window.centralwidget.layout().addWidget(tw, 1, 0, Qt.AlignTop)

        # RecorderWidget
        rw = RecorderWidget(self.broadcaster, self.window)
        self.window.centralwidget.layout().addWidget(rw, 1, 1, Qt.AlignTop)


        # acsw = ACSControlWidget(self.window)
        # self.window.centralwidget.layout().addWidget(acsw, 2, 0, Qt.AlignTop)

        # atw = AutomatedTestWidget(self.broadcaster, acsw, rw, self.window)
        # self.window.centralwidget.layout().addWidget(atw, 2, 1, Qt.AlignTop)

        self.broadcaster.displayImage.connect(ivw.displayImage)

        self.broadcaster.updateX.connect(tw.widget.leX.setText)
        self.broadcaster.updateY.connect(tw.widget.leY.setText)
        self.broadcaster.updateZ.connect(tw.widget.leZ.setText)

        self.broadcaster.updateYaw.connect(tw.widget.leYaw.setText)
        self.broadcaster.updatePitch.connect(tw.widget.lePitch.setText)
        self.broadcaster.updateRoll.connect(tw.widget.leRoll.setText)
        self.broadcaster.updateDistance.connect(tw.widget.leDistance.setText)

        self.broadcaster.updateAge.connect(tw.set_age)
        self.broadcaster.updateReferenceAge.connect(tw.set_reference_age)
        self.broadcaster.updateRate.connect(tw.set_rate)
        self.broadcaster.updateReferenceRate.connect(tw.set_reference_rate)

        tw.widget.cbTrackedObject.currentIndexChanged[str].connect(self.broadcaster.set_desired_object)
        self.broadcaster.addTrackedObject.connect(tw.add_tracked_object)
        tw.widget.cbReferenceObject.currentIndexChanged[str].connect(self.broadcaster.set_reference_object)

        self.broadcaster.timer.timeout.connect(self.recordingTimedOut)

    def show(self):
        self.window.show()

    def recordingTimedOut(self):
        self.window.statusbar.showMessage('Recording timed out', 3000)

from pyquaternion import Quaternion
from aruco_analyzer import SingleOutput

class Broadcaster(QObject):

    updateX = Signal(str)
    updateY = Signal(str)
    updateZ = Signal(str)
    updateYaw = Signal(str)
    updatePitch = Signal(str)
    updateRoll = Signal(str)
    updateDistance = Signal(str)
    updateAge = Signal(float)
    updateReferenceAge = Signal(float)
    updateRate = Signal(float)
    updateReferenceRate = Signal(float)
    displayImage = Signal()

    addTrackedObject = Signal(str)
    desiredObject = None
    referenceObject = 'Camera'
    detectedObjects = {}

    counter_desired = 0
    start_desired = None
    counter_ref = 0
    start_ref = None
    rate_window = 2

    recordingStopped = Signal()
    stopTimer = Signal()
    recordingProgress = Signal(int, int)
    timer = None
    record = False
    sample_counter = 0
    max_samples = 500
    record_timeout = 5000
    recorded_samples = []

    def __init__(self, parent):
        super(Broadcaster, self).__init__()
        self.parent = parent

        self.logger = logging.getLogger('aruco_analyzer.gui.broadcaster')

        self.timer = QTimer(self)
        self.timer.setInterval(self.record_timeout)
        self.timer.timeout.connect(self.stopRecording)
        self.stopTimer.connect(self.timer.stop)

    @property
    def tracked_object(self):
        return self.desiredObject

    def broadcast(self, target):
        id = target.get_unique_ar_id_string()

        if id not in self.detectedObjects:
            self.addTrackedObject.emit(id)
            
        self.detectedObjects[id] = target

        if id == self.referenceObject:
            self.counter_ref += 1

            if time.time() - self.start_ref  > self.rate_window:
                self.updateReferenceRate.emit(self.counter_ref / (time.time() - self.start_ref))
                self.counter_ref = 0
                self.start_ref = time.time()

        if id == self.desiredObject:
            self.counter_desired += 1

            if time.time() - self.start_desired  > self.rate_window:
                self.updateRate.emit(self.counter_desired / (time.time() - self.start_desired))
                self.counter_desired = 0
                self.start_desired = time.time()
            
            target = self.calculate_transformation(self.referenceObject, self.desiredObject)
            self.emit_target(target)

            if self.record is True:
                self.sample_counter += 1
                self.recorded_samples.append(target)
                self.recordingProgress.emit(self.sample_counter, self.max_samples)
                if self.sample_counter >= self.max_samples:
                    self.stopTimer.emit()
                    self.stopRecording()     
        else:
            pass

    def emit_target(self, target):
        self.parent.image[0] = target.camera_image.image
        pos = target.position * 100
        ori = list(map(math.degrees, target.euler))
        dist = np.linalg.norm(pos)

        self.updateX.emit('{: 5.3f}cm'.format(pos[0]))
        self.updateY.emit('{: 5.3f}cm'.format(pos[1]))
        self.updateZ.emit('{: 5.3f}cm'.format(pos[2]))
        self.updateRoll.emit('{: 5.3f}°'.format(ori[0]))
        self.updatePitch.emit('{: 5.3f}°'.format(ori[1]))
        self.updateYaw.emit('{: 5.3f}°'.format(ori[2]))
        self.updateDistance.emit('{: 5.3f}cm'.format(dist))
        self.updateAge.emit(time.time() - target.timestamp)
        if self.referenceObject == 'Camera':
            self.updateReferenceAge.emit(-1)
            self.updateReferenceRate.emit(-1)
        else:
            self.updateReferenceAge.emit(time.time() - self.detectedObjects[self.referenceObject].timestamp)

        self.displayImage.emit()

    @Slot()
    def set_desired_object(self, sample_id):
        self.counter_desired = 0
        self.start_desired = time.time()
        if sample_id == '':
            self.desiredObject = None
        else:
            self.desiredObject = sample_id
            target = self.calculate_transformation(self.referenceObject, self.desiredObject)
            self.emit_target(target)    

    @Slot()
    def set_reference_object(self, reference_id):
        self.counter_ref = 0
        self.start_ref = time.time()
        self.referenceObject = reference_id
    
    def calculate_transformation(self, reference_id, relative_id):
        if reference_id == 'Camera':
            return self.detectedObjects[relative_id]

        reference = self.detectedObjects[reference_id]
        relative = self.detectedObjects[relative_id]

        timestamp = relative.timestamp

        q_rel = Quaternion(relative.quaternion).normalised
        q_ref = Quaternion(reference.quaternion).normalised
        q_rel_ref = q_rel.conjugate*q_ref

        relative_position = relative.position - reference.position
        transformed_position = self.transform(relative_position, q_ref.inverse)

        transformed = SingleOutput()
        transformed.camera_image = relative.camera_image
        transformed.ar_id = relative.ar_id
        transformed.quaternion = q_rel_ref.elements
        transformed.position = transformed_position
        transformed.timestamp = timestamp
        transformed.marker_type = relative.marker_type

        return transformed

    def transform(self, position, q):
        position_ = np.zeros((4))
        position_[1:] = position
        position = q * position_ * q.inverse

        return position.elements[1:]

    def startRecording(self, samples, record_timeout):
        if self.desiredObject is not None:
            self.max_samples = samples
            self.record_timeout = record_timeout
            self.timer.setInterval(self.record_timeout)
            self.record = True
            del self.recorded_samples[:]
            self.sample_counter = 0
            if self.record_timeout != 0:
                self.timer.start()
            return True
        else:
            return False

    @Slot()
    def stopRecording(self):
        self.logger.info('{}/{} samples recorded'.format(self.sample_counter, self.max_samples))
        self.record = False
        self.recordingStopped.emit()
        self.stopTimer.emit()

    def saveToFile(self, fileName):
        # ensure that path exists
        dir_path = os.path.dirname(os.path.realpath(fileName))
        dir = QDir('/')
        dir.mkpath(dir_path)
        file = QSaveFile(fileName)
        if file.open(QFile.WriteOnly):
            out = QTextStream(file)
            for sample in self.recorded_samples:
                out << sample.toCSV() << '\n'
            file.commit()
            del self.recorded_samples[:]
            self.recordingProgress.emit(0, self.max_samples)
        else:
            self.logger.error('Failed to open file')
            self.logger.error(file.error())

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setApplicationName('ADCS Evaluation Tool')
    form = Form()
    form.show()
    sys.exit(app.exec_())
