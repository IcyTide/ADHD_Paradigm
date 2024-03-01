import os
import random
import time
from enum import Enum

from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel
from PySide6.QtGui import QPixmap, Qt
from PySide6.QtCore import QTimer

READY_TIME = 3000
SHOW_TIME = 800
PAUSE_TIME = 200

MAX_TURN = 24

BOARD_SIZE = 2


class Step(Enum):
    go = 0
    no_go = 1


IMAGE_FOLDER = {
    Step.go: "assets/go",
    Step.no_go: "assets/no_go"
}
IMAGE_FILES = {k: os.listdir(v) for k, v in IMAGE_FOLDER.items()}
PROMPT2IMAGE = {
    Step.go: {
        "当你看到狮子或老虎时请按下按钮": ["狮子.jpg", "老虎.jpg"]
    },
    Step.no_go: {
        "当你看到大象时不要按下按钮": []
    }
}


class Experiment1Widget(QWidget):
    is_start = False
    current_image = ""
    current_prompt = ""
    current_score = 0
    current_turn = 1

    def __init__(self):
        super().__init__()
        self.step = Step.go

        self.prompt = QLabel()
        self.image = QLabel()
        self.button = QPushButton()
        self.scoreboard = QLabel("Score:0")
        self.init_ui()
        self.build_ui()

        self.button.clicked.connect(self.click)

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

        self.image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image.setWordWrap(True)
        font = self.image.font()
        font.setPointSize(60)
        self.image.setFont(font)
        self.image.setStyleSheet(F"border: {BOARD_SIZE} solid black")
        layout.addWidget(self.image, 3)

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

    def init_ui(self):
        self.prompt.setText("Prompt Area")
        self.image.setText("Image Area")
        self.button.setText("Start!")

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
        self.current_score = score
        self.scoreboard.setText(f"Score:{score}")

    def start(self):
        self.set_prompt(random.choice(list(PROMPT2IMAGE[self.step])))
        self.set_score(0)
        self.button.setText("Match!")

        self.is_start = True
        self.current_turn = 1
        QTimer.singleShot(READY_TIME, self.show)

    def click(self):
        if self.is_start:
            self.trigger()
        else:
            self.start()

    def trigger(self):
        if self.current_image in PROMPT2IMAGE[self.step][self.current_prompt]:
            self.current_score += 1
            self.set_score(self.current_score)

        self.button.setEnabled(False)

    def show(self):
        self.set_image(random.choice(IMAGE_FILES[self.step]))
        self.button.setEnabled(True)
        QTimer.singleShot(SHOW_TIME, self.pause)

    def pause(self):
        self.image.setText("Image Area")
        self.current_turn += 1
        if self.current_turn > MAX_TURN:
            QTimer.singleShot(PAUSE_TIME, self.stop)
        else:
            QTimer.singleShot(PAUSE_TIME, self.show)

    def stop(self):
        self.init_ui()
        self.is_start = False
        self.button.setEnabled(True)
        if self.step == Step.go:
            self.step = Step.no_go
        else:
            self.step = Step.go
