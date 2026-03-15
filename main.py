import sys
from PySide6.QtWidgets import QApplication, QPushButton, QMainWindow # type: ignore

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.button_checked = True

        self.setWindowTitle("Hello World!")

        self.button = QPushButton("Click Me!")

        self.button.setCheckable(True)
        self.button.clicked.connect(self.button_clicked)
        self.button.toggled.connect(self.button_toggled)

        self.setCentralWidget(self.button)

    def button_clicked(self):
        print("Clicked!")

    def button_toggled(self, checked):
        self.button_checked = checked
        print("Checked?", checked)

app = QApplication(sys.argv)

window = MainWindow()

window.show()

sys.exit(app.exec())