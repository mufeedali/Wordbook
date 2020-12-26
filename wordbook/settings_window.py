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
    _debug_switch = Gtk.Template.Child("debug_switch")
    _double_click_switch = Gtk.Template.Child("double_click_switch")
    _live_search_switch = Gtk.Template.Child("live_search_switch")
    _max_hide_switch = Gtk.Template.Child("max_hide_switch")
    _dark_ui_switch = Gtk.Template.Child("dark_ui_switch")
    _dark_font_switch = Gtk.Template.Child("dark_font_switch")

    def __init__(self, **kwargs):
        """Initialize the Settings window."""
        super().__init__(**kwargs)

        self._cdef_switch.connect("notify::active", self._on_cdef_switch_activate)
        self._debug_switch.connect("notify::active", self._on_debug_switch_activate)
        self._double_click_switch.connect(
            "notify::active", self._double_click_switch_activate
        )
        self._live_search_switch.connect(
            "notify::active", self._on_live_search_activate
        )
        self._max_hide_switch.connect(
            "notify::active", self._on_max_hide_swtich_activate
        )
        self._dark_ui_switch.connect("notify::active", self._on_dark_ui_swtich_activate)
        self._dark_font_switch.connect(
            "notify::active", self._on_dark_font_swtich_activate
        )

        self._debug_switch.set_sensitive(
            not Gio.Application.get_default().development_mode
        )

    def load_settings(self):
        """Load settings from the Settings instance."""
        self._cdef_switch.set_active(Settings.get().cdef)
        self._debug_switch.set_active(Settings.get().debug)
        self._double_click_switch.set_active(Settings.get().double_click)
        self._live_search_switch.set_active(Settings.get().live_search)
        self._max_hide_switch.set_active(Settings.get().gtk_max_hide)
        self._dark_ui_switch.set_active(Settings.get().gtk_dark_ui)
        self._dark_font_switch.set_active(Settings.get().gtk_dark_font)

    @staticmethod
    def _on_cdef_switch_activate(switch, _gparam):
        """Change custom definition state."""
        Settings.get().cdef = switch.get_active()

    @staticmethod
    def _on_debug_switch_activate(switch, _gparam):
        """Change debugging mode state."""
        Settings.get().debug = switch.get_active()
        utils.log_init(Settings.get().debug)

    @staticmethod
    def _double_click_switch_activate(switch, _gparam):
        """Change 'double click to search' state."""
        Settings.get().double_click = switch.get_active()

    @staticmethod
    def _on_live_search_activate(switch, _gparam):
        """Change live search state."""
        Settings.get().live_search = switch.get_active()

    @staticmethod
    def _on_max_hide_swtich_activate(switch, _gparam):
        """Change 'Hide window buttons when Wordbook is maximized' state."""
        Settings.get().gtk_max_hide = switch.get_active()

    @staticmethod
    def _on_dark_ui_swtich_activate(switch, _gparam):
        """Change UI theme."""
        Settings.get().gtk_dark_ui = switch.get_active()
        Gtk.Settings.get_default().set_property(
            "gtk-application-prefer-dark-theme", switch.get_active()
        )

    @staticmethod
    def _on_dark_font_swtich_activate(switch, _gparam):
        """Change definitions' font colors."""
        Settings.get().gtk_dark_font = switch.get_active()
