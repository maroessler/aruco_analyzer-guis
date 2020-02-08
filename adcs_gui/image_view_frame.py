from __future__ import division

import os
import sys
import time
from threading import Lock
from PySide2.QtWidgets import QFrame
from PySide2.QtCore import Qt, Slot, QFile
from PySide2.QtUiTools import QUiLoader
from PySide2.QtGui import QImage, QPixmap, QPainter

import cv2

class ImageViewFrame(QFrame):

    def __init__(self, image, parent=None):
        super(ImageViewFrame, self).__init__(parent)

        self.image = image
        self.qimage = None
        self.lock = Lock()

    @Slot()
    def displayImage(self):
        if self.lock.acquire(False):
            if self.image[0] is not None:
                image = self.image[0].copy()
                cv2.cvtColor(image, cv2.COLOR_BGR2RGB, image)
                height, width, _ = image.shape
                self.qimage = QImage(image, width, height, image.strides[0], QImage.Format_RGB888)
                self.resizeAspectRatio(self.contentsRect().size())
                
            self.lock.release()
            self.update()
            self.repaint()
        else:
            print('image_view_widget: acquiring lock failed')
        self.update()

    def resizeAspectRatio(self, size):
        try:
            width = self.qimage.size().width()
            height = self.qimage.size().height()
            ratio = height / width
            if self.contentsRect().size().height() / self.contentsRect().size().width() > ratio:
                event_width = size.width()
                self.resize(event_width, event_width*ratio)
            else:
                event_height = size.height()
                self.resize(event_height / ratio, event_height)
        except ZeroDivisionError as zde:
            pass

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawImage(self.contentsRect(), self.qimage)

    def resizeEvent(self, event):
        if self.qimage is not None:
            self.resizeAspectRatio(event.size())
