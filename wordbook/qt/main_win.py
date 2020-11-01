# -*- coding: utf-8 -*-
# Copyright (C) 2016-2020 Mufeed Ali
# SPDX-License-Identifier: GPL-3.0-only or GPL-3.0-or-later
# Author: Mufeed Ali <fushinari@protonmail.com>

import random
import sys

from PyQt5 import QtCore, QtWidgets

from wordbook import base, utils
from wordbook.qt.ui_mainwin import Ui_WordbookMain
from wordbook.settings import Settings

QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)


class WordbookMain(QtWidgets.QMainWindow, Ui_WordbookMain):
    """Define all UI interactions."""
    searched_term = None

    def __init__(self, *args, **kwargs):
        """Initialize the application."""
        super(WordbookMain, self).__init__(*args, **kwargs)
        self.setupUi(self)

        self.wn_future = base.get_wn_file()

        self.searchButton.clicked.connect(self._on_search_clicked)
        self.audioButton.clicked.connect(self._on_audio_clicked)

        self.searchEntry.textChanged.connect(self._on_entry_changed)
        self.defView.anchorClicked.connect(self._on_link_activated)

        self.actionRandom_Word.triggered.connect(self._on_random_word_triggered)
        self.actionPaste_Search.triggered.connect(self._on_paste_search_triggered)
        self.actionSearch_Selected.triggered.connect(self._on_search_selected_triggered)
        self.actionLive_Search.triggered.connect(self._on_live_search_triggered)
        self.actionDark_Mode.triggered.connect(self._on_dark_mode_triggered)
        self.actionDebug.triggered.connect(self._on_debug_triggered)
        self.actionAbout.triggered.connect(self._on_about)
        self.actionQuit.triggered.connect(self.quit)

        self.actionLive_Search.setChecked(Settings.get().live_search)
        self.actionDark_Mode.setChecked(Settings.get().qt_dark_font)
        self.actionDebug.setChecked(Settings.get().debug)

    @staticmethod
    def quit():
        """Quit the application."""
        sys.exit()

    def _on_about(self):
        """Show an About window."""
        QtWidgets.QMessageBox.about(
            self,
            f'About Wordbook-Qt {utils.VERSION}',
            f'<p><b>About Wordbook-Qt {utils.VERSION}</b></p>'
            '<p>Wordbook is a dictionary application using espeak-ng, python-wn, etc.</p>'
            '<p>Licensed under GNU General Public License, version 3 or later.</p>'
            '<p>Copyright (C) 2016-2020 Mufeed Ali (fushinari)</p>'
            '<p><a href="https://www.github.com/fushinari/wordbook">GitHub</a></p>'
        )

    def _on_audio_clicked(self):
        """Say the text out loud."""
        term = self.searchEntry.text().strip()
        speed = '120'  # To change eSpeak-ng audio speed.
        if not term == '':
            base.read_term(term, speed)
        elif term == '' or term.isspace():
            new_ced = QtWidgets.QMessageBox.warning
            new_ced(self, 'Umm..?', 'Wordbook can\'t find any text there! You sure you typed something?')

    def _on_entry_changed(self):
        """To live search or not to live search."""
        if Settings.get().live_search:
            self._on_search_clicked()

    def _on_dark_mode_triggered(self):
        """Enable or disable dark mode."""
        Settings.get().qt_dark_font = self.actionDark_Mode.isChecked()
        self._on_search_clicked(pass_check=True, pause=False)

    def _on_debug_triggered(self):
        """Enable or disable debug mode."""
        Settings.get().debug = self.actionDebug.isChecked()
        utils.log_init(Settings.get().debug)

    def _on_link_activated(self, url):
        """Search term in link."""
        term = url.toString()
        if term.startswith('search:'):
            term = term[7:]
            self.searchEntry.setText(term)
            self._on_search_clicked(pause=False, text=term)

    def _on_live_search_triggered(self):
        """Enable or disable live search."""
        Settings.get().live_search = self.actionLive_Search.isChecked()

    def _on_search_clicked(self, pass_check=False, pause=True, text=None):
        """Search entered text."""
        if text is None:
            if pass_check:
                text = self.searched_term
            else:
                text = self.searchEntry.text().strip()

        except_list = ('fortune -a', 'cowfortune')
        if pass_check or not text == self.searched_term or text in except_list:
            if pause:
                self.defView.clear()

            self.searched_term = text
            if not text.strip() == '':
                out = self.__search(text)
                if out is None:
                    return

                out_text = base.clean_html(f'<p><b>{out["term"].strip()}</b><br>'
                                           f'{out["pronunciation"].strip()}</p>'
                                           f'<p>{out["definition"] or "Definition not found."}</p>')

                self.defView.setText(out_text)
                return
            return

    def _on_paste_search_triggered(self):
        """Paste and search."""
        self.searchEntry.setText(QtWidgets.QApplication.clipboard().text())
        self._on_search_clicked()

    def _on_random_word_triggered(self):
        """Choose a random word and pass it to the search box."""
        random_word = random.choice(self.wn_future.result()['list'])
        random_word = random_word.replace('_', ' ')
        self.searchEntry.setText(random_word)
        self._on_search_clicked(text=random_word)

    def _on_search_selected_triggered(self):
        """Search selected text."""
        self.searchEntry.setText(self.defView.textCursor().selectedText())
        self._on_search_clicked()

    def __search(self, search_text):
        """Clean input text, give errors and pass data to reactor."""
        text = base.cleaner(search_text)
        if not text == '' and not text.isspace():
            return base.reactor(
                text,
                Settings.get().qt_dark_font,
                self.wn_future.result()['version'],
                self.wn_future.result()['instance'],
                Settings.get().cdef
            )
        new_ced = QtWidgets.QMessageBox.warning
        new_ced(
            self,
            'Invalid Input',
            'Wordbook thinks that your input was actually just a bunch of useless characters.'
            'And so, an \'Invalid Characters\' error.'
        )
        self.searched_term = None
        return None
