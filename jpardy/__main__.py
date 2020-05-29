import sys
import os
from random import shuffle
from PyQt5.QtGui import QPainter, QPen, QBrush, QImage, QColor, QFont, QMovie, QPixmap
from PyQt5.QtWidgets import *#QWidget, QApplication, QDesktopWidget, QPushButton
from PyQt5.QtCore import Qt, QRectF, QPoint, QTimer, QSize
import logging
import pickle
from threading import Thread
from random import choice
import time

from .retrieve import get_game, get_all_games, get_game_sum
from .buzzer.controller import BuzzerController
from .boardwindow import DisplayWindow

def updateUI(f):
    def wrapper(self, *args):
        ret = f(self, *args)
        self.update()
        return ret
    return wrapper

class Welcome(QMainWindow):
    def __init__(self, SC):
        super().__init__()
        self.socket_controller = SC
        self.socket_controller.welcome_window = self
        self.title = 'JParty!'
        self.left = 10
        self.top = 10
        self.width = 500
        self.height = 300
        self.all_games = None
        self.valid_game = False

        self.icon_label = QLabel(self)
        self.startButton = QPushButton('Start!', self)

        self.randButton = QPushButton('loading...', self)
        self.summary_label = QLabel("", self)

        self.textbox = QLineEdit(self)
        self.gameid_label = QLabel("Game ID:", self)
        # self.player_heading = QLabel("Players:", self)
        self.player_labels = [QLabel(self) for _ in range(3)]



        self.players = []

        self.monitor_error = QLabel("JParty requires two seperate monitors", self)


        self.show()
        self.initUI()

        if os.path.exists(".bkup"):
            self.run_game(pickle.load(open(".bkup",'rb')))

        else:
            self.full_index_thread = Thread(target=self.full_index)
            self.full_index_thread.start()

    def full_index(self):
        self.all_games = get_all_games()
        self.randButton.setEnabled(True)
        self.randButton.setText("Random")
        print('got all games')

    @updateUI
    def random(self, checked):
        self.full_index_thread.join()
        game_id = choice(self.all_games)
        self.textbox.setText(str(game_id))
        self.textbox.show()

    @updateUI
    def _show_summary(self,text):
        try:
            game_id = int(text)
            self.summary_label.setText(get_game_sum(game_id))
            self.valid_game = True
        except ValueError as e:
            self.summary_label.setText("invalid game id")
            self.valid_game = False
        self.check_start()

    def show_summary(self, text):
        t = Thread(target=self._show_summary, args=(text,))
        t.start()


    def check_second_monitor(self):
        if len(qApp.screens()) > 1:
            self.monitor_error.hide()
            self.windowHandle().setScreen(qApp.screens()[0])

            self.host_overlay = HostOverlay(self.socket_controller.host())
            self.host_overlay.windowHandle().setScreen(qApp.screens()[1])
            self.host_overlay.show()

        self.check_start()

    def initUI(self):
        print(self.socket_controller.localip())
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        qtRectangle = self.frameGeometry()
        centerPoint = QDesktopWidget().availableGeometry().center()
        qtRectangle.moveCenter(centerPoint)
        self.move(qtRectangle.topLeft())

        icon_size = 64
        icon = QPixmap(os.getcwd()+"/icon.png")
        self.icon_label.setPixmap(icon.scaled(icon_size, icon_size, transformMode=Qt.SmoothTransformation))
        self.icon_label.setGeometry((self.rect().width()-icon_size)/2, 10, icon_size, icon_size)

        self.monitor_error.setStyleSheet("QLabel { color: red}")
        self.monitor_error.setGeometry(140, 75, self.rect().width(), 20)

        qApp.screenAdded.connect(self.check_second_monitor)
        qApp.screenRemoved.connect(self.check_second_monitor)
        self.check_second_monitor()


        self.startButton.setToolTip('Start Game')
        self.startButton.move(280,95)
        self.startButton.clicked.connect(self.start_game)
        self.startButton.setEnabled(False)

        self.randButton.setToolTip('Random Game')
        self.randButton.move(280,120)
        self.randButton.setFocus(False)
        self.randButton.clicked.connect(self.random)
        self.randButton.setEnabled(False)
        summary_margin = 50
        self.summary_label.setGeometry(summary_margin, 150, self.rect().width()-2*summary_margin,40)
        self.summary_label.setAlignment(Qt.AlignHCenter)

        self.gameid_label.move(120,105)
        self.textbox.move(180, 100)
        self.textbox.resize(100,40)
        self.textbox.textChanged.connect(self.show_summary)
        f = self.textbox.font()
        f.setPointSize(30) # sets the size to 27
        self.textbox.setFont(f)

        loading_movie = QMovie("loading.gif")
        movie_width = 64
        loading_movie.setScaledSize(QSize(movie_width, movie_width))
        label_fontsize = 25
        # self.player_heading.setGeometry(0, 140, self.rect().width(), 50)
        # self.player_heading.setAlignment(Qt.AlignHCenter)
        for i,label in enumerate(self.player_labels):
            f = label.font()
            f.setPointSize(label_fontsize) # sets the size to 27
            label.setFont(f)

            label.setMovie(loading_movie)
            label_margin = (self.rect().width() - 3*movie_width)//4
            label.setGeometry(label_margin * (i+1) + movie_width*i, 210, movie_width, movie_width)
        loading_movie.start()

        self.show()
        print(len(qApp.screens()))

    def check_start(self):
        if self.startable():
            self.startButton.setEnabled(True)
        else:
            self.startButton.setEnabled(False)


    def startable(self):
        return self.valid_game and len(self.players)>0 and len(qApp.screens())>1


    def start_game(self):
        try:
            game_id = int(self.textbox.text())
        except ValueError as e:
            error_dialog = QErrorMessage()
            error_dialog.showMessage('Invalid game ID')
            return False

        game = get_game(game_id)

        game.scores = {n:0 for n in self.players}
        self.run_game(game)

    def run_game(self, game):
        print(game.rounds)
        self.socket_controller.game = game
        game.buzzer_controller = self.socket_controller
        self.host_overlay.hide()
        self.show_board(game)


    def show_board(self, game):
        self.alex_window = DisplayWindow(game,alex=True,monitor=0)
        self.main_window = DisplayWindow(game,alex=False,monitor=1)

    def new_player(self, name):
        self.player_labels[len(self.players)].setText(name)
        self.players.append(name)
        self.check_start()
        self.update()

    def closeEvent(self, event):
        if os.path.exists(".bkup"):
            os.remove('.bkup')
        QApplication.quit()


