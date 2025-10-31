from PyQt6.QtGui import QColor, QPalette, QGuiApplication
from PyQt6.QtCore import QMargins

from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
)

from jparty.board_widget import BoardWidget
from jparty.scoreboard import ScoreBoard, HostScoreBoard
from jparty.borders import Borders, HostBorders
from jparty.question_widget import (
    QuestionWidget,
    DailyDoubleWidget,
    FinalJeopardyWidget,
    HostQuestionWidget,
    HostDailyDoubleWidget,
    HostFinalJeopardyWidget,
)
from jparty.final_display import FinalDisplay
from jparty.welcome_widget import Welcome, QRWidget


class DisplayWindow(QMainWindow):
    def __init__(self, game):

        super().__init__()
        self.game = game
        self.setWindowTitle("Host" if self.host() else "Board")

        colorpal = QPalette()
        colorpal.setColor(QPalette.ColorRole.Window, QColor("#000000"))
        self.setPalette(colorpal)

        self.welcome_widget = None
        self.question_widget = None

        self.board_widget = BoardWidget(game, self)
        self.scoreboard = self.create_score_board()
        self.borders = self.create_border_widget()

        self.board_layout = QHBoxLayout()
        self.board_layout.addWidget(self.borders.left, 1)
        self.board_layout.addWidget(self.board_widget, 20)
        self.board_layout.addWidget(self.borders.right, 1)

        self.newWidget = QWidget(self)
        self.main_layout = QVBoxLayout()
        self.main_layout.addLayout(self.board_layout, 7)
        self.main_layout.addWidget(self.scoreboard, 2)
        self.newWidget.setLayout(self.main_layout)

        self.welcome_widget = self.create_start_menu()

        self.final_window = None
        self.final_display = None

        self.setCentralWidget(self.newWidget)

        monitor = QGuiApplication.screens()[self.monitor()].geometry()

        self.setGeometry(monitor)

        self.showFullScreen()

        self.show()

    def host(self):
        return False

    def monitor(self):
        return 1
        # return 0

    def create_border_widget(self):
        return Borders(self)

    def create_start_menu(self):
        return QRWidget(self.game.buzzer_controller.host(), self)

    def create_score_board(self):
        return ScoreBoard(self.game, self)

    def create_question_widget(self, q):
        if q.dd:
            return DailyDoubleWidget(q, self)
        else:
            return QuestionWidget(q, self)

    def create_final_widget(self, q):
        return FinalJeopardyWidget(q, self)

    def resizeEvent(self, event):
        fullrect = self.rect()
        margins = (
            QMargins(
                fullrect.width(), fullrect.height(), fullrect.width(), fullrect.height()
            )
            * 0.3
        )
        if self.welcome_widget is not None:
            self.welcome_widget.setGeometry(fullrect - margins)
        if self.final_display is not None:
            self.final_display.setGeometry(fullrect)

    def show_welcome_widgets(self):
        self.welcome_widget.setVisible(True)
        self.welcome_widget.setDisabled(False)
        self.welcome_widget.restart()

    def hide_welcome_widgets(self):
        self.welcome_widget.setVisible(False)
        self.welcome_widget.setDisabled(True)

    def hide_question(self):
        self.board_widget.setVisible(True)
        self.board_layout.replaceWidget(self.question_widget, self.board_widget)
        self.question_widget.deleteLater()
        self.question_widget = None

    def load_question(self, q):
        self.question_widget = self.create_question_widget(q)
        self.board_widget.setVisible(False)
        self.board_layout.replaceWidget(self.board_widget, self.question_widget)

    def load_final(self, q):
        self.question_widget = self.create_final_widget(q)
        self.board_widget.setVisible(False)
        self.board_layout.replaceWidget(self.board_widget, self.question_widget)

    def load_final_judgement(self):
        self.final_display = FinalDisplay(self.game, self)
        self.final_window = self.final_display.answer_widget

    def closeEvent(self, event):
        super().closeEvent(event)
        self.game.close()

    def player_widget(self, player):
        for pw in self.scoreboard.player_widgets:
            if pw.player is player:
                return pw

    def remove_card(self, q):
        for label in self.board_widget.question_labels:
            if label.question is q:
                label.question = None

    def restart(self):
        self.hide_question()
        self.final_display.close()
        self.final_display = None
        self.board_widget.clear()
        self.show_welcome_widgets()
        self.scoreboard.refresh_players()


class HostDisplayWindow(DisplayWindow):
    def __init__(self, game):
        super().__init__(game)

    def host(self):
        return True

    def monitor(self):
        return 0

    def create_start_menu(self):
        return Welcome(self.game, self)

    def create_score_board(self):
        return HostScoreBoard(self.game, self)

    def create_border_widget(self):
        return HostBorders(self)

    def create_question_widget(self, q):
        if q.dd:
            return HostDailyDoubleWidget(q, self)
        else:
            return HostQuestionWidget(q, self)

    def create_final_widget(self, q):
        return HostFinalJeopardyWidget(q, self)

    def keyPressEvent(self, event):
        self.game.keystroke_manager.call(event.key())

    def hide_welcome_widgets(self):
        super().hide_welcome_widgets()
        self.scoreboard.hide_close_buttons()
