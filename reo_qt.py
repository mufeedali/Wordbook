#!/usr/bin/python

"""
Reo-Qt is a dictionary application made with Python and Qt5.

It is the Qt5 frontend for Reo. It uses existing tools and as such, easily
works across most Linux distributions without any changes.
"""

# The MIT License (MIT)

# Copyright (c) 2019 Mufeed Ali
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
import subprocess
import reo_base
from qtpy import QtWidgets

from mainwin import Ui_ReoMain

senCol = "cyan"  # Color of sentences in Dark mode
wordCol = "lightgreen"  # Color of: Similar Words, Synonyms and Antonyms.


class ReoMain(QtWidgets.QMainWindow, Ui_ReoMain):
    """Define all UI interactions."""

    def __init__(self, *args, obj=None, **kwargs):
        """Initialize the application."""
        super(ReoMain, self).__init__(*args, **kwargs)
        self.setupUi(self)
        self.searchButton.clicked.connect(self.searchDef)
        self.audioButton.clicked.connect(self.termSay)

    def searchDef(self):
        """Search for definition."""
        term = self.searchEntry.text()
        self.defView.clear()
        newced = QtWidgets.QMessageBox.warning
        if (not term.strip('<>"?`![]()/\\^:;,') == '' and
                not term.isspace() and not term == ''):
            cleanTerm = term.strip().strip('<>"?`![]()/^\\:;,')
            self.defView.setHtml(self.dataObtain(cleanTerm))
        elif (term.strip('<>"?`![]()/\\:;,') == '' and
              not term.isspace() and
              not term == ''):
            newced('Error: Invalid Input!', "Reo thinks that your input was " +
                   "actually \njust a bunch of useless characters. \nSo, " +
                   "'Invalid Characters' error!")
        elif term.isspace():
            newced(self, "Umm..?", "Reo can't find any text" +
                   " there! You sure \nyou typed something?")
        elif term == '':
            newced(self, "Umm..?", "Reo can't find any text" +
                   " there! You sure \nyou typed something?")

    def dataObtain(self, term):
        """Obtain the data to be processed and presented."""
        strat = "lev"
        try:
            procDefi = subprocess.Popen(["dict", "-d", "wn", term],
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE)
            procPron = subprocess.Popen(["espeak-ng", "-ven-uk-rp",
                                         "--ipa", "-q", term],
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE)
            procClos = subprocess.Popen(["dict", "-m", "-d", "wn",
                                         "-s", strat, term],
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE)
        except Exception as ex:
            print("Didnt Work! ERROR INFO: " + str(ex))
        procDefi.wait()
        defi = procDefi.stdout.read().decode()
        if not defi == '':
            cleanDefi = reo_base.defProcessor(defi, term, senCol, wordCol)
            NoDef = 0
        else:
            cleanDefi = "Coundn't find definition for '" + term + "'."
            NoDef = 1
        procPron.wait()
        pron = procPron.stdout.read().decode()
        cleanPron = " /" + pron.strip().replace('\n ', ' ') + "/"
        procClos.wait()
        clos = procClos.stdout.read().decode()
        cleanClos = reo_base.clsfmt(clos, term)
        fail = 0
        if term.lower() == 'recursion':
            clos = 'recursion'
        if clos == '':
            fail = 1
        if procPron and not NoDef == 1:
            finalPron = "<b>Pronunciation</b>: <b>" + cleanPron + '</b>'
        elif procPron and NoDef == 1:
            finalPron = ("<b>Probable Pronunciation</b>: <b>" + cleanPron +
                         '</b>')
        if fail == 0:
            if NoDef == 1:
                finalClos = ('<b>Did you mean</b>:<br><i><font color="' +
                             wordCol + '">  ' + cleanClos + '</font></i>')
            else:
                finalClos = ('<b>Similar Words</b>:<br>' +
                             '<i><font color="' + wordCol + '">  ' +
                             cleanClos + '</font></i>')
        else:
            finalClos = ''
        finalData = ("<p>" + finalPron + '</p><p>' + cleanDefi +
                     '</p><p>' + finalClos.strip() + "</p>")
        return finalData

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
