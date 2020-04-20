#!/usr/bin/python

"""
Reo-Qt is a dictionary application made with Python and Qt5.

It is the Qt5 frontend for Reo. It uses existing tools and as such, easily
works across most Linux distributions without any changes.
"""

import argparse  # for CommandLine-Interface (CLI).
import logging
import sys

from PyQt5 import QtWidgets

from reo import reo_base, utils
from reo.qt.main_win import ReoMain

PARSER = argparse.ArgumentParser()  # declare parser as the ArgumentParser used
MGROUP = PARSER.add_mutually_exclusive_group()
MGROUP.add_argument("-i", "--verinfo", action="store_true",
                    help="Advanced Version Info")
MGROUP.add_argument("-l", "--livesearch", action="store_true",
                    help="Enable live search")
MGROUP.add_argument("-v", "--verbose", action="store_true",
                    help="Make it scream louder")
PARSED = PARSER.parse_args()
if PARSED.verbose:
    level = logging.DEBUG
    DEBUG = True
else:
    level = logging.WARNING
    DEBUG = False
reo_base.log_init(DEBUG)
logging.basicConfig(level=level,
                    format="%(asctime)s - [%(levelname)s] [%(threadName)s] (%(module)s:%(lineno)d) %(message)s")
reo_base.fold_gen()

SEN_COL = "cyan"  # Color of sentences in Dark mode
WORD_COL = "lightgreen"  # Color of: Similar Words, Synonyms and Antonyms.

REO_VERSION = utils.VERSION
REO_FOLD = utils.CONFIG_FOLD
CDEF_FOLD = utils.CDEF_FOLD
REO_CONFIG = utils.CONFIG_FILE
LIVE_SEARCH = False

if PARSED.verinfo:
    reo_base.get_version_info()
    sys.exit()
if PARSED.livesearch:
    LIVE_SEARCH = True


def main():
    """Execute the application."""
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName("Reo")
    app.setDesktopFileName("Reo")
    logging.info("Executing Reo-Qt")
    main_window = ReoMain(LIVE_SEARCH, WORD_COL, SEN_COL)
    main_window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
