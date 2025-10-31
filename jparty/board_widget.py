from PyQt6.QtWidgets import QWidget, QGridLayout
from PyQt6.QtGui import QPalette
from PyQt6.QtCore import QTimer
import random
import itertools
import simpleaudio as sa
from functools import partial

from jparty.game import Board
from jparty.style import MyLabel, CARDPAL, JBLUE, DARKBLUE
from jparty.constants import CATEGORY_REVEAL_TIME, QUESTION_REVEAL_TIME, BEFORE_REVEAL_WAIT_TIME
from jparty.utils import resource_path


class CardLabel(QWidget):
    def __init__(self, text, parent=None):
        super().__init__(parent)

        self.label = MyLabel(text, self.startFontSize, parent=self)
        self.label.setAutosizeMargins(0.1)
        self.setPalette(CARDPAL)
        self.setAutoFillBackground(True)

    def startFontSize(self):
        return self.height() * 0.6

    def setText(self, text):
        self.label.setText(text)

    @property
    def text(self):
        return self.label.text()

    def resizeEvent(self, event):
        self.label.setGeometry(self.rect())


class CategoryCard(CardLabel):
    pass


class QuestionCard(CardLabel):
    def __init__(self, game, question=None):
        self.game = game
        self.__question = question
        super().__init__(self.__moneytext())
        self.label.setStyleSheet("color: #ffcc00")
        self.label.setAutosizeMargins(0.2)

    @property
    def question(self):
        return self.__question

    def __moneytext(self):
        if self.question is not None and not self.question.complete:
            return "$" + str(self.question.value)
        else:
            return ""

    @question.setter
    def question(self, q):
        self.__question = q
        self.setText(self.__moneytext())

    def startFontSize(self):
        return self.height() * 0.5

    def inactive(self):
        return self.question is None or self.question.complete


class HostQuestionCard(QuestionCard):
    def __init__(self, game, question=None):
        super().__init__(game, question)
        self.setMouseTracking(True)

    def mousePressEvent(self, event):
        if self.inactive():
            return None

        self.leaveEvent(None)
        self.game.load_question(self.question)

    def leaveEvent(self, event):
        if self.inactive():
            return None

        pal = self.palette()
        pal.setColor(QPalette.ColorRole.Window, JBLUE)
        self.setPalette(pal)

    def enterEvent(self, event):
        if self.inactive():
            return None

        pal = self.palette()
        pal.setColor(QPalette.ColorRole.Window, DARKBLUE)
        self.setPalette(pal)


class BoardWidget(QWidget):
    rows = 6
    columns = 6

    def __init__(self, game, parent=None):
        super().__init__(parent)
        self.game = game

        self.responses_open = False

        self.questionwidget = None
        self.question_labels = []

        self.grid_layout = QGridLayout()

        self.resizeEvent(None)

        for x in range(Board.size[0]):
            self.grid_layout.setRowStretch(x, 1)
        for y in range(Board.size[1] + 1):
            self.grid_layout.setColumnStretch(y, 1)

        for x in range(Board.size[0]):
            for y in range(Board.size[1] + 1):
                if y == 0:
                    label = CategoryCard("")
                    self.grid_layout.addWidget(label, 0, x)
                else:
                    if self.parent().host():
                        label = HostQuestionCard(game, None)
                    else:
                        label = QuestionCard(game, None)
                    self.question_labels.append(label)
                    self.grid_layout.addWidget(label, y, x)

        self.setLayout(self.grid_layout)
        self.show()

    def load_round(self, round):
        gl = self.grid_layout

        sa.WaveObject.from_wave_file(resource_path("board_fill.wav")).play()

        category_delay = BEFORE_REVEAL_WAIT_TIME + 8 * QUESTION_REVEAL_TIME

        question_cards_ix = list( itertools.product(range(Board.size[0]), range(1, Board.size[1]+1)) )
        random.shuffle(question_cards_ix)

        for (x,y) in question_cards_ix:
            q = round.get_question(x, y - 1)
            gl.itemAtPosition(y, x).widget().question = None
            delay = random.randint(0, 5) * QUESTION_REVEAL_TIME + BEFORE_REVEAL_WAIT_TIME
            QTimer.singleShot(delay, partial(self.set_question, x, y, q))

        for x in range(Board.size[0]):
            gl.itemAtPosition(0, x).widget().setText("")
            delay = category_delay + x * CATEGORY_REVEAL_TIME
            QTimer.singleShot(delay, partial(self.set_category, x, round.categories[x]))

    def resizeEvent(self, event):
        self.grid_layout.setSpacing(self.width() // 150)

    def set_category(self, x, text):
        if not self.game.game_started():
            return
        card = self.grid_layout.itemAtPosition(0, x).widget()
        card.setText(text)

    def set_question(self, x, y, question):
        if not self.game.game_started():
            return
        card = self.grid_layout.itemAtPosition(y, x).widget()
        card.question = question

    @property
    def board(self):
        return self.game.current_round

    def clear(self):
        gl = self.grid_layout
        for x in range(Board.size[0]):
            for y in range(Board.size[1] + 1):
                if y == 0:
                    # Categories
                    gl.itemAtPosition(y, x).widget().setText("")
                else:
                    # Questions
                    gl.itemAtPosition(y, x).widget().question = None
