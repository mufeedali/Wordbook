# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2016-2020 Mufeed Ali <fushinari@protonmail.com>
# SPDX-License-Identifier: GPL-3.0-or-later

import os

from gi.repository import Gio, Gtk, Handy

from wordbook import utils
from wordbook.settings import Settings

PATH = os.path.dirname(__file__)


@Gtk.Template(resource_path=f"{utils.RES_PATH}/ui/settings_window.ui")
class SettingsWindow(Handy.PreferencesWindow):
    """Allows the user to customize Wordbook to some extent."""

    __gtype_name__ = "SettingsWindow"

    _cdef_switch = Gtk.Template.Child("cdef_switch")
    _double_click_switch = Gtk.Template.Child("double_click_switch")
    _live_search_switch = Gtk.Template.Child("live_search_switch")
    _pronunciations_accent_row = Gtk.Template.Child("pronunciations_accent_row")

    _max_hide_switch = Gtk.Template.Child("max_hide_switch")
    _dark_ui_switch = Gtk.Template.Child("dark_ui_switch")
    _dark_font_switch = Gtk.Template.Child("dark_font_switch")

    def __init__(self, **kwargs):
        """Initialize the Settings window."""
        super().__init__(**kwargs)

        self._cdef_switch.connect("notify::active", self._on_cdef_switch_activate)
        self._double_click_switch.connect(
            "notify::active", self._double_click_switch_activate
        )
        self._live_search_switch.connect(
            "notify::active", self._on_live_search_activate
        )
        self._max_hide_switch.connect(
            "notify::active", self._on_max_hide_switch_activate
        )
        self._dark_ui_switch.connect("notify::active", self._on_dark_ui_switch_activate)
        self._dark_font_switch.connect(
            "notify::active", self._on_dark_font_switch_activate
        )

        # Pronunciations accent choices.
        liststore = Gio.ListStore.new(Handy.ValueObject)
        liststore.insert(0, Handy.ValueObject.new("American English"))
        liststore.insert(1, Handy.ValueObject.new("British English"))

        self._pronunciations_accent_row.bind_name_model(
            liststore, Handy.ValueObject.dup_string
        )
        self._pronunciations_accent_row.connect(
            "notify::selected-index", self._on_pronunciations_accent_activate
        )

    def load_settings(self):
        """Load settings from the Settings instance."""
        self._cdef_switch.set_active(Settings.get().cdef)
        self._double_click_switch.set_active(Settings.get().double_click)
        self._live_search_switch.set_active(Settings.get().live_search)
        self._pronunciations_accent_row.set_selected_index(
            Settings.get().pronunciations_accent_value
        )

        self._max_hide_switch.set_active(Settings.get().gtk_max_hide)
        self._dark_ui_switch.set_active(Settings.get().gtk_dark_ui)
        self._dark_font_switch.set_active(Settings.get().gtk_dark_font)

    @staticmethod
    def _on_cdef_switch_activate(switch, _gparam):
        """Change custom definition state."""
        Settings.get().cdef = switch.get_active()

    @staticmethod
    def _double_click_switch_activate(switch, _gparam):
        """Change 'double click to search' state."""
        Settings.get().double_click = switch.get_active()

    @staticmethod
    def _on_live_search_activate(switch, _gparam):
        """Change live search state."""
        Settings.get().live_search = switch.get_active()

    @staticmethod
    def _on_pronunciations_accent_activate(row, _gparam):
        """Change pronunciations' accent."""
        Settings.get().pronunciations_accent_value = row.get_selected_index()

    @staticmethod
    def _on_max_hide_switch_activate(switch, _gparam):
        """Change 'Hide window buttons when Wordbook is maximized' state."""
        Settings.get().gtk_max_hide = switch.get_active()

    @staticmethod
    def _on_dark_ui_switch_activate(switch, _gparam):
        """Change UI theme."""
        Settings.get().gtk_dark_ui = switch.get_active()
        Gtk.Settings.get_default().set_property(
            "gtk-application-prefer-dark-theme", switch.get_active()
        )

    @staticmethod
    def _on_dark_font_switch_activate(switch, _gparam):
        """Change definitions' font colors."""
        Settings.get().gtk_dark_font = switch.get_active()
