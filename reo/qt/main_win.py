import random
import sys

from PyQt5 import QtWidgets

from reo import base, utils
from reo.qt.ui_mainwin import Ui_ReoMain
from reo.settings import Settings


class ReoMain(QtWidgets.QMainWindow, Ui_ReoMain):
    """Define all UI interactions."""
    searched_term = None

    def __init__(self, *args, **kwargs):
        """Initialize the application."""
        super(ReoMain, self).__init__(*args, **kwargs)
        self.setupUi(self)

        self.wn_future = base.get_wn_file()

        self.searchButton.clicked.connect(self.on_search_clicked)
        self.audioButton.clicked.connect(self.term_say)

        self.searchEntry.textChanged.connect(self.entry_changed)

        self.actionRandom_Word.triggered.connect(self.random_word)
        self.actionPaste_Search.triggered.connect(self.paste_search)
        self.actionSearch_Selected.triggered.connect(self.search_selected)
        self.actionLive_Search.triggered.connect(self.on_live_search_triggered)
        self.actionDark_Mode.triggered.connect(self.on_dark_mode_triggered)
        self.actionDebug.triggered.connect(self.on_debug_triggered)
        self.actionAbout.triggered.connect(self.about)
        self.actionQuit.triggered.connect(self.quit)

        self.actionLive_Search.setChecked(Settings.get().live_search)
        self.actionDark_Mode.setChecked(Settings.get().qt_dark_font)
        self.actionDebug.setChecked(Settings.get().debug)

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

    def entry_changed(self):
        """To live search or not to live search."""
        if Settings.get().live_search:
            self.on_search_clicked()

    def on_dark_mode_triggered(self):
        """Enable or disable dark mode."""
        Settings.get().qt_dark_font = self.actionDark_Mode.isChecked()
        self.on_search_clicked(pass_check=True)

    def on_live_search_triggered(self):
        """Enable or disable live search."""
        Settings.get().live_search = self.actionLive_Search.isChecked()

    def on_debug_triggered(self):
        """Enable or disable debug mode."""
        Settings.get().debug = self.actionDebug.isChecked()
        utils.log_init(Settings.get().debug)

    def on_search_clicked(self, pass_check=False):
        if pass_check:
            text = self.searched_term
        else:
            text = self.searchEntry.text().strip()
        except_list = ('fortune -a', 'cowfortune')
        if pass_check or not text == self.searched_term or text in except_list:
            self.defView.clear()
            self.searched_term = text
            if not text.strip() == '':
                out = self.__search(text)
                if out is not None:
                    self.defView.setHtml(out)

    def paste_search(self):
        """Paste and search."""
        self.searchEntry.setText(QtWidgets.QApplication.clipboard().text())
        self.on_search_clicked()

    @staticmethod
    def quit():
        """Quit the application."""
        sys.exit()

    def random_word(self):
        """Choose a random word and pass it to the search box."""
        self.searchEntry.setText(random.choice(self.wn_future.result()[1]))
        self.on_search_clicked()

    def search_selected(self):
        """Search selected text."""
        self.searchEntry.setText(self.defView.textCursor().selectedText())
        self.on_search_clicked()

    def term_say(self):
        """Say the text out loud."""
        term = self.searchEntry.text().strip()
        speed = '120'  # To change eSpeak-ng audio speed.
        if not term == '':
            base.read_term(term, speed)
        elif term == '' or term.isspace():
            new_ced = QtWidgets.QMessageBox.warning
            new_ced(self, "Umm..?", "Reo can't find any text there! You sure you typed something?")

    def __reactor(self, clean_term):
        """Search for definition."""
        if Settings.get().qt_dark_font:
            sencol = "cyan"  # Color of sentences in Dark mode
            wordcol = "lightgreen"  # Color of: Similar Words,
#                                     Synonyms and Antonyms.
        else:
            sencol = "blue"  # Color of sentences in regular
            wordcol = "green"  # Color of: Similar Words, Synonyms, Antonyms.
        wn_list = (
            '00-database-allchars',
            '00-database-info',
            '00-database-short',
            '00-database-url'
        )
        if clean_term in wn_list:
            return f"<tt> Running Reo with WordNet {self.wn_future.result()[0]}</tt>"
        if clean_term == 'fortune -a':
            return base.clean_html(base.get_fortune())
        if clean_term == 'cowfortune':
            return base.clean_html(base.get_cowfortune())
        if clean_term == 'reo':
            return base.clean_html(str(
                "<tt>Pronunciation: <b>/ɹˈiːəʊ/</b>\n"
                "  <b>Reo</b> ~ <i>Japanese Word</i>\n"
                "  <b>1:</b> Name of this application, chosen kind of at random.\n"
                "  <b>2:</b> Japanese word meaning 'Wise Center'\n"
                " <b>Similar Words:</b>\n"
                f" <i><font foreground=\"{wordcol}\">  ro, re, roe, redo, reno, oreo, ceo, leo, neo, rho, rio, "
                "reb, red, ref, rem, rep, res, ret, rev, rex</font></i></tt>"
            ))
        if clean_term in ('crash now', 'close now'):
            sys.exit()
            return None
        if clean_term and not clean_term == '' and not clean_term.isspace():
            return base.generate_definition(clean_term, wordcol, sencol, True, "html")
        return None

    def __search(self, search_text):
        """Clean input text, give errors and pass data to reactor."""
        text = search_text.strip().strip('<>".-?`![](){}/\\:;,*').rstrip("'")
        cleaner = ['(', ')', '<', '>', '[', ']']
        for item in cleaner:
            text = text.replace(item, '')
        if not text == '' and not text.isspace():
            return self.__reactor(text)
        new_ced = QtWidgets.QMessageBox.warning
        new_ced(
            self,
            "Invalid Input",
            "Reo thinks that your input was actually just a bunch of useless characters."
            "And so, an 'Invalid Characters' error."
        )
        self.searched_term = None
        return None
