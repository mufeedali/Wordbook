from PySide2 import QtWidgets
from reo import reo_base

from reo.qt.ui_mainwin import Ui_ReoMain

searchedText = None


class ReoMain(QtWidgets.QMainWindow, Ui_ReoMain):
    """Define all UI interactions."""

    def __init__(self, live_search, word_col, sen_col, debug, *args, obj=None, **kwargs):
        """Initialize the application."""
        super(ReoMain, self).__init__(*args, **kwargs)
        self.setupUi(self)
        self.live_search = live_search
        self.wordCol = word_col
        self.senCol = sen_col
        self.debug = debug
        self.searchButton.clicked.connect(self.search_def)
        self.audioButton.clicked.connect(self.term_say)
        self.searchEntry.textChanged.connect(self.entry_changed)

    def entry_changed(self):
        """To live search or not to live search."""
        term = self.searchEntry.text()
        clean_term = term.strip().strip('<>"?`![]()/^\\:;,')
        if self.live_search and not clean_term == searchedText:
            self.search_def()

    def search_def(self):
        """Search for definition."""
        global searchedText
        term = self.searchEntry.text()
        self.defView.clear()
        new_ced = QtWidgets.QMessageBox.warning
        clean_term = term.strip().strip('<>"?`![]()/^\\:;,')
        if clean_term == 'fortune -a':
            out = reo_base.fortune().strip().replace('\n', '<br>')
            out = out.replace(' ', '&nbsp;')
            self.defView.setHtml(out)
        elif clean_term == 'cowfortune':
            out = reo_base.cowfortune().strip().replace('\n', '<br>')
            out = out.replace(' ', '&nbsp;')
            self.defView.setHtml(out)
        elif not clean_term == '' and not term.isspace() and not term == '':
            self.defView.setHtml(reo_base.data_obtain(clean_term, self.wordCol, self.senCol, "html", self.debug))
            searchedText = clean_term
        elif clean_term == '' and not term.isspace() and not term == '':
            new_ced(self, 'Error: Invalid Input!', "Reo thinks that your input was actually just a bunch of useless" +
                    " characters. So, 'Invalid Characters' error!")

    def term_say(self):
        """Say the text out loud."""
        term = self.searchEntry.text().strip()
        speed = '120'  # To change eSpeak-ng audio speed.
        if not term == '':
            reo_base.read_term(term, speed)
        elif term == '' or term.isspace():
            new_ced = QtWidgets.QMessageBox.warning
            new_ced("Umm..?", "Reo can't find any text there! You sure \nyou typed something?")
        print(term)
