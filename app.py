from PySide6.QtWidgets import QApplication, QMainWindow, QStyleFactory, QMessageBox, QVBoxLayout, QWidget, QTabWidget
import sys

from experiment_1 import Experiment1Widget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Paradigm")

        # icon = QIcon("qt/assets/icon.ico")
        # self.setWindowIcon(icon)
        # self.message_box = QMessageBox()
        #
        # self.message_box.setWindowIcon(icon)

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.resize(960, 640)
        layout = QVBoxLayout(self.central_widget)

        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        layout.setStretchFactor(self.tab_widget, 1)

        self.experiment_1_widget = Experiment1Widget()
        self.tab_widget.addTab(self.experiment_1_widget, "Go-nogo")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create('Fusion'))
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
