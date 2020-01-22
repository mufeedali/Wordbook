from PyQt5 import QtWidgets
from reo import reo_base

from reo.qt.ui_mainwin import Ui_ReoMain

searchedText = None


class ReoMain(QtWidgets.QMainWindow, Ui_ReoMain):
    """Define all UI interactions."""

    def __init__(self, livesearch, wordCol, senCol, debug,
                 *args, obj=None, **kwargs):
        """Initialize the application."""
        super(ReoMain, self).__init__(*args, **kwargs)
        self.setupUi(self)
        self.livesearch = livesearch
        self.wordCol = wordCol
        self.senCol = senCol
        self.debug = debug
        self.searchButton.clicked.connect(self.searchDef)
        self.audioButton.clicked.connect(self.termSay)
        self.searchEntry.textChanged.connect(self.entryChanged)

    def entryChanged(self):
        """To live search or not to live search."""
        term = self.searchEntry.text()
        cleanTerm = term.strip().strip('<>"?`![]()/^\\:;,')
        if self.livesearch and not cleanTerm == searchedText:
            self.searchDef()

    def searchDef(self):
        """Search for definition."""
        global searchedText
        term = self.searchEntry.text()
        self.defView.clear()
        newced = QtWidgets.QMessageBox.warning
        cleanTerm = term.strip().strip('<>"?`![]()/^\\:;,')
        if (cleanTerm == 'fortune -a'):
            out = reo_base.fortune().strip().replace('\n', '<br>')
            out = out.replace(' ', '&nbsp;')
            self.defView.setHtml(out)
        elif (cleanTerm == 'cowfortune'):
            out = reo_base.cowfortune().strip().replace('\n', '<br>')
            out = out.replace(' ', '&nbsp;')
            self.defView.setHtml(out)
        elif (not cleanTerm == '' and not term.isspace() and not term == ''):
            self.defView.setHtml(reo_base.dataObtain(cleanTerm, self.wordCol,
                                                     self.senCol, "html",
                                                     self.debug))
            searchedText = cleanTerm
        elif (cleanTerm == '' and not term.isspace() and not term == ''):
            newced(self, 'Error: Invalid Input!', "Reo thinks that your " +
                   "input was actually just a bunch of useless characters. " +
                   "So, 'Invalid Characters' error!")

    def termSay(self):
        """Say the text out loud."""
        term = self.searchEntry.text().strip()
        speed = '120'  # To change eSpeak-ng audio speed.
        if not term == '':
            reo_base.readTerm(term, speed)
        elif term == '' or term.isspace():
            newced = QtWidgets.QMessageBox.warning
            newced("Umm..?", "Reo can't find any text" +
                   " there! You sure \nyou typed something?")
        print(term)
