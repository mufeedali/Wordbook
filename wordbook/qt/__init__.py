#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (C) 2016-2020 Mufeed Ali
# SPDX-License-Identifier: GPL-3.0-only or GPL-3.0-or-later
# Author: Mufeed Ali <fushinari@protonmail.com>

"""
Wordbook-Qt is a dictionary application made with Python and Qt5.

It is the Qt5 frontend for Wordbook. It uses existing tools and as such, easily
works across most Linux distributions without any changes.
"""

import argparse  # for CommandLine-Interface (CLI).
import signal
import sys

from PySide6 import QtWidgets

from wordbook import base, utils
from wordbook.qt.main_win import WordbookMain
from wordbook.settings import Settings

PARSER = argparse.ArgumentParser()
MGROUP = PARSER.add_mutually_exclusive_group()
MGROUP.add_argument("-i", "--verinfo", action="store_true", help="Print version info")
MGROUP.add_argument(
    "-v", "--verbose", action="store_true", help="Make it scream louder"
)
PARSED = PARSER.parse_args()
utils.log_init(bool(PARSED.verbose) or Settings.get().debug)
signal.signal(
    signal.SIGINT, signal.SIG_DFL
)  # Exit if we get a SIGINT. The exit is dirty but causes no issues.
base.fold_gen()

REO_VERSION = utils.VERSION
REO_FOLD = utils.CONFIG_DIR
CDEF_FOLD = utils.CDEF_DIR
REO_CONFIG = utils.CONFIG_FILE

if PARSED.verinfo:
    base.get_version_info()
    sys.exit()


def main():
    """Execute the application."""
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName("Wordbook")
    utils.log_info("Launching Wordbook-Qt")
    main_window = WordbookMain()
    main_window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
