import os
from PySide2.QtWidgets import QWidget, QSizePolicy
from PySide2.QtCore import Qt, Slot, QFile
from PySide2.QtUiTools import QUiLoader

from .image_view_frame import ImageViewFrame

class ImageViewWidget(QWidget):

    def __init__(self, image, parent=None):
        super(ImageViewWidget, self).__init__(parent)

        base_dir = os.path.dirname(os.path.realpath(__file__))
        form_dir = os.path.join(base_dir, 'forms', 'image_view_widget.ui')
        file = QFile(form_dir)
        file.open(QFile.ReadOnly)
        loader = QUiLoader()
        self.widget = loader.load(file, self)
        file.close()

        self.ivf = ImageViewFrame(image, self)
        self.widget.layout().addWidget(self.ivf)

        self.image = image

        self.setMinimumSize(640, 360),
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    @Slot()
    def displayImage(self):
        self.ivf.displayImage()

    def resizeEvent(self, event):
        self.widget.resize(event.size())
