# -*- coding: utf-8 -*-
# Copyright (C) 2016-2020 Mufeed Ali
# SPDX-License-Identifier: GPL-3.0-only or GPL-3.0-or-later
# Author: Mufeed Ali <fushinari@protonmail.com>

import os
import random

from gi.repository import Gdk, GLib, Gtk

from reo import base, utils
from reo.gtk.settings_window import SettingsWindow
from reo.settings import Settings

PATH = os.path.dirname(__file__)


@Gtk.Template(filename=f'{PATH}/ui/window.ui')
class ReoGtkWindow(Gtk.ApplicationWindow):
    __gtype_name__ = 'ReoGtkWindow'

    _clear_button = Gtk.Template.Child('clear_button')
    _def_event_box = Gtk.Template.Child('def_event_box')
    _def_view = Gtk.Template.Child('def_view')
    _pronunciation_view = Gtk.Template.Child('pronunciation_view')
    _term_view = Gtk.Template.Child('term_view')
    _header_bar = Gtk.Template.Child('header_bar')
    _menu_button = Gtk.Template.Child('reo_menu_button')
    _search_entry = Gtk.Template.Child('search_entry')
    _search_button = Gtk.Template.Child('search_button')
    _speak_button = Gtk.Template.Child('speak_button')
    _stack = Gtk.Template.Child('main_stack')

    _searched_term = None
    _wn_future = base.get_wn_file()

    def __init__(self, **kwargs):
        """Initialize the window."""
        super().__init__(**kwargs)

        builder = Gtk.Builder.new_from_file(f'{PATH}/ui/menu.xml')
        menu = builder.get_object('reo-menu')
        self.set_icon_name('accessories-dictionary')

        popover = Gtk.Popover.new_from_model(self._menu_button, menu)
        self._menu_button.set_popover(popover)

        self.connect('notify::is-maximized', self._on_window_state_changed)
        self.connect('key-press-event', self._on_key_press_event)
        self._clear_button.connect('clicked', self._on_clear_clicked)
        self._def_event_box.connect('button_press_event', self._on_def_event)
        self._def_view.connect('activate-link', self._on_link_activated)
        self._search_button.connect('clicked', self._on_search_clicked)
        self._search_entry.connect('changed', self._on_entry_changed)
        self._speak_button.connect('clicked', self._on_speak_clicked)

    def on_about(self, _action, _param):
        """Show the about window."""
        about_dialog = Gtk.AboutDialog(
            transient_for=self,
            modal=True
        )
        about_dialog.set_logo_icon_name('accessories-dictionary')
        about_dialog.set_program_name('Reo')
        about_dialog.set_version(utils.VERSION)
        about_dialog.set_comments(
            'Reo is a dictionary application that uses dictd, dict-wn and '
            'eSpeak-ng to provide a complete user interface.'
        )
        about_dialog.set_authors(['Mufeed Ali', ])
        about_dialog.set_license_type(Gtk.License.GPL_3_0)
        about_dialog.set_website("https://www.github.com/fushinari/reo")
        about_dialog.set_copyright('Copyright © 2016-2020 Mufeed Ali')
        about_dialog.connect('response', lambda dialog, response: dialog.destroy())
        about_dialog.present()

    def on_paste_search(self, _action, _param):
        """Search text in clipboard."""
        text = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD).wait_for_text()
        if text is not None and not text.strip() == '' and not text.isspace():
            GLib.idle_add(self._search_entry.set_text, text)
            GLib.idle_add(self._on_search_clicked)
            GLib.idle_add(self._search_entry.grab_focus)

    def on_preferences(self, _action, _param):
        """Show settings window."""
        window = SettingsWindow(transient_for=self)
        window.connect('destroy', self._on_preferences_destroy)
        window.load_settings()
        window.present()

    def on_random_word(self, _action, _param):
        """Search a random word from the wordlist."""
        random_word = random.choice(self._wn_future.result()[1])
        GLib.idle_add(self._search_entry.set_text, random_word)
        GLib.idle_add(self._on_search_clicked, pause=False, text=random_word)
        GLib.idle_add(self._search_entry.grab_focus)

    def on_search_selected(self, _action, _param):
        """Search selected text from inside or outside the window."""
        text = Gtk.Clipboard.get(Gdk.SELECTION_PRIMARY).wait_for_text()
        if text is not None and not text.strip() == '' and not text.isspace():
            text = text.replace('         ', '').replace('\n', '')
            GLib.idle_add(self._search_entry.set_text, text)
            GLib.idle_add(self._on_search_clicked, pause=False, text=text)
            GLib.idle_add(self._search_entry.grab_focus)

    def on_shortcuts(self, _action, _param):
        """Launch the Keyboard Shortcuts window."""
        builder = Gtk.Builder.new_from_file(f'{PATH}/ui/shortcuts_window.ui')
        shortcuts_window = builder.get_object('shortcuts')
        shortcuts_window.set_transient_for(self)
        shortcuts_window.show()

    def _on_clear_clicked(self, _button):
        """Clear all text in the window."""
        GLib.idle_add(self._def_view.set_text, '')
        GLib.idle_add(self._pronunciation_view.set_text, '')
        GLib.idle_add(self._term_view.set_text, '')
        GLib.idle_add(self._search_entry.set_text, '')
        GLib.idle_add(self._speak_button.set_visible, False)
        self.__page_switch('welcome_page')

    def _on_def_event(self, _eventbox, event):
        if Settings.get().double_click and event.type == Gdk.EventType._2BUTTON_PRESS:
            text = Gtk.Clipboard.get(Gdk.SELECTION_PRIMARY).wait_for_text()
            if text is not None and not text.strip() == '' and not text.isspace():
                text = text.split(' ')[0]
                GLib.idle_add(self._search_entry.set_text, text)
                GLib.idle_add(self._on_search_clicked, pause=False, text=text)
                GLib.idle_add(self._search_entry.grab_focus)

    def _on_key_press_event(self, _widget, event):
        """Focus onto the search entry when needed (quick search)."""
        modifiers = event.get_state() & Gtk.accelerator_get_default_mod_mask()

        shift_mask = Gdk.ModifierType.SHIFT_MASK
        key_unicode = Gdk.keyval_to_unicode(event.keyval)
        if GLib.unichar_isgraph(chr(key_unicode)) and modifiers in (shift_mask, 0):
            self._search_entry.grab_focus_without_selecting()

    def _on_link_activated(self, _widget, data):
        """Search for terms that are marked as hyperlinks."""
        if data.startswith('search'):
            GLib.idle_add(self._search_entry.set_text, data[7:])
            self._on_search_clicked(pause=False, text=data[7:])

    def _on_preferences_destroy(self, _window):
        """Refresh view when Preferences window is closed. Only necessary for definition now."""
        if self._searched_term is not None:
            self._on_search_clicked(pass_check=True, pause=False, text=self._searched_term)

    def _on_search_clicked(self, _button=None, pass_check=False, pause=True, text=None):
        """Pass data to search function and set TextView data."""
        if not text:
            text = self._search_entry.get_text().strip()

        except_list = ('fortune -a', 'cowfortune')
        if pass_check or not text == self._searched_term or text in except_list:
            if pause:
                GLib.idle_add(self._def_view.set_text, '')
                GLib.idle_add(self._pronunciation_view.set_text, '')
                GLib.idle_add(self._term_view.set_text, '')
                GLib.idle_add(self._speak_button.set_visible, False)

            self._searched_term = text
            if not text.strip() == '':
                out = self.__search(text)

                if out is None:
                    return

                GLib.idle_add(self._term_view.set_markup,
                              f'<span size="large" weight="bold">{out["term"].strip()}</span>')
                GLib.idle_add(self._pronunciation_view.set_markup, f'<i>{out["pronunciation"].strip()}</i>')

                out_text = base.clean_pango(f'{out["definition"]}')
                if out['close']:
                    out_text = out_text + base.clean_pango(f'\n\n{out["close"].strip()}').replace('&', '&amp;')

                GLib.idle_add(self._def_view.set_markup, out_text)
                if text not in except_list and out["term"] != 'Lookup failed.':
                    GLib.idle_add(self._speak_button.set_visible, True)

                return

            self.__page_switch('welcome_page')
            return

    def _on_speak_clicked(self, _button):
        """Say the search entry out loud with espeak speech synthesis."""
        speed = '120'  # To change eSpeak-ng audio speed.
        text = self._searched_term
        base.read_term(text, speed)

    def _on_window_state_changed(self, _window, _state):
        """Detect changes to the window state and adapt."""
        if Settings.get().gtk_max_hide and not os.environ.get('GTK_CSD') == '0':
            if self.props.is_maximized:
                GLib.idle_add(self._header_bar.set_show_close_button, False)
            else:
                GLib.idle_add(self._header_bar.set_show_close_button, True)

    def _on_entry_changed(self, _entry):
        """Detect changes to text and do live search if enabled."""
        if Settings.get().live_search:
            GLib.idle_add(self._on_search_clicked)

    def __new_error(self, primary_text, seconday_text):
        """Show an error dialog."""
        dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.OK, primary_text)
        dialog.format_secondary_text(seconday_text)
        dialog.run()
        dialog.destroy()

    def __page_switch(self, page):
        if self._stack.get_visible_child_name == page:
            return True
        GLib.idle_add(self._stack.set_visible_child_name, page)
        return False

    def __search(self, search_text):
        """Clean input text, give errors and pass data to reactor."""
        text = base.cleaner(search_text)
        if not text == '' and not text.isspace():
            self.__page_switch('content_page')
            return base.reactor(text, Settings.get().gtk_dark_font, self._wn_future.result()[0], Settings.get().cdef)
        self.__page_switch('welcome_page')
        if not Settings.get().live_search:
            self.__new_error(
                'Invalid Input',
                'Reo thinks that your input was actually just a bunch of useless characters. '
                'And so, an \'Invalid Characters\' error.'
            )
        self._searched_term = None
        return None