class HostOverlay(QMainWindow):
    def __init__(self, host):
        QMainWindow.__init__(self)

        screen_width = QDesktopWidget().screenGeometry(1).width()
        display_width = int(0.7 * screen_width)
        display_height = int(0.1 * display_width)
        font_size = int(0.6 * display_height)

        self.setWindowFlags(
            Qt.WindowStaysOnTopHint |
            Qt.FramelessWindowHint |
            Qt.X11BypassWindowManagerHint
            )
        self.setGeometry(QStyle.alignedRect(
            Qt.LeftToRight, Qt.AlignCenter,
            QSize(display_width, display_height),
            QDesktopWidget().screenGeometry(1)))

        font = QFont()
        font.setPointSize(font_size)
        self.label = QLabel("http://"+host, self)
        self.label.setGeometry(self.rect())
        self.label.setAlignment(Qt.AlignVCenter | Qt.AlignHCenter)
        self.label.setFont(font)


        self.show()


def main():
    # game_id = 4727

    # game = get_game(game_id)
    # for r in game.rounds:
    # 	for q in r.questions:
    # 		print(q.answer)

    app = QApplication(sys.argv)
    SC = BuzzerController()
    wel = Welcome(SC)
    SC.start()
    #wel.start_game(SC)

    sys.exit(app.exec_())