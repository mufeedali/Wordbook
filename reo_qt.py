#!/usr/bin/python

"""
Reo-Qt is a dictionary application made with Python and Qt5.

It is the Qt5 frontend for Reo. It uses existing tools and as such, easily
works across most Linux distributions without any changes.
"""

# The MIT License (MIT)

# Copyright (c) 2019-2020 Mufeed Ali
# This file is part of Reo

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# Author: Mufeed Ali

import sys
import reo_base
import logging
import argparse  # for CommandLine-Interface (CLI).
from qtpy import QtWidgets

from mainwin import Ui_ReoMain

parser = argparse.ArgumentParser()  # declare parser as the ArgumentParser used
mgroup = parser.add_mutually_exclusive_group()
mgroup.add_argument("-i", "--verinfo", action="store_true",
                    help="Advanced Version Info")
parser.add_argument("-l", "--livesearch", action="store_true",
                    help="Enable live search")
parser.add_argument("-v", "--verbose", action="store_true",
                    help="Make it scream louder")
parsed = parser.parse_args()
if(parsed.verbose):
    level = logging.DEBUG
    debug = True
else:
    level = logging.WARNING
    debug = False
logging.basicConfig(level=level, format="%(asctime)s - " +
                    "[%(levelname)s] [%(threadName)s] (%(module)s:" +
                    "%(lineno)d) %(message)s")

senCol = "cyan"  # Color of sentences in Dark mode
wordCol = "lightgreen"  # Color of: Similar Words, Synonyms and Antonyms.

reo_version = reo_base.reo_version
reo_fold = reo_base.reo_fold
cdef_fold = reo_base.cdef_fold
reo_config = reo_base.reo_config
livesearch = False
searchedText = None

if parsed.verinfo:
    reo_base.verinfo()
    sys.exit()
if parsed.livesearch:
    livesearch = True


class ReoMain(QtWidgets.QMainWindow, Ui_ReoMain):
    """Define all UI interactions."""

    def __init__(self, *args, obj=None, **kwargs):
        """Initialize the application."""
        super(ReoMain, self).__init__(*args, **kwargs)
        self.setupUi(self)
        self.searchButton.clicked.connect(self.searchDef)
        self.audioButton.clicked.connect(self.termSay)
        self.searchEntry.textChanged.connect(self.entryChanged)

    def entryChanged(self):
        """To live search or not to live search."""
        term = self.searchEntry.text()
        cleanTerm = term.strip().strip('<>"?`![]()/^\\:;,')
        if livesearch and not cleanTerm == searchedText:
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
            self.defView.setHtml(reo_base.dataObtain(cleanTerm, wordCol,
                                                     senCol, "html", debug))
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


def main():
    """Execute the application."""
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName("Reo")
    main = ReoMain()
    main.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
