import os
import random
from enum import Enum
import time

from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QTableWidget, QAbstractItemView, \
    QTableWidgetItem, QHeaderView, QHBoxLayout
from PySide6.QtGui import QPixmap, Qt
from PySide6.QtCore import QTimer

READY_TIME = 3000
SHOW_TIME = 800
PAUSE_TIME = 200

MAX_TURN = 4

BOARD_SIZE = 2


RESULT_TEMPLATE = """
本次共计得分：{}
选择正确{}个，正确率：{}%
选择错误{}个，错误率：{}%
漏选{}个，漏选率：{}%
""".strip()
RESULT_HEADERS = ["Turn", "Elapse", "Result"]


class Step(Enum):
    go = 0
    no_go = 1


class Summary:
    def __init__(self):
        self.records = []
        self.start_time = 0

        self.correct = 0
        self.wrong = 0

    @property
    def total(self):
        return len(self.records)

    @property
    def miss(self):
        return self.total - self.correct - self.wrong

    def record(self, correct=None):
        if correct is None:
            self.records.append((SHOW_TIME, "miss"))
            self.start_time = time.time()
        elif correct:
            cost_time = int(1000 * (time.time() - self.start_time))
            self.records[-1] = (cost_time, "correct")
            self.correct += 1
        else:
            cost_time = int(1000 * (time.time() - self.start_time))
            self.records[-1] = (cost_time, "wrong")
            self.wrong += 1

    @property
    def result_args(self):
        correct_rate = round(self.correct * 100 / self.total)
        wrong_rate = round(self.wrong * 100 / self.total)
        miss_rate = round(100 - correct_rate - wrong_rate)
        return self.correct, self.correct, correct_rate, self.wrong, wrong_rate, self.miss, miss_rate


IMAGE_FOLDER = {
    Step.go: "assets/go",
    Step.no_go: "assets/no_go"
}
IMAGE_FILES = {k: os.listdir(v) for k, v in IMAGE_FOLDER.items()}
PROMPT2IMAGE = {
    Step.go: {
        "当你看到狮子或老虎时请按下按钮": ["lion.jpg", "tiger.jpg"]
    },
    Step.no_go: {
        "当你看到不是大象的动物时请按下按钮": ["giraffe.jpg"]
    }
}


class Experiment1Widget(QWidget):
    is_start = False
    current_image = ""
    current_prompt = ""

    summary = None

    def __init__(self):
        super().__init__()
        self.step = Step.go

        self.images = []
        self.prompt = QLabel("Prompt Area")
        self.image = QLabel("Image Area")
        self.button = QPushButton("Start!")
        self.table = QTableWidget()
        self.scoreboard = QLabel("Score:0")
        self.build_ui()

        self.button.clicked.connect(self.__click)

    def build_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.prompt.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.prompt.setWordWrap(True)
        font = self.prompt.font()
        font.setPointSize(30)
        self.prompt.setFont(font)
        self.prompt.setStyleSheet(F"border: {BOARD_SIZE}px solid black")
        layout.addWidget(self.prompt, 1)

        h_layout = QHBoxLayout()

        self.image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image.setWordWrap(True)
        font = self.image.font()
        font.setPointSize(30)
        self.image.setFont(font)
        self.image.setStyleSheet(F"border: {BOARD_SIZE} solid black")
        h_layout.addWidget(self.image, 2)

        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setColumnCount(len(RESULT_HEADERS))
        self.table.setHorizontalHeaderLabels(RESULT_HEADERS)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        h_layout.addWidget(self.table, 1)
        self.table.hide()

        layout.addLayout(h_layout, 3)

        font = self.button.font()
        font.setPointSize(30)
        self.button.setFont(font)
        layout.addWidget(self.button, 1)

        self.scoreboard.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scoreboard.setWordWrap(True)
        font = self.scoreboard.font()
        font.setPointSize(30)
        self.scoreboard.setFont(font)
        layout.addWidget(self.scoreboard, 1)

    def set_table(self):
        self.table.setRowCount(self.summary.total)

        for i, row in enumerate(self.summary.records):
            self.table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            for j, e in enumerate(row):
                self.table.setItem(i, j + 1, QTableWidgetItem(str(e)))
        self.table.resizeColumnsToContents()

        self.table.show()

    def set_image(self, image):
        self.current_image = image
        pix_map = QPixmap(os.path.join(IMAGE_FOLDER[self.step], image)).scaled(
            self.image.width() - BOARD_SIZE * 2, self.image.height() - BOARD_SIZE * 2,
            Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
        )
        self.image.setPixmap(pix_map)

    def set_prompt(self, prompt):
        self.current_prompt = prompt
        self.prompt.setText(prompt)

    def set_score(self, score):
        self.scoreboard.setText(f"Score:{score}")

    def __click(self):
        if self.is_start:
            self.__trigger()
        else:
            self.__start()

    def __start(self):
        self.set_prompt(random.choice(list(PROMPT2IMAGE[self.step])))
        self.set_score(0)

        self.images = IMAGE_FILES[self.step].copy() * MAX_TURN
        self.image.setText("Image Area")
        self.table.hide()
        self.button.setText("Match!")
        self.button.setEnabled(False)

        self.is_start = True
        self.summary = Summary()
        QTimer.singleShot(READY_TIME, self.__show)

    def __trigger(self):
        if self.current_image in PROMPT2IMAGE[self.step][self.current_prompt]:
            self.summary.record(True)
            self.set_score(self.summary.correct)
        else:
            self.summary.record(False)
        self.button.setEnabled(False)

    def __show(self):
        if not self.images:
            self.__stop()
            return

        image = self.images.pop(random.randint(0, len(self.images) - 1))
        self.set_image(image)
        self.summary.record()

        self.button.setEnabled(True)
        QTimer.singleShot(SHOW_TIME, self.__pause)

    def __pause(self):
        self.image.clear()
        QTimer.singleShot(PAUSE_TIME, self.__show)

    def __stop(self):
        self.is_start = False
        self.button.setText("Start!")
        self.image.setText(
            RESULT_TEMPLATE.format(*self.summary.result_args)
        )
        self.set_table()
        self.button.setEnabled(True)
        if self.step == Step.go:
            self.step = Step.no_go
        else:
            self.step = Step.go
