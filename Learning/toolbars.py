import os, sys
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("My App")

        tools = QToolBar("Main Toolbar")

        label = QLabel("Hello")
        label.setAlignment(Qt.AlignCenter)

        self.setCentralWidget(label)

        buttonAction = QAction("Click", self)
        buttonAction.setStatusTip("This is a button!")
        buttonAction.triggered.connect(self.buttonClicked)
        
        tools.addAction(buttonAction)

        self.addToolBar(tools)
    
    def buttonClicked(self, s):
        print("Button clicked!", s)
app = QApplication(sys.argv)

window = MainWindow()
window.show()

app.exec()