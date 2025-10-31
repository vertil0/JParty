from PyQt6.QtGui import (
    QPainter,
    QPen,
    QColor,
    QFont,
)
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout

from jparty.style import MyLabel, CARDPAL

import requests
from PyQt6.QtWidgets import QApplication, QWidget, QLabel
from PyQt6.QtGui import QImage, QPixmap

class QuestionWidget(QWidget):
    def __init__(self, question, parent=None, show_image=True):
        super().__init__(parent)
        self.question = question
        self.setAutoFillBackground(True)

        self.main_layout = QVBoxLayout()

        self.question_text, url = self.getUrl(question.text)

        if url and show_image:
            image = QImage()
            self.question_label = MyLabel("", self.startFontSize, self)
            image.loadFromData(requests.get(url).content)
            image = image.scaledToHeight(800)
            self.question_label.setPixmap(QPixmap(image))
            self.main_layout.addWidget(self.question_label)
        else:
            self.question_label = MyLabel(self.question_text.upper(), self.startFontSize, self)
            self.question_label.setFont(QFont("ITC_ Korinna"))
            self.main_layout.addWidget(self.question_label)
        self.setLayout(self.main_layout)

        self.setPalette(CARDPAL)
        self.show()

    def startFontSize(self):
        return self.width() * 0.05
    
    def getUrl(self, text):
        if 'http' in text:
            text_split = text.split('http')
            text_split[1] = 'http' + text_split[1]
            return text_split
        return text, ''


class HostQuestionWidget(QuestionWidget):
    def __init__(self, question, parent=None):
        super().__init__(question, parent, show_image=False)

        self.question_label.setText(self.question_text)
        self.main_layout.setStretchFactor(self.question_label, 6)
        self.main_layout.addSpacing(self.main_layout.contentsMargins().top())
        self.answer_label = MyLabel(question.answer, self.startFontSize, self)
        self.answer_label.setFont(QFont("ITC_ Korinna"))
        self.main_layout.addWidget(self.answer_label, 1)

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)
        qp.setPen(QPen(QColor("white")))
        line_y = self.main_layout.itemAt(1).geometry().top()
        qp.drawLine(0, line_y, self.width(), line_y)


class DailyDoubleWidget(QuestionWidget):
    def __init__(self, question, parent=None, show_image=True):
        super().__init__(question, parent)
        self.question_label.setVisible(False)

        self.dd_label = MyLabel("DAILY<br/>DOUBLE!", self.startDDFontSize, self)
        self.main_layout.replaceWidget(self.question_label, self.dd_label)

    def startDDFontSize(self):
        return self.width() * 0.2

    def show_question(self):
        self.main_layout.replaceWidget(self.dd_label, self.question_label)
        self.dd_label.deleteLater()
        self.dd_label = None
        self.question_label.setVisible(True)


class HostDailyDoubleWidget(HostQuestionWidget, DailyDoubleWidget):
    def __init__(self, question, parent=None, show_image=False):
        super().__init__(question, parent)
        self.answer_label.setVisible(False)

        self.main_layout.setStretchFactor(self.dd_label, 6)
        self.hint_label = MyLabel(
            "Click the player below who found the Daily Double",
            self.startFontSize,
            self,
        )
        self.main_layout.replaceWidget(self.answer_label, self.hint_label)
        self.main_layout.setStretchFactor(self.hint_label, 1)

    def show_question(self):
        super().show_question()
        self.main_layout.replaceWidget(self.hint_label, self.answer_label)
        self.hint_label.deleteLater()
        self.hint_label = None
        self.answer_label.setVisible(True)


class FinalJeopardyWidget(QuestionWidget):
    def __init__(self, question, parent=None, show_image=True):
        super().__init__(question, parent)
        self.question_label.setVisible(False)

        self.category_label = MyLabel(
            question.category, self.startCategoryFontSize, self
        )
        self.main_layout.replaceWidget(self.question_label, self.category_label)

    def startCategoryFontSize(self):
        return self.width() * 0.1

    def show_question(self):
        self.main_layout.replaceWidget(self.category_label, self.question_label)
        self.category_label.deleteLater()
        self.category_label = None
        self.question_label.setVisible(True)


class HostFinalJeopardyWidget(FinalJeopardyWidget, HostQuestionWidget):
    def __init__(self, question, parent, show_image=False):
        self.display = parent
        super().__init__(question, parent)
        self.answer_label.setVisible(False)

        self.main_layout.setStretchFactor(self.question_label, 6)
        self.hint_label = MyLabel(
            "Waiting for all players to wager...", self.startFontSize, self
        )
        self.main_layout.replaceWidget(self.answer_label, self.hint_label)
        self.main_layout.setStretchFactor(self.hint_label, 1)

    def hide_hint(self):
        self.hint_label.setVisible(True)

    def show_question(self):
        super().show_question()
        self.main_layout.replaceWidget(self.hint_label, self.answer_label)
        self.display.settings_button.setVisible(False)
        self.hint_label.deleteLater()
        self.hint_label = None
        self.answer_label.setVisible(True)
