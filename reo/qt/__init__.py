#!/usr/bin/python

"""
Reo-Qt is a dictionary application made with Python and Qt5.

It is the Qt5 frontend for Reo. It uses existing tools and as such, easily
works across most Linux distributions without any changes.
"""

import sys
import logging
import argparse  # for CommandLine-Interface (CLI).
from PyQt5 import QtWidgets
from reo import utils, reo_base
from reo.qt.main_win import ReoMain


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

reo_version = utils.VERSION
reo_fold = utils.CONFIG_FOLD
cdef_fold = utils.CDEF_FOLD
reo_config = utils.CONFIG_FILE
livesearch = False

if parsed.verinfo:
    reo_base.verinfo()
    sys.exit()
if parsed.livesearch:
    livesearch = True


def main():
    """Execute the application."""
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName("Reo")
    app.setDesktopFileName("Reo")
    main = ReoMain(livesearch, wordCol, senCol, debug)
    main.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
