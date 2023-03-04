import sys
from PySide6 import QtGui
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout

class SetupToolApp(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        
        self.setWindowTitle("PID_Py : SetupTool")
        self.setFixedSize(1000, 600)

        # ===== Real-time graph ====
        

        # ===== Central widget =====
        centralWidget = QWidget()
        centralLayout = QVBoxLayout(centralWidget)

        self.setCentralWidget(centralWidget)

if __name__=="__main__":
    app = QApplication(sys.argv)

    setupToolApp = SetupToolApp()
    setupToolApp.show()

    app.exec()