import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import *

from gui_utils import *

init_windows_appid("dialogs")

icon_path = get_resource_path("resources/logo.ico")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        button = QPushButton("Press me for a QDialog!")
        button.clicked.connect(self.button_dialog)

        button2 = QPushButton("Press me for a QMessageBox!")
        button2.clicked.connect(self.button_message)

        layout = QHBoxLayout()
        layout.addWidget(button)
        layout.addWidget(button2)

        main = QWidget()
        main.setLayout(layout)

        self.setCentralWidget(main)

    def button_dialog(self):
        dlg = CustomDialog(self)
        if dlg.exec():
            print("Success!")
        else:
            print("Cancel!")

    def button_message(self):
        msg = QMessageBox()
        msg.setWindowTitle("Message")
        msg.setWindowIcon(QIcon(icon_path))
        msg.setText("This is a simple message!")
        msg.setIcon(QMessageBox.Question)
        button = msg.exec()

        if button == QMessageBox.Ok:
            print("Ok!")

class CustomDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Dialogs!")
        self.setWindowIcon(QIcon(icon_path))

        QBtn = (
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )

        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        layout = QVBoxLayout()
        message = QLabel("Something happened, is that OK?")
        layout.addWidget(message)
        layout.addWidget(self.buttonBox)
        self.setLayout(layout)

app = QApplication(sys.argv)

window = MainWindow()
window.setWindowTitle("Dialogs")
window.setWindowIcon(QIcon(icon_path))
window.show()

app.exec()