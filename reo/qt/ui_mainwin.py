# -*- coding: utf-8 -*-
# Copyright (C) 2016-2020 Mufeed Ali
# SPDX-License-Identifier: GPL-3.0-only or GPL-3.0-or-later
# Author: Mufeed Ali <fushinari@protonmail.com>

# Form implementation generated from reading ui file 'mainwin.ui'
#
# Created by: PyQt5 UI code generator 5.14.2
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_ReoMain():
    def setupUi(self, ReoMain):
        ReoMain.setObjectName("ReoMain")
        ReoMain.resize(388, 388)
        icon = QtGui.QIcon.fromTheme("accessories-dictionary")
        ReoMain.setWindowIcon(icon)
        self.centralwidget = QtWidgets.QWidget(ReoMain)
        self.centralwidget.setAutoFillBackground(True)
        self.centralwidget.setObjectName("centralwidget")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(self.centralwidget)
        self.horizontalLayout_2.setContentsMargins(4, 4, 4, 4)
        self.horizontalLayout_2.setSpacing(4)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setSizeConstraint(QtWidgets.QLayout.SetMaximumSize)
        self.verticalLayout.setSpacing(2)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setSpacing(4)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.searchEntry = QtWidgets.QLineEdit(self.centralwidget)
        self.searchEntry.setStyleSheet("")
        self.searchEntry.setClearButtonEnabled(True)
        self.searchEntry.setObjectName("searchEntry")
        self.horizontalLayout.addWidget(self.searchEntry)
        self.searchButton = QtWidgets.QToolButton(self.centralwidget)
        self.searchButton.setStyleSheet("")
        icon = QtGui.QIcon.fromTheme("edit-find")
        self.searchButton.setIcon(icon)
        self.searchButton.setObjectName("searchButton")
        self.horizontalLayout.addWidget(self.searchButton)
        self.clearButton = QtWidgets.QToolButton(self.centralwidget)
        self.clearButton.setStyleSheet("")
        icon = QtGui.QIcon.fromTheme("edit-clear")
        self.clearButton.setIcon(icon)
        self.clearButton.setObjectName("clearButton")
        self.horizontalLayout.addWidget(self.clearButton)
        self.audioButton = QtWidgets.QToolButton(self.centralwidget)
        self.audioButton.setStyleSheet("")
        icon = QtGui.QIcon.fromTheme("audio-speakers-symbolic")
        self.audioButton.setIcon(icon)
        self.audioButton.setObjectName("audioButton")
        self.horizontalLayout.addWidget(self.audioButton)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.defView = QtWidgets.QTextBrowser(self.centralwidget)
        self.defView.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.defView.setPlaceholderText("")
        self.defView.setOpenLinks(False)
        self.defView.setObjectName("defView")
        self.verticalLayout.addWidget(self.defView)
        self.horizontalLayout_2.addLayout(self.verticalLayout)
        ReoMain.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(ReoMain)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 388, 30))
        self.menubar.setObjectName("menubar")
        self.menuSearch = QtWidgets.QMenu(self.menubar)
        self.menuSearch.setObjectName("menuSearch")
        self.menuHelp = QtWidgets.QMenu(self.menubar)
        self.menuHelp.setObjectName("menuHelp")
        self.menuSettings = QtWidgets.QMenu(self.menubar)
        self.menuSettings.setObjectName("menuSettings")
        ReoMain.setMenuBar(self.menubar)
        self.actionPaste_Search = QtWidgets.QAction(ReoMain)
        icon = QtGui.QIcon.fromTheme("edit-paste-symbolic")
        self.actionPaste_Search.setIcon(icon)
        self.actionPaste_Search.setObjectName("actionPaste_Search")
        self.actionSearch_Selected = QtWidgets.QAction(ReoMain)
        icon = QtGui.QIcon.fromTheme("edit-find-symbolic")
        self.actionSearch_Selected.setIcon(icon)
        self.actionSearch_Selected.setObjectName("actionSearch_Selected")
        self.actionRandom_Word = QtWidgets.QAction(ReoMain)
        icon = QtGui.QIcon.fromTheme("media-playlist-shuffle-symbolic")
        self.actionRandom_Word.setIcon(icon)
        self.actionRandom_Word.setObjectName("actionRandom_Word")
        self.actionAbout = QtWidgets.QAction(ReoMain)
        icon = QtGui.QIcon.fromTheme("help-about-symbolic")
        self.actionAbout.setIcon(icon)
        self.actionAbout.setObjectName("actionAbout")
        self.actionQuit = QtWidgets.QAction(ReoMain)
        icon = QtGui.QIcon.fromTheme("window-close-symbolic")
        self.actionQuit.setIcon(icon)
        self.actionQuit.setObjectName("actionQuit")
        self.actionLive_Search = QtWidgets.QAction(ReoMain)
        self.actionLive_Search.setCheckable(True)
        self.actionLive_Search.setObjectName("actionLive_Search")
        self.actionDark_Mode = QtWidgets.QAction(ReoMain)
        self.actionDark_Mode.setCheckable(True)
        self.actionDark_Mode.setChecked(True)
        self.actionDark_Mode.setObjectName("actionDark_Mode")
        self.actionDebug = QtWidgets.QAction(ReoMain)
        self.actionDebug.setCheckable(True)
        self.actionDebug.setObjectName("actionDebug")
        self.menuSearch.addAction(self.actionPaste_Search)
        self.menuSearch.addAction(self.actionSearch_Selected)
        self.menuSearch.addAction(self.actionRandom_Word)
        self.menuHelp.addAction(self.actionAbout)
        self.menuHelp.addAction(self.actionQuit)
        self.menuSettings.addAction(self.actionLive_Search)
        self.menuSettings.addAction(self.actionDark_Mode)
        self.menuSettings.addAction(self.actionDebug)
        self.menubar.addAction(self.menuSearch.menuAction())
        self.menubar.addAction(self.menuSettings.menuAction())
        self.menubar.addAction(self.menuHelp.menuAction())

        self.retranslateUi(ReoMain)
        self.searchEntry.returnPressed.connect(self.searchButton.click)
        self.clearButton.clicked.connect(self.searchEntry.clear)
        QtCore.QMetaObject.connectSlotsByName(ReoMain)

    def retranslateUi(self, ReoMain):
        _translate = QtCore.QCoreApplication.translate
        ReoMain.setWindowTitle(_translate("ReoMain", "Reo"))
        self.searchButton.setToolTip(_translate("ReoMain", "Search"))
        self.searchButton.setText(_translate("ReoMain", "Search"))
        self.clearButton.setToolTip(_translate("ReoMain", "Clear"))
        self.clearButton.setText(_translate("ReoMain", "Clear"))
        self.audioButton.setToolTip(_translate("ReoMain", "Audio"))
        self.audioButton.setText(_translate("ReoMain", "Audio"))
        self.menuSearch.setTitle(_translate("ReoMain", "Search"))
        self.menuHelp.setTitle(_translate("ReoMain", "Help"))
        self.menuSettings.setTitle(_translate("ReoMain", "Settings"))
        self.actionPaste_Search.setText(_translate("ReoMain", "Paste && Search"))
        self.actionPaste_Search.setShortcut(_translate("ReoMain", "Ctrl+Shift+V"))
        self.actionSearch_Selected.setText(_translate("ReoMain", "Search Selected Text"))
        self.actionSearch_Selected.setShortcut(_translate("ReoMain", "Ctrl+S"))
        self.actionRandom_Word.setText(_translate("ReoMain", "Random Word"))
        self.actionRandom_Word.setShortcut(_translate("ReoMain", "Ctrl+R"))
        self.actionAbout.setText(_translate("ReoMain", "About Reo"))
        self.actionQuit.setText(_translate("ReoMain", "Quit"))
        self.actionQuit.setShortcut(_translate("ReoMain", "Ctrl+Q"))
        self.actionLive_Search.setText(_translate("ReoMain", "Live Search"))
        self.actionDark_Mode.setText(_translate("ReoMain", "Dark Mode"))
        self.actionDebug.setText(_translate("ReoMain", "Debug"))
