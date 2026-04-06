import sys

from PySide6.QtGui import *
from PySide6.QtWidgets import *

from gui_utils import *

init_windows_appid("battlesnake")
icon_path = get_resource_path("resources/logo.ico")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

app = QApplication(sys.argv)

window = MainWindow()
window.setWindowTitle("Battlesnake")
window.setWindowIcon(QIcon(icon_path))
window.show()

app.exec()