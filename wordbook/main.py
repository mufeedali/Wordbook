# SPDX-FileCopyrightText: 2016-2025 Mufeed Ali <me@mufeed.dev>
# SPDX-License-Identifier: GPL-3.0-or-later

from gettext import gettext as _

import gi

gi.require_version("Gdk", "4.0")
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gio, GLib, Gtk  # noqa

from wordbook import base, utils  # noqa
from wordbook.window import WordbookWindow  # noqa
from wordbook.settings import Settings  # noqa


class Application(Adw.Application):
    """Manages the windows, properties, etc of Wordbook."""

    app_id: str = ""
    development_mode: bool = False
    version: str = "0.0.0"

    lookup_term: str | None = None
    auto_paste_requested: bool = False
    win: WordbookWindow | None = None

    def __init__(self, app_id: str, version: str):
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
        self.add_main_option(
            "auto-paste",
            b"p",
            GLib.OptionFlags.NONE,
            GLib.OptionArg.NONE,
            "Automatically paste and search clipboard content",
            None,
        )

        Adw.StyleManager.get_default().set_color_scheme(
            Adw.ColorScheme.FORCE_DARK if Settings.get().gtk_dark_ui else Adw.ColorScheme.PREFER_LIGHT
        )

        base.create_required_dirs()

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
                auto_paste_requested=self.auto_paste_requested,
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

        if "auto-paste" in options:
            self.auto_paste_requested = True

        utils.log_init(self.development_mode or "verbose" in options or False)

        if self.win is not None:
            if term:
                self.win.trigger_search(term)
            elif self.auto_paste_requested:
                self.win.queue_auto_paste()
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
        about_window.set_comments(_("Look up definitions of any English term."))
        about_window.set_developer_name("Mufeed Ali")
        about_window.set_translator_credits(_("translator-credits"))
        about_window.set_license_type(Gtk.License.GPL_3_0)
        about_window.set_website("https://github.com/mufeedali/Wordbook")
        about_window.set_issue_url("https://github.com/mufeedali/Wordbook/issues")
        about_window.set_copyright(_("Copyright © 2016-2025 Mufeed Ali"))
        about_window.set_transient_for(self.win)
        about_window.present()

    def on_quit(self, _action, _param):
        """Quit the application."""
        self.quit()

    def setup_actions(self):
        """Setup the Gio actions for the application."""
        about_action = Gio.SimpleAction.new("about", None)
        about_action.connect("activate", self.on_about)
        self.add_action(about_action)

        quit_action = Gio.SimpleAction.new("quit", None)
        quit_action.connect("activate", self.on_quit)
        self.add_action(quit_action)

        self.set_accels_for_action("app.quit", ["<Primary>q", "Escape"])
        self.set_accels_for_action("win.search-selected", ["<Primary>s"])
        self.set_accels_for_action("win.random-word", ["<Primary>r"])
        self.set_accels_for_action("win.paste-search", ["<Primary><Shift>v"])
        self.set_accels_for_action("win.preferences", ["<Primary>comma"])
