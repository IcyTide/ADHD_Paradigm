import datetime
import os
import random
from enum import Enum
import time

from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QTableWidget, QAbstractItemView, \
    QTableWidgetItem, QHeaderView, QHBoxLayout
from PySide6.QtGui import QPixmap, Qt, QKeySequence
from PySide6.QtCore import QTimer


class Step(Enum):
    go = 0
    no_go = 1


IMAGE_FOLDER = {
    Step.go: "assets/go",
    Step.no_go: "assets/no_go"
}
LOG_FOLDER = "logs/Go-no_go"
if not os.path.exists(LOG_FOLDER):
    os.makedirs(LOG_FOLDER)
LOG_FORMAT = "{}.csv"

IMAGE_FILES = {k: os.listdir(v) for k, v in IMAGE_FOLDER.items()}
PRACTICE_START_PROMPTS = [
    "小朋友，你看到狮子或者老虎时请按下按键，如果你选择对了得1分，错误不得分",
    "小朋友，你看到大象以外得其他动物时请按下按键，如果你选择对了得1分，错误不得分"
]
PRACTICE_FINISH_PROMPTS = [
    "如果你已经知道怎么游戏，请点击继续",
    "如果你已经知道怎么游戏，请点击正式开始"
]
TEST_PROMPTS = {
    Step.go: "当你看到狮子或老虎时请按下按钮",
    Step.no_go: "当你看到不是大象的动物时请按下按钮"
}

PROMPT2IMAGE = {
    PRACTICE_START_PROMPTS[0]: ["lion.jpg", "tiger.jpg"],
    PRACTICE_START_PROMPTS[1]: ["giraffe.jpg"],

    TEST_PROMPTS[Step.go]: ["lion.jpg", "tiger.jpg"],
    TEST_PROMPTS[Step.no_go]: ["giraffe.jpg"],
}

RESULT_TEMPLATE = """
本次实验结束
本次共计得分：{}
选择正确{}个，正确率：{}%
选择错误{}个，错误率：{}%
漏选{}个，漏选率：{}%
""".strip()
RESULT_HEADERS = ["Turn", "Elapse", "Result", "Step"]

READY_TIME = 3000
SHOW_TIME = 800
PAUSE_TIME = 200

PRACTICE_TURN = 20
TEST_TURN = 24
TEST_EPOCH = 6 * 2

BOARD_SIZE = 2


class Summary:
    def __init__(self):
        self.records = []
        self.start_time = 0

        self.correct_count = 0
        self.wrong_count = 0
        self.miss_count = 0
        self.pass_count = 0

    @property
    def total(self):
        return len(self.records)

    def record(self, correct, step):
        if correct == "miss":
            self.records.append((SHOW_TIME, correct, step))
            self.start_time = time.time()
            self.miss_count += 1
        elif correct == "pass":
            self.records.append((SHOW_TIME, correct, step))
            self.start_time = time.time()
            self.pass_count += 1
        elif correct:
            cost_time = int(1000 * (time.time() - self.start_time))
            self.records[-1] = (cost_time, "correct", step)
            self.correct_count += 1
            self.miss_count -= 1
        else:
            cost_time = int(1000 * (time.time() - self.start_time))
            self.records[-1] = (cost_time, "wrong", step)
            self.wrong_count += 1
            self.pass_count -= 1

    @property
    def result_args(self):
        correct_rate = round(self.correct_count * 100 / self.total)
        wrong_rate = round(self.wrong_count * 100 / self.total)
        miss_rate = round(self.miss_count * 100 / self.total)
        return (self.correct_count, self.correct_count, correct_rate, self.wrong_count, wrong_rate,
                self.miss_count, miss_rate)


