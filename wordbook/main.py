# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2016-2023 Mufeed Ali <mufeed.dev@pm.me>
# SPDX-License-Identifier: GPL-3.0-or-later

import gi

from gettext import gettext as _

gi.require_version("Gdk", "4.0")
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gio, GLib, Gtk  # noqa

from wordbook import base, utils  # noqa
from wordbook.window import WordbookWindow  # noqa
from wordbook.settings import Settings  # noqa


class Application(Adw.Application):
    """Manages the windows, properties, etc of Wordbook."""

    app_id = ""
    development_mode = False
    version = "0.0.0"

    lookup_term = ""
    win = None

    def __init__(self, app_id, version):
        """Initialize the application."""
        super().__init__(
            application_id=app_id,
            flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE,
        )
        GLib.set_application_name(_("Wordbook"))
        GLib.set_prgname(self.app_id)

        self.app_id = app_id
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

        Adw.StyleManager.get_default().set_color_scheme(
            Adw.ColorScheme.FORCE_DARK
            if Settings.get().gtk_dark_ui
            else Adw.ColorScheme.PREFER_LIGHT
        )

        base.fold_gen()

    def do_startup(self):
        """Manage startup of the application."""
        self.set_resource_base_path(utils.RES_PATH)
        Adw.Application.do_startup(self)

    def do_activate(self):
        """Activate the application."""
        self.win = self.get_active_window()
        if not self.win:
            self.win = WordbookWindow(
                application=self,
                title=_("Wordbook"),
                term=self.lookup_term,
            )
            self.setup_actions()

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

    def on_about(self, _action, _param):
        """Show the about window."""
        about_window = Adw.AboutWindow()
        about_window.set_application_icon(Gio.Application.get_default().app_id)
        about_window.set_application_name(_("Wordbook"))
        about_window.set_version(Gio.Application.get_default().version)
        about_window.set_comments(_("Lookup definitions of any English term."))
        about_window.set_developer_name("Mufeed Ali")
        about_window.set_translator_credits(_("translator-credits"))
        about_window.set_license_type(Gtk.License.GPL_3_0)
        about_window.set_website("https://github.com/mufeedali/Wordbook")
        about_window.set_issue_url("https://github.com/mufeedali/Wordbook/issues")
        about_window.set_copyright(_("Copyright © 2016-2023 Mufeed Ali"))
        about_window.set_transient_for(self.win)
        about_window.present()

    def setup_actions(self):
        """Setup the Gio actions for the application."""
        about_action = Gio.SimpleAction.new("about", None)
        about_action.connect("activate", self.on_about)
        self.add_action(about_action)

        self.set_accels_for_action("win.search-selected", ["<Primary>s"])
        self.set_accels_for_action("win.random-word", ["<Primary>r"])
        self.set_accels_for_action("win.paste-search", ["<Primary><Shift>v"])
        self.set_accels_for_action("win.preferences", ["<Primary>comma"])
