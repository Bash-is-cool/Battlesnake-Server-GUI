import os, sys
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *

from gui_utils import *

init_windows_appid("battlesnake.server.gui.v3")

icon_path = get_resource_path("resources/logo.ico")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.label = QLabel("Main Window")
        self.setCentralWidget(self.label)

        self.w = AnotherWindow()
        self.w.show()

        self.w2 = AnotherWindow()
        self.w2.show()

class AnotherWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Another Window")
        self.setWindowIcon(QIcon(icon_path))

        layout = QVBoxLayout()
        self.label = QLabel("Additional Window")
        layout.addWidget(self.label)
        self.setLayout(layout)



app = QApplication(sys.argv)

window = MainWindow()
window.setWindowTitle("Toolbars")
window.setWindowIcon(QIcon(icon_path))
window.show()

app.exec()