import os
import sys

from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QApplication
from PySide2.QtCore import QFile, QObject, Qt

from tester_gui.aruco_tester_widget import ArUcoTesterWidget
from tester_gui.acs_control_widget import ACSControlWidget
from tester_gui.automated_test_widget import AutomatedTestWidget
from aruco_analyzer import ARMarkerDetector, OpenCVImageMiner

class Form(QObject):
 
    def __init__(self, parent=None):
        super(Form, self).__init__(parent)

        base_dir = os.path.dirname(os.path.realpath(__file__))
        ui_dir = os.path.join(base_dir, 'tester_gui', 'forms', 'main_window.ui')
        ui_file = QFile(ui_dir)
        ui_file.open(QFile.ReadOnly)
        loader = QUiLoader()
        self.window = loader.load(ui_file)
        ui_file.close()
  
        acsControlWidget = ACSControlWidget(self.window)
        self.window.gridLayout.addWidget(acsControlWidget)

        arucoTesterWidget = ArUcoTesterWidget(ARMarkerDetector, OpenCVImageMiner, self.window)
        self.window.gridLayout.addWidget(arucoTesterWidget)

        acsControlWidget.targetAngleSet.connect(arucoTesterWidget.setTargetAngle)

        automatedTestWidget = AutomatedTestWidget(acs_control_widget=acsControlWidget, aruco_tester_widget=arucoTesterWidget, parent=self.window)
        self.window.gridLayout.addWidget(automatedTestWidget)
        self.window.setWindowFlag(Qt.WindowStaysOnTopHint, True)

        self.window.show()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setApplicationName('ArUco Evaluation Tool')
    form = Form()
    sys.exit(app.exec_())
