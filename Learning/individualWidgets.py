import sys, os

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDial,
    QDoubleSpinBox,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # QLabel
        # self.label = QLabel()
        # pixmap = QPixmap("duffy.png")
        # print(pixmap.isNull())
        # self.label.setPixmap(pixmap)
    
        # #self.setWindowTitle("My App")
        # self.setCentralWidget(self.label)

        # QCheckBox
        # self.checkbox = QCheckBox("This is a checkbox!")
        # self.checkbox.setChecked(True)
        # # self.checkbox.setTristate(True)
        # self.checkbox.stateChanged.connect(self.show_state)
        # self.setCentralWidget(self.checkbox)

        # QComboBox
        # self.check_box = QComboBox()
        # self.check_box.addItems(["One", "Two", "Three"])
        # self.setCentralWidget(self.check_box)

        # QListWidget
        # self.list = QListWidget()
        # self.list.addItems(["One", "Two", "Three"])
        # self.setCentralWidget(self.list)

        # QLineEdit
        # self.line_edit = QLineEdit()
        # self.line_edit.setPlaceholderText("Type something here...")
        # self.line_edit.setMaxLength(10)
        # self.setCentralWidget(self.line_edit)

        # QSpinBox and QDoubleSpinBox
        # self.spinbox = QSpinBox()
        # self.spinbox.setRange(-10, 10)
        # self.spinbox.setPrefix("$")
        # self.spinbox.setSuffix("c")

        # self.double_spinbox = QDoubleSpinBox()
        # self.double_spinbox.setRange(-10, 10)
        # self.double_spinbox.setPrefix("$")
        # self.double_spinbox.setSuffix("c")

        # layout = QVBoxLayout()
        # layout.addWidget(self.spinbox)
        # layout.addWidget(self.double_spinbox)

        # container = QWidget()
        # container.setLayout(layout)

        # self.setCentralWidget(container)

        # QSlider
        # self.slider = QSlider(Qt.Orientation.Horizontal) # Could also be Vertical
        # self.slider.setRange(0, 100)
        # self.slider.setValue(50)
        # self.setCentralWidget(self.slider)

        # QDial
        # self.dial = QDial()
        # self.dial.setRange(0, 100)
        # self.dial.setValue(50)
        # self.setCentralWidget(self.dial)

        self.image = QLabel()
        self.image.setPixmap(QPixmap("resources/logo.png"))
        self.setCentralWidget(self.image)

    def show_state(self, state):
        print(state == Qt.CheckState.Checked.value)
        print(state)

app = QApplication(sys.argv)
app.setWindowIcon(QIcon("resources/logo.png"))

window = MainWindow()
window.show()
app.exec()