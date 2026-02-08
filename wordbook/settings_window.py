# SPDX-FileCopyrightText: 2016-2026 Mufeed Ali <me@mufeed.dev>
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from gi.repository import Adw, Gtk

from wordbook import utils
from wordbook.constants import RES_PATH
from wordbook.settings import PronunciationAccent, Settings

if TYPE_CHECKING:
    from wordbook.window import WordbookWindow

PATH: str = os.path.dirname(__file__)


@Gtk.Template(resource_path=f"{RES_PATH}/ui/settings-window.ui")
class SettingsDialog(Adw.PreferencesDialog):
    """A dialog window that allows the user to customize Wordbook."""

    __gtype_name__ = "SettingsDialog"

    _dark_ui_switch: Adw.SwitchRow = Gtk.Template.Child("dark_ui_switch")

    _double_click_switch: Adw.SwitchRow = Gtk.Template.Child("double_click_switch")
    _live_search_switch: Adw.SwitchRow = Gtk.Template.Child("live_search_switch")
    _auto_paste_switch: Adw.SwitchRow = Gtk.Template.Child("auto_paste_switch")
    _pronunciations_accent_row: Adw.ComboRow = Gtk.Template.Child("pronunciations_accent_row")

    def __init__(self, parent: WordbookWindow, **kwargs):
        """Initializes the Settings window, loads current settings, and connects signals."""
        super().__init__(**kwargs)

        self.parent: WordbookWindow = parent

        self.load_settings()

        self._double_click_switch.connect("notify::active", self._double_click_switch_activate)
        self._live_search_switch.connect("notify::active", self._on_live_search_activate)
        self._auto_paste_switch.connect("notify::active", self._on_auto_paste_switch_activate)
        self._dark_ui_switch.connect("notify::active", self._on_dark_ui_switch_activate)
        self._pronunciations_accent_row.connect("notify::selected", self._on_pronunciations_accent_activate)

    def load_settings(self):
        """Loads settings from the Settings singleton and applies them to the UI widgets."""
        self._double_click_switch.set_active(Settings.get().double_click)
        self._live_search_switch.set_active(Settings.get().live_search)
        self._auto_paste_switch.set_active(Settings.get().auto_paste_on_launch)
        self._pronunciations_accent_row.set_selected(Settings.get().pronunciations_accent.index)

        self._dark_ui_switch.set_active(Settings.get().gtk_dark_ui)

    @staticmethod
    def _double_click_switch_activate(switch, _gparam):
        """Callback for the 'double-click to search' switch. Saves the new state."""
        Settings.get().double_click = switch.get_active()

    def _on_live_search_activate(self, switch, _gparam):
        """Callback for the 'live search' switch. Toggles UI elements and saves the new state."""
        self.parent.completer.set_popup_completion(not switch.get_active())
        self.parent.search_button.set_visible(not switch.get_active())
        if not switch.get_active():
            self.parent.set_default_widget(self.parent.search_button)
        Settings.get().live_search = switch.get_active()

    @staticmethod
    def _on_auto_paste_switch_activate(switch, _gparam):
        """Callback for the 'auto-paste on launch' switch. Saves the new state."""
        Settings.get().auto_paste_on_launch = switch.get_active()

    @staticmethod
    def _on_pronunciations_accent_activate(row, _gparam):
        """Callback for the pronunciation accent dropdown. Saves the new selection."""
        Settings.get().pronunciations_accent = PronunciationAccent.from_index(row.get_selected())

    @staticmethod
    def _on_dark_ui_switch_activate(switch, _gparam):
        """Callback for the 'force dark mode' switch. Applies the theme and saves the setting."""
        Settings.get().gtk_dark_ui = switch.get_active()
        Adw.StyleManager.get_default().set_color_scheme(
            Adw.ColorScheme.FORCE_DARK if switch.get_active() else Adw.ColorScheme.PREFER_LIGHT
        )
