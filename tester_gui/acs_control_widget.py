import os
import serial
from PySide2.QtWidgets import (QApplication, QLabel, QPushButton, QLineEdit, QWidget)
from PySide2.QtCore import QFile, Signal, Slot
from PySide2.QtUiTools import QUiLoader

class ACSControlWidget(QWidget):
    targetAngleSet = Signal(str)

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)

        base_dir = os.path.dirname(os.path.realpath(__file__))
        dir = os.path.join(base_dir, 'forms', 'acs_control_widget.ui')
        file = QFile(dir)
        file.open(QFile.ReadOnly)
        loader = QUiLoader()
        self.widget = loader.load(file, self)
        file.close()

        self.controller = ACSController()

        self.widget.pbOpen.clicked.connect(self.onOpenPortClicked)
        self.widget.pbMotorOn.clicked.connect(self.onMotorOnClicked)
        self.widget.pbMotorOff.clicked.connect(self.onMotorOffClicked)
        self.widget.pbStopMotor.clicked.connect(self.onMotorStopClicked)
        self.widget.pbPA.clicked.connect(self.onSetTargetAngleClicked)
        self.widget.pbSP.clicked.connect(self.onSetSpeedClicked)

        self.widget.leFeedback.setText('DISPLAY OF FEEDBACK INFO')
        self.widget.lePort.setText('/dev/ttyUSB0')

    @Slot()
    def onOpenPortClicked(self):
        self.controller.open_port(self.widget.lePort.text())
        self.feedback_test = 'Port is open\n'.encode('UTF-8')
        self.widget.leFeedback.setText(self.feedback_test)

    @Slot()
    def onMotorOnClicked(self):
        self.controller.motor_on()

    @Slot()
    def onMotorOffClicked(self):
        self.controller.motor_off()

    @Slot()
    def onMotorStopClicked(self):
        self.controller.stop_motor()

    @Slot()
    def onSetSpeedClicked(self):
        self.controller.sp(self.widget.leSpeed.text())

    @Slot()
    def onSetTargetAngleClicked(self):
        self.controller.pa(self.widget.leDegrees.text())
        self.targetAngleSet.emit(str(self.widget.leDegrees.text()))

class ACSController(object):
    def __init__(self):
        self.serial_interface=serial.Serial(port=None, baudrate=19200, \
            bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, \
            stopbits=serial.STOPBITS_ONE, timeout=None, xonxoff=False, \
            rtscts=True, write_timeout=None, \
            dsrdtr=True, inter_byte_timeout=None)

    def open_port(self, port):
        if self.serial_interface.is_open:
            self.serial_interface.close()
        self.serial_interface.port = port
        self.serial_interface.open()

    def send_encode_string(self, data):
        data=data+'\r\n'
        self.serial_interface.write(data.encode('UTF-8'))

    def read_decode_string(self):
        return self.serial_interface.readline().decode('UTF-8')

    def motor_on(self):
        self.send_encode_string('SH')

    def motor_off(self):
        self.send_encode_string('MO')

    def stop_motor(self):
        self.send_encode_string('ST')

    def sp(self, speed):
        number = int(speed)
        number = number*10000
        self.send_encode_string('SP'+str(number))

    def pa(self, degree):
        number = int(degree)
        number = number*10000
        self.send_encode_string('PA'+str(number))
        self.send_encode_string('BG')

    def not_moving_fix(self):
        self.send_encode_string('ST')
        self.send_encode_string('SH')
        self.send_encode_string('SP100000')