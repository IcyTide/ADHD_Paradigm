from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMainWindow, QStyleFactory, QVBoxLayout, QWidget, QTabWidget
import sys

from experiment_1 import Experiment1Widget
from experiment_2 import Experiment2Widget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Paradigm")

        icon = QIcon("assets/icon.ico")
        self.setWindowIcon(icon)
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
        self.tab_widget.addTab(self.experiment_1_widget, "Go-no_go")
        self.experiment_2_widget = Experiment2Widget()
        self.tab_widget.addTab(self.experiment_2_widget, "1_back-2_back")

        self.tab_widget.tabBar().tabBarClicked.connect(self.tab_selected)

        self.experiment_1_widget.prepare_practice_1()

    def tab_selected(self, index):
        if index == 0:
            self.experiment_2_widget.media_player.stop()
            self.experiment_1_widget.prepare_practice_1()
        elif index == 1:
            self.experiment_1_widget.media_player.stop()
            self.experiment_2_widget.prepare_practice_1()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create('Fusion'))
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
