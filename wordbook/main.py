# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2016-2021 Mufeed Ali <fushinari@protonmail.com>
# SPDX-License-Identifier: GPL-3.0-or-later

import gi

gi.require_version("Gdk", "3.0")
gi.require_version("Gtk", "3.0")
gi.require_version("Handy", "1")
from gi.repository import Gdk, Gio, GLib, Gtk, Handy  # noqa

from wordbook import base, utils  # noqa
from wordbook.window import WordbookGtkWindow  # noqa
from wordbook.settings import Settings  # noqa


class Application(Gtk.Application):
    """Manages the windows, properties, etc of Wordbook."""

    development_mode = False
    version = "0.0.0"

    lookup_term = ""
    win = None

    def __init__(self, version):
        """Initialize the application."""
        super().__init__(
            application_id=utils.APP_ID,
            flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE,
        )

        self.version = version

        # Add command line options
        self.add_main_option(
            "look-up",
            b"l",
            GLib.OptionFlags.NONE,
            GLib.OptionArg.STRING,
            "Term to look up",
            None,
        )
        self.add_main_option(
            "info",
            ord("i"),
            GLib.OptionFlags.NONE,
            GLib.OptionArg.NONE,
            "Print version info",
            None,
        )
        self.add_main_option(
            "verbose",
            ord("v"),
            GLib.OptionFlags.NONE,
            GLib.OptionArg.NONE,
            "Make it scream louder",
            None,
        )

    def do_activate(self):
        """Activate the application."""

        def setup_actions(window):
            """Setup the Gio actions for the application."""
            about_action = Gio.SimpleAction.new("about", None)
            about_action.connect("activate", window.on_about)
            self.add_action(about_action)

            paste_search_action = Gio.SimpleAction.new("paste-search", None)
            paste_search_action.connect("activate", window.on_paste_search)
            self.add_action(paste_search_action)

            preferences_action = Gio.SimpleAction.new("preferences", None)
            preferences_action.connect("activate", window.on_preferences)
            self.add_action(preferences_action)

            random_word_action = Gio.SimpleAction.new("random-word", None)
            random_word_action.connect("activate", window.on_random_word)
            self.add_action(random_word_action)

            search_selected_action = Gio.SimpleAction.new("search-selected", None)
            search_selected_action.connect("activate", window.on_search_selected)
            self.add_action(search_selected_action)

            shortcuts_action = Gio.SimpleAction.new("shortcuts", None)
            shortcuts_action.connect("activate", window.on_shortcuts)
            self.add_action(shortcuts_action)

            self.add_accelerator("<Primary>s", "app.search-selected", None)
            self.add_accelerator("<Primary>r", "app.random-word", None)
            self.add_accelerator("<Primary><Shift>v", "app.paste-search", None)
            self.add_accelerator("<Primary>comma", "app.preferences", None)

        self.win = self.props.active_window
        if not self.win:
            self.win = WordbookGtkWindow(
                application=self,
                title="Wordbook",
                term=self.lookup_term,
            )
            setup_actions(self.win)

        self.win.present()

    def do_command_line(self, command_line):
        """Parse commandline arguments."""
        options = command_line.get_options_dict().end().unpack()
        term = ""

        if "verinfo" in options:
            base.get_version_info(self.version)
            return 0

        if "look-up" in options:
            term = options["look-up"]

        utils.log_init(self.development_mode or "verbose" in options or False)

        if self.win is not None:
            self.win.trigger_search(term)
        else:
            self.lookup_term = term

        self.activate()
        return 0

    def do_startup(self):
        """Manage startup of the application."""
        Gtk.Application.do_startup(self)
        Gtk.Settings.get_default().set_property(
            "gtk-application-prefer-dark-theme", Settings.get().gtk_dark_ui
        )

        GLib.set_application_name("Wordbook")
        GLib.set_prgname(utils.APP_ID)

        Handy.init()
        base.fold_gen()

        css_provider = Gtk.CssProvider()
        css_provider.load_from_resource(f'{utils.RES_PATH}/ui/css/style.css')
        screen = Gdk.Screen.get_default()
        Gtk.StyleContext.add_provider_for_screen(
            screen, css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
