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

        label = QLabel("Hello")
        label.setAlignment(Qt.AlignCenter)
        self.setCentralWidget(label)

        tools = QToolBar("Main Toolbar")
        tools.setIconSize(QSize(16, 16))

        self.addToolBar(tools)

        button_action = QAction(QIcon("../resources/bug.png"), "Click", self)
        button_action.setCheckable(True)
        button_action.setStatusTip("This is a button!")
        button_action.triggered.connect(self.buttonClicked)
        button_action.setShortcut(QKeySequence(Qt.CTRL | Qt.Key_P))
        tools.addAction(button_action)

        tools.addSeparator()

        button_action2 = QAction(QIcon("../resources/bug.png"), "Click", self)
        button_action2.setCheckable(True)
        button_action2.setStatusTip("This is a button2!")
        button_action2.triggered.connect(self.buttonClicked)
        tools.addAction(button_action2)

        tools.addWidget(QLabel("This is a label"))
        tools.addWidget(QCheckBox())

        menu = self.menuBar()

        file_menu = menu.addMenu("&File")
        file_menu.addAction(button_action)

        file_submenu = file_menu.addMenu("Submenu")
        file_submenu.addAction(button_action2)

        menu.addAction(button_action2)

        self.setStatusBar(QStatusBar(self))

    def buttonClicked(self, s):
        print("Button clicked!", s)

app = QApplication(sys.argv)

window = MainWindow()
window.setWindowTitle("Toolbars")
window.setWindowIcon(QIcon(icon_path))
window.show()

app.exec()