# SPDX-FileCopyrightText: 2016-2025 Mufeed Ali <me@mufeed.dev>
# SPDX-License-Identifier: GPL-3.0-or-later

import os

from gi.repository import Adw, Gtk

from wordbook import utils
from wordbook.settings import Settings

PATH: str = os.path.dirname(__file__)


@Gtk.Template(resource_path=f"{utils.RES_PATH}/ui/settings_window.ui")
class SettingsDialog(Adw.PreferencesDialog):
    """Allows the user to customize Wordbook to some extent."""

    __gtype_name__ = "SettingsDialog"

    _dark_ui_switch: Adw.SwitchRow = Gtk.Template.Child("dark_ui_switch")

    _double_click_switch: Adw.SwitchRow = Gtk.Template.Child("double_click_switch")
    _live_search_switch: Adw.SwitchRow = Gtk.Template.Child("live_search_switch")
    _auto_paste_switch: Adw.SwitchRow = Gtk.Template.Child("auto_paste_switch")
    _pronunciations_accent_row: Adw.ComboRow = Gtk.Template.Child("pronunciations_accent_row")

    def __init__(self, parent: Adw.ApplicationWindow, **kwargs):
        """Initialize the Settings window."""
        super().__init__(**kwargs)

        self.parent = parent

        self.load_settings()

        self._double_click_switch.connect("notify::active", self._double_click_switch_activate)
        self._live_search_switch.connect("notify::active", self._on_live_search_activate)
        self._auto_paste_switch.connect("notify::active", self._on_auto_paste_switch_activate)
        self._dark_ui_switch.connect("notify::active", self._on_dark_ui_switch_activate)
        self._pronunciations_accent_row.connect("notify::selected", self._on_pronunciations_accent_activate)

    def load_settings(self):
        """Load settings from the Settings instance."""
        self._double_click_switch.set_active(Settings.get().double_click)
        self._live_search_switch.set_active(Settings.get().live_search)
        self._auto_paste_switch.set_active(Settings.get().auto_paste_on_launch)
        self._pronunciations_accent_row.set_selected(Settings.get().pronunciations_accent_value)

        self._dark_ui_switch.set_active(Settings.get().gtk_dark_ui)

    @staticmethod
    def _double_click_switch_activate(switch, _gparam):
        """Change 'double click to search' state."""
        Settings.get().double_click = switch.get_active()

    def _on_live_search_activate(self, switch, _gparam):
        """Change live search state."""
        self.parent.completer.set_popup_completion(not switch.get_active())
        self.parent.search_button.set_visible(not switch.get_active())
        if not switch.get_active():
            self.parent.set_default_widget(self.parent.search_button)
        Settings.get().live_search = switch.get_active()

    @staticmethod
    def _on_auto_paste_switch_activate(switch, _gparam):
        """Change auto paste on launch state."""
        Settings.get().auto_paste_on_launch = switch.get_active()

    @staticmethod
    def _on_pronunciations_accent_activate(row, _gparam):
        """Change pronunciations' accent."""
        Settings.get().pronunciations_accent_value = row.get_selected()

    @staticmethod
    def _on_dark_ui_switch_activate(switch, _gparam):
        """Change UI theme."""
        Settings.get().gtk_dark_ui = switch.get_active()
        Adw.StyleManager.get_default().set_color_scheme(
            Adw.ColorScheme.FORCE_DARK if switch.get_active() else Adw.ColorScheme.PREFER_LIGHT
        )