class Experiment1Widget(QWidget):
    is_start = False
    is_click = False

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
        self.display = QLabel()
        self.button = QPushButton()
        self.table = QTableWidget()

        self.build_ui()

        self.prepare_practice_1()

        self.button.clicked.connect(self.__click)

    def build_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        h_layout = QHBoxLayout()

        self.display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.display.setWordWrap(True)
        font = self.display.font()
        font.setPointSize(30)
        self.display.setFont(font)
        self.display.setStyleSheet(F"border: {BOARD_SIZE} solid black")
        h_layout.addWidget(self.display, 2)

        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setColumnCount(len(RESULT_HEADERS))
        self.table.setHorizontalHeaderLabels(RESULT_HEADERS)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        h_layout.addWidget(self.table, 1)
        self.table.hide()

        layout.addLayout(h_layout, 4)

        font = self.button.font()
        font.setPointSize(30)
        self.button.setFont(font)
        self.button.setStyleSheet("background-color: rgb(255,228,98);")
        layout.addWidget(self.button, 1)

    def set_table(self):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        logs = f"{','.join(RESULT_HEADERS)}\n"
        logs += "\n".join(f"{i + 1}," + ",".join(str(e) for e in row) for i, row in enumerate(self.summary.records))
        logs += "\n" + "\n".join(RESULT_TEMPLATE.format(*self.summary.result_args).split("\n")[1:])
        with open(os.path.join(LOG_FOLDER, LOG_FORMAT.format(timestamp)), "w") as f:
            f.write(logs)
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
            self.display.width() - BOARD_SIZE * 2, self.display.height() - BOARD_SIZE * 4,
            Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
        )
        self.display.setPixmap(pix_map)

    def set_prompt(self, prompt):
        self.current_prompt = prompt
        self.display.setText(prompt)

    def __click(self):
        if self.is_start:
            self.__trigger()
        else:
            self.start_func()

    def __prepare(self, button=None):
        self.summary = Summary()
        if button:
            self.button.setText(button)
        else:
            self.button.setText("开始")
        self.button.setEnabled(True)

    def __start(self, times):
        self.images = IMAGE_FILES[self.step].copy() * (times // len(IMAGE_FILES[self.step]))
        self.table.hide()
        self.button.setText("Match!")
        self.button.setShortcut(QKeySequence(' '))
        self.button.setEnabled(False)
        self.display.setStyleSheet("background-color : transparent")
        self.is_start = True

    def __stop(self, button="开始", table=False):
        self.is_start = False
        self.button.setText(button)
        self.button.setShortcut(QKeySequence())
        self.button.setEnabled(True)
        self.display.setStyleSheet("background-color : transparent")
        self.display.setText(
            RESULT_TEMPLATE.format(*self.summary.result_args)
        )
        if table:
            self.set_table()

    def prepare_practice_1(self):
        self.step = Step.go
        self.start_func = self.start_practice_1
        self.set_prompt(PRACTICE_START_PROMPTS[0])
        self.__prepare()

    def start_practice_1(self):
        self.stop_func = self.stop_practice_1
        self.__start(PRACTICE_TURN)
        self.__show()

    def stop_practice_1(self):
        self.start_func = self.prepare_practice_2
        self.__stop(PRACTICE_FINISH_PROMPTS[0])

    def prepare_practice_2(self):
        self.step = Step.no_go
        self.start_func = self.start_practice_2
        self.set_prompt(PRACTICE_START_PROMPTS[1])
        self.__prepare()

    def start_practice_2(self):
        self.stop_func = self.stop_practice_2
        self.__start(PRACTICE_TURN)
        self.__show()

    def stop_practice_2(self):
        self.__stop(PRACTICE_FINISH_PROMPTS[1])
        self.prepare_test(PRACTICE_FINISH_PROMPTS[1])

    def prepare_test(self, button=None):
        self.step = Step.go
        self.current_epoch = 0
        self.start_func = self.start_test
        self.stop_func = self.switch_test
        self.__prepare(button)

    def start_test(self):
        self.__start(TEST_TURN)
        self.current_epoch += 1
        self.set_prompt(TEST_PROMPTS[self.step])
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
        self.__stop(table=True)

        self.prepare_test()

    def __trigger(self):
        self.button.setEnabled(False)
        if self.current_image in PROMPT2IMAGE[self.current_prompt]:
            self.summary.record(True, self.step.name)
            self.display.setStyleSheet("background-color : green")
        else:
            self.summary.record(False, self.step.name)
            self.display.setStyleSheet("background-color : red")

    def __show(self):
        self.display.setStyleSheet("background-color : transparent")
        if not self.images:
            self.stop_func()
            return

        image = self.images.pop(random.randint(0, len(self.images) - 1))
        self.set_image(image)
        if image in PROMPT2IMAGE[self.current_prompt]:
            self.summary.record("miss", self.step.name)
        else:
            self.summary.record("pass", self.step.name)

        self.button.setEnabled(True)
        QTimer.singleShot(SHOW_TIME, self.__pause)

    def __pause(self):
        self.display.clear()
        # self.display.setStyleSheet("background-color : transparent")
        # self.button.setEnabled(False)
        QTimer.singleShot(PAUSE_TIME, self.__show)
