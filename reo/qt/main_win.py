import lzma
import random
import threading

from PyQt5 import QtWidgets

from reo import reo_base, utils
from reo.qt.ui_mainwin import Ui_ReoMain

WN_VERSION = '3.1'
WN_CHECK_ONCE = False
WN = None
SEARCHED = None


def wn_check():
    """Check if WordNet is properly installed."""
    global WN_VERSION, WN_CHECK_ONCE, WN
    if not WN_CHECK_ONCE:
        WN_VERSION = reo_base.wn_ver_check()
        WN_CHECK_ONCE = True
    WN = str(lzma.open(utils.get_word_list(WN_VERSION), 'r').read()).split('\\n')


threading.Thread(target=wn_check).start()


class ReoMain(QtWidgets.QMainWindow, Ui_ReoMain):
    """Define all UI interactions."""
    searched_text = None

    def __init__(self, live_search, word_col, sen_col, *args, **kwargs):
        """Initialize the application."""
        super(ReoMain, self).__init__(*args, **kwargs)
        self.setupUi(self)
        self.live_search = live_search
        self.wordCol = word_col
        self.senCol = sen_col
        self.searchButton.clicked.connect(self.search_def)
        self.audioButton.clicked.connect(self.term_say)
        self.searchEntry.textChanged.connect(self.entry_changed)
        self.actionRandom_Word.triggered.connect(self.random_word)
        self.actionAbout.triggered.connect(self.about)
        self.actionPaste_Search.triggered.connect(self.paste_search)
        self.actionSearch_Selected.triggered.connect(self.search_selected)
        self.actionQuit.triggered.connect(self.quit)

    def about(self):
        """Show an About window."""
        QtWidgets.QMessageBox.about(self, f'About Reo-Qt {utils.VERSION}',
                                    f'<p><b>About Reo-Qt {utils.VERSION}</b></p>'
                                    '<p>Reo is a dictionary application using dictd, espeak, etc.</p>'
                                    '<p>This program is MIT-licensed.</p>'
                                    '<p>Copyright (C) 2016-2020 Mufeed Ali (lastweakness)</p>'
                                    '<p><a href="http://github.com/lastweakness/reo">GitHub</a></p>')

    def paste_search(self):
        """Paste and search."""
        self.searchEntry.setText(QtWidgets.QApplication.clipboard().text())
        self.search_def()

    def search_selected(self):
        """Search selected text."""
        self.searchEntry.setText(self.defView.textCursor().selectedText())
        self.search_def()

    @staticmethod
    def quit():
        """Quit the application."""
        exit(0)

    def random_word(self):
        """Choose a random word and pass it to the search box."""
        self.searchEntry.setText(random.choice(WN))
        self.search_def()

    def entry_changed(self):
        """To live search or not to live search."""
        term = self.searchEntry.text()
        clean_term = term.strip().strip('<>"-?`![](){}/\\:;,*')
        if self.live_search and not clean_term == self.searched_text:
            self.search_def()

    def search_def(self):
        """Search for definition."""
        term = self.searchEntry.text()
        self.defView.clear()
        new_ced = QtWidgets.QMessageBox.warning
        clean_term = term.strip().strip('<>"?`![]()/^\\:;,*')
        if clean_term == 'fortune -a':
            out = reo_base.fortune().strip().replace('\n', '<br>')
            out = out.replace(' ', '&nbsp;')
            self.defView.setHtml(out)
        elif clean_term == 'cowfortune':
            out = reo_base.cowfortune().strip().replace('\n', '<br>')
            out = out.replace(' ', '&nbsp;')
            self.defView.setHtml(out)
        elif not clean_term == '' and not term.isspace() and not term == '':
            self.defView.setHtml(reo_base.data_obtain(clean_term, self.wordCol, self.senCol, "html"))
            self.searched_text = clean_term
        elif clean_term == '' and not term.isspace() and not term == '':
            new_ced(self, 'Error: Invalid Input!', "Reo thinks that your input was actually just a bunch of useless"
                    " characters. So, 'Invalid Characters' error!")

    def term_say(self):
        """Say the text out loud."""
        term = self.searchEntry.text().strip()
        speed = '120'  # To change eSpeak-ng audio speed.
        if not term == '':
            reo_base.read_term(term, speed)
        elif term == '' or term.isspace():
            new_ced = QtWidgets.QMessageBox.warning
            new_ced(self, "Umm..?", "Reo can't find any text there! You sure \nyou typed something?")
        print(term)
