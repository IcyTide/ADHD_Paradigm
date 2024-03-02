import os
import random
from enum import Enum
import time

from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QTableWidget, QAbstractItemView, \
    QTableWidgetItem, QHeaderView, QHBoxLayout
from PySide6.QtGui import QPixmap, Qt
from PySide6.QtCore import QTimer


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


READY_TIME = 3000
SHOW_TIME = 800
PAUSE_TIME = 200

PRACTICE_TURN = 2
TEST_TURN = 4
TEST_EPOCH = 6

BOARD_SIZE = 2

RESULT_TEMPLATE = """
本次共计得分：{}
选择正确{}个，正确率：{}%
选择错误{}个，错误率：{}%
漏选{}个，漏选率：{}%
""".strip()
RESULT_HEADERS = ["Turn", "Elapse", "Result"]

IMAGE_FOLDER = {
    Step.go: "assets/go",
    Step.no_go: "assets/no_go"
}
IMAGE_FILES = {k: os.listdir(v) for k, v in IMAGE_FOLDER.items()}
PROMPT2IMAGE = {
    Step.go: {
        "当你看到狮子或老虎时请按下按钮": ["lion.jpg", "tiger.jpg"],
        "小朋友，你看到狮子或者老虎时请按下按键，如果你选择对了得1分，错误不得分": ["lion.jpg", "tiger.jpg"]
    },
    Step.no_go: {
        "当你看到不是大象的动物时请按下按钮": ["giraffe.jpg"],
        "小朋友，你看到大象以外得其他动物时请按下按键，如果你选择对了得1分，错误不得分": ["giraffe.jpg"]
    }
}
PRACTICE_PROMPTS = [
    "小朋友，你看到狮子或者老虎时请按下按键，如果你选择对了得1分，错误不得分",
    "小朋友，你看到大象以外得其他动物时请按下按键，如果你选择对了得1分，错误不得分"
]
PRACTICE_FINISH_TEXTS = [
    "如果你已经知道怎么游戏，请点击继续按键",
    "如果你已经知道怎么游戏，那么我们可以正式开始"
]


class Experiment1Widget(QWidget):
    is_start = False

    start_func = None
    stop_func = None

    current_epoch = 0
    current_image = ""
    current_prompt = ""

    summary = None

    def __init__(self):
        super().__init__()
        self.step = Step.go

        self.start_func = self.start_practice_1
        self.stop_func = self.stop_practice_1

        self.images = []
        self.prompt = QLabel()
        self.image = QLabel()
        self.button = QPushButton()
        self.table = QTableWidget()
        self.scoreboard = QLabel()
        self.build_ui()

        self.prepare_practice_1()

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

    def set_score(self):
        score = self.summary.correct
        self.scoreboard.setText(f"Score:{score}")

    def __click(self):
        if self.is_start:
            self.__trigger()
        else:
            self.start_func()

    def prepare_practice_1(self):
        self.step = Step.go
        self.set_prompt(PRACTICE_PROMPTS[0])
        self.summary = Summary()
        self.set_score()
        self.image.setText("Image Area")
        self.button.setText("开始")
        self.button.setEnabled(True)
        self.start_func = self.start_practice_1

    def start_practice_1(self):
        self.images = IMAGE_FILES[self.step].copy() * PRACTICE_TURN
        self.button.setText("Match!")
        self.button.setEnabled(False)
        self.is_start = True
        self.stop_func = self.stop_practice_1
        self.__show()

    def stop_practice_1(self):
        self.button.setText("继续")
        self.button.setEnabled(True)
        self.is_start = False
        self.set_prompt(PRACTICE_FINISH_TEXTS[0])
        self.image.setText(
            RESULT_TEMPLATE.format(*self.summary.result_args)
        )
        self.start_func = self.prepare_practice_2

    def prepare_practice_2(self):
        self.step = Step.no_go
        self.set_prompt(PRACTICE_PROMPTS[1])
        self.summary = Summary()
        self.set_score()
        self.image.setText("Image Area")
        self.button.setText("开始")
        self.button.setEnabled(True)
        self.start_func = self.start_practice_2

    def start_practice_2(self):
        self.images = IMAGE_FILES[self.step].copy() * PRACTICE_TURN
        self.button.setText("Match!")
        self.button.setEnabled(False)
        self.is_start = True
        self.stop_func = self.stop_practice_2
        self.__show()

    def stop_practice_2(self):
        self.button.setText("继续")
        self.button.setEnabled(True)
        self.is_start = False
        self.set_prompt(PRACTICE_FINISH_TEXTS[1])
        self.image.setText(
            RESULT_TEMPLATE.format(*self.summary.result_args)
        )
        self.prepare_test()

    def prepare_test(self):
        self.step = Step.go
        self.button.setText("开始测试")
        self.button.setEnabled(True)
        self.summary = Summary()
        self.set_score()
        self.start_func = self.start_test
        self.stop_func = self.switch_test

        self.current_epoch = 0

    def start_test(self):
        self.set_prompt(random.choice(list(PROMPT2IMAGE[self.step])[:-1]))
        self.image.setText("Image Area")
        self.images = IMAGE_FILES[self.step].copy() * PRACTICE_TURN
        self.button.setText("Match!")
        self.button.setEnabled(False)
        self.is_start = True

        self.current_epoch += 1
        QTimer.singleShot(READY_TIME, self.__show)

    def switch_test(self):
        if self.step == Step.go:
            self.step = Step.no_go
        else:
            self.step = Step.go

        if self.current_epoch == TEST_EPOCH:
            self.stop_test()
        else:
            self.start_test()

    def stop_test(self):
        self.image.setText(
            RESULT_TEMPLATE.format(*self.summary.result_args)
        )
        self.set_table()

    def __trigger(self):
        if self.current_image in PROMPT2IMAGE[self.step][self.current_prompt]:
            self.summary.record(True)
            self.set_score()
        else:
            self.summary.record(False)
        self.button.setEnabled(False)

    def __show(self):
        if not self.images:
            self.stop_func()
            return

        image = self.images.pop(random.randint(0, len(self.images) - 1))
        self.set_image(image)
        self.summary.record()

        self.button.setEnabled(True)
        QTimer.singleShot(SHOW_TIME, self.__pause)

    def __pause(self):
        self.image.clear()
        QTimer.singleShot(PAUSE_TIME, self.__show)
