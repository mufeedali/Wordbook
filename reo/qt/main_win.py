import random
import sys

from PyQt5 import QtWidgets

from reo import base, utils
from reo.qt.ui_mainwin import Ui_ReoMain


class ReoMain(QtWidgets.QMainWindow, Ui_ReoMain):
    """Define all UI interactions."""
    searched_text = None

    def __init__(self, live_search, word_col, sen_col, *args, **kwargs):
        """Initialize the application."""
        super(ReoMain, self).__init__(*args, **kwargs)
        self.setupUi(self)

        self.wn_future = base.get_wn_file()
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
        QtWidgets.QMessageBox.about(
            self,
            f'About Reo-Qt {utils.VERSION}',
            f'<p><b>About Reo-Qt {utils.VERSION}</b></p>'
            '<p>Reo is a dictionary application using dictd, espeak, etc.</p>'
            '<p>This program is MIT-licensed.</p>'
            '<p>Copyright (C) 2016-2020 Mufeed Ali (lastweakness)</p>'
            '<p><a href="http://github.com/lastweakness/reo">GitHub</a></p>'
        )

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
        sys.exit()

    def random_word(self):
        """Choose a random word and pass it to the search box."""
        self.searchEntry.setText(random.choice(self.wn_future.result()[1]))
        self.search_def()

    def entry_changed(self):
        """To live search or not to live search."""
        if self.live_search:
            self.search_def()

    def search_def(self):
        """Search for definition."""
        term = self.searchEntry.text().strip()
        clean_term = term.strip('<>".-?`![](){}/\\:;,*').rstrip("'")
        cleaner = ['(', ')', '<', '>', '[', ']']
        for item in cleaner:
            clean_term = clean_term.replace(item, '')
        if clean_term == self.searched_text:
            return
        self.defView.clear()
        new_ced = QtWidgets.QMessageBox.warning
        wn_list = (
            '00-database-allchars',
            '00-database-info',
            '00-database-short',
            '00-database-url'
        )
        if clean_term in wn_list:
            self.defView.setHtml(f"<tt> Running Reo with WordNet {self.wn_future.result()[0]}</tt>")
            return
        if clean_term == 'fortune -a':
            self.defView.setHtml(base.clean_html(base.get_fortune()))
            return
        if clean_term == 'cowfortune':
            self.defView.setHtml(base.clean_html(base.get_cowfortune()))
            return
        if clean_term == 'reo':
            self.defView.setHtml(base.clean_html(str(
                "<tt>Pronunciation: <b>/ɹˈiːəʊ/</b>\n"
                "  <b>Reo</b> ~ <i>Japanese Word</i>\n"
                "  <b>1:</b> Name of this application, chosen kind of at random.\n"
                "  <b>2:</b> Japanese word meaning 'Wise Center'\n"
                " <b>Similar Words:</b>\n"
                f" <i><font foreground=\"{self.wordCol}\">  ro, re, roe, redo, reno, oreo, ceo, leo, neo, rho, rio, "
                "reb, red, ref, rem, rep, res, ret, rev, rex</font></i></tt>"
            )))
            return
        if clean_term in ('crash now', 'close now'):
            sys.exit()
            return
        if not clean_term == '' and not term.isspace() and not term == '':
            self.defView.setHtml(base.generate_definition(clean_term, self.wordCol, self.senCol, True, "html"))
            self.searched_text = clean_term
            return
        if clean_term == '' and not term.isspace() and not term == '':
            new_ced(self, 'Error: Invalid Input!', "Reo thinks that your input was actually just a bunch of useless"
                    " characters. So, 'Invalid Characters' error!")
        return

    def term_say(self):
        """Say the text out loud."""
        term = self.searchEntry.text().strip()
        speed = '120'  # To change eSpeak-ng audio speed.
        if not term == '':
            base.read_term(term, speed)
        elif term == '' or term.isspace():
            new_ced = QtWidgets.QMessageBox.warning
            new_ced(self, "Umm..?", "Reo can't find any text there! You sure you typed something?")
