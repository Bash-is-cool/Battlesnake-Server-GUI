import os
import sys
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QStackedLayout
)

from layoutColorWidget import Color

from gui_utils import *

init_windows_appid("layouts")
icon_path = get_resource_path("resources/logo.ico")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        main = QWidget()

        # QVBoxLayout
        # layout = QVBoxLayout()
        # layout.addWidget(Color('red'))
        # layout.addWidget(Color('green'))
        # layout.addWidget(Color('blue'))
        # main.setLayout(layout)

        # QHBoxLayout
        # layout = QHBoxLayout()
        # layout.addWidget(Color('red'))
        # layout.addWidget(Color('green'))
        # layout.addWidget(Color('blue'))
        # main.setLayout(layout)

        # Nesting Layouts
        # mainLayout = QHBoxLayout()

        # leftLayout = QVBoxLayout()
        # leftLayout.addWidget(Color('red'))
        # leftLayout.addWidget(Color('green'))
        # leftLayout.addWidget(Color('blue'))

        # rightLayout = QVBoxLayout()
        # rightLayout.addWidget(Color('cyan'))
        # rightLayout.addWidget(Color('magenta'))
        # rightLayout.addWidget(Color('yellow'))

        # mainLayout.addLayout(leftLayout)
        # mainLayout.addLayout(rightLayout)

        # mainLayout.setContentsMargins(0, 0, 0, 0)
        # mainLayout.setSpacing(0)

        # main.setLayout(mainLayout)

        # QGridLayout
        # layout = QGridLayout()
        # layout.addWidget(Color('red'), 0, 0)
        # layout.addWidget(Color('green'), 1, 0)
        # layout.addWidget(Color('blue'), 1, 1)
        # layout.addWidget(Color('purple'), 2, 1)

        # main.setLayout(layout)

        # QStackedLayout
        stack = QStackedLayout()
        stack.addWidget(Color('red'))
        stack.addWidget(Color('green'))
        stack.addWidget(Color('blue'))

        stack.setCurrentIndex(1)

        main.setLayout(stack)

        self.setCentralWidget(main)

app = QApplication(sys.argv)

window = MainWindow()
window.setWindowTitle("Layouts")
window.setWindowIcon(QIcon(icon_path))
window.show()

app.exec()