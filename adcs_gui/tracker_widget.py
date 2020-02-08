import os
import sys
import time
from PySide2.QtWidgets import QWidget
from PySide2.QtCore import Qt, Slot, QFile
from PySide2.QtUiTools import QUiLoader

class TrackerWidget(QWidget):

    def __init__(self, parent=None):
        super(TrackerWidget, self).__init__(parent)

        base_dir = os.path.dirname(os.path.realpath(__file__))
        ui_dir = os.path.join(base_dir, 'forms', 'tracker_widget.ui')
        file = QFile(ui_dir)
        file.open(QFile.ReadOnly)
        loader = QUiLoader()
        self.widget = loader.load(file, self)
        file.close()

        self.setMinimumSize(460, 220)
        self.setMaximumSize(16777215, 220)

        self.widget.cbTrackedObject.addItem('')
        self.widget.cbReferenceObject.addItem('Camera')

        self.widget.cbTrackedObject.currentIndexChanged.connect(self.reset_labels)
        self.widget.cbReferenceObject.currentIndexChanged.connect(self.reset_reference_labels)

    @Slot()
    def reset_labels(self):
        self.widget.leAge.setText('')
        self.widget.leRate.setText('')

    @Slot()
    def reset_reference_labels(self):
        self.widget.leReferenceAge.setText('')
        self.widget.leReferenceRate.setText('')

    @Slot()
    def set_rate(self, rate):
        self.widget.leRate.setText('{: 5.3f}Hz'.format(rate))

    @Slot()
    def set_reference_rate(self, rate):
        if rate == -1:
            self.widget.leReferenceRate.setEnabled(False)
            self.widget.leReferenceRate.setText('')
        else:
            self.widget.leReferenceRate.setEnabled(True)
            self.widget.leReferenceRate.setText('{: 5.3f}Hz'.format(rate))

    @Slot()
    def set_age(self, age):
        self.widget.leAge.setText('{: 5.3f}s'.format(age))
        if age > 1:
            self.widget.leAge.setStyleSheet('background: red')
        elif age > 0.5:
            self.widget.leAge.setStyleSheet('background: yellow')
        else:
            self.widget.leAge.setStyleSheet('background: white')

    @Slot()
    def set_reference_age(self, age):
        if age == -1:
            self.widget.leReferenceAge.setEnabled(False)
            self.widget.leReferenceAge.setText('')
        else:
            self.widget.leReferenceAge.setEnabled(True)
            self.widget.leReferenceAge.setText('{: 5.3f}s'.format(age))
            if age > 1:
                self.widget.leReferenceAge.setStyleSheet('background: red')
            elif age > 0.5:
                self.widget.leReferenceAge.setStyleSheet('background: yellow')
            else:
                self.widget.leReferenceAge.setStyleSheet('background: white')

    @Slot()
    def add_tracked_object(self, trackedObject):
        self.widget.cbTrackedObject.addItem(trackedObject)
        self.widget.cbTrackedObject.model().sort(0)
        self.widget.cbReferenceObject.addItem(trackedObject)
        self.widget.cbReferenceObject.model().sort(0)

    def resizeEvent(self, event):
        self.widget.resize(event.size())
