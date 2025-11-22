# SPDX-FileCopyrightText: 2016-2025 Mufeed Ali <me@mufeed.dev>
# SPDX-License-Identifier: GPL-3.0-or-later

from gettext import gettext as _

import gi

gi.require_version("Gdk", "4.0")
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gio, GLib, Gtk  # noqa

from wordbook import base, utils  # noqa
from wordbook.constants import RES_PATH  # noqa
from wordbook.window import WordbookWindow  # noqa
from wordbook.settings import Settings  # noqa


class Application(Adw.Application):
    """Manages the windows, properties, and application lifecycle for Wordbook."""

    app_id: str = ""
    development_mode: bool = False
    version: str = "0.0.0"

    lookup_term: str | None = None
    auto_paste_requested: bool = False
    win: WordbookWindow | None = None

    def __init__(self, app_id: str, version: str):
        """Initializes the application, command-line options, and theme."""
        super().__init__(
            application_id=app_id,
            flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE,
        )
        GLib.set_application_name(_("Wordbook"))
        GLib.set_prgname(self.app_id)

        self.app_id = app_id
        self.version = version

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
        """GApplication lifecycle method for one-time setup, like setting resource paths."""
        self.set_resource_base_path(RES_PATH)
        Adw.Application.do_startup(self)

    def do_activate(self):
        """
        The main entry point for when the application is launched.

        It ensures a window is created (if it doesn't exist) and presented.
        """
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
        """
        Handles command-line argument parsing. This can be called before do_activate().

        It processes options like --look-up, --info, and --auto-paste, and can
        trigger actions in an existing window or set state for a new window.

        Returns:
            0 on success.
        """
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
        """Callback for the 'about' action to display the application's about window."""
        about_window = Adw.AboutDialog()
        about_window.set_application_icon(Gio.Application.get_default().app_id)
        about_window.set_application_name(_("Wordbook"))
        about_window.set_version(Gio.Application.get_default().version)
        about_window.set_comments(_("Look up definitions for words"))
        about_window.set_developer_name("Mufeed Ali")
        about_window.set_translator_credits(_("translator-credits"))
        about_window.set_license_type(Gtk.License.GPL_3_0)
        about_window.set_website("https://apps.gnome.org/Wordbook")
        about_window.add_link(_("Source Code"), "https://github.com/mufeedali/Wordbook")
        about_window.set_issue_url("https://github.com/mufeedali/Wordbook/issues")
        about_window.set_copyright(_("Copyright © 2016-2025 Mufeed Ali"))
        about_window.present(self.win)

    def on_quit(self, _action, _param):
        """Callback for the 'quit' action."""
        self.quit()

    def setup_actions(self):
        """
        Creates and connects global application actions and keyboard shortcuts.

        These are actions that are not specific to a single window, such as 'About'
        and 'Quit'. It also defines the application-wide keyboard accelerators.
        """
        about_action = Gio.SimpleAction.new("about", None)
        about_action.connect("activate", self.on_about)
        self.add_action(about_action)

        quit_action = Gio.SimpleAction.new("quit", None)
        quit_action.connect("activate", self.on_quit)
        self.add_action(quit_action)

        self.set_accels_for_action("app.quit", ["<Primary>q"])
        self.set_accels_for_action("win.quit", ["<Primary>w"])
        self.set_accels_for_action("win.search-selected", ["<Primary>s"])
        self.set_accels_for_action("win.random-word", ["<Primary>r"])
        self.set_accels_for_action("win.paste-search", ["<Primary><Shift>v"])
        self.set_accels_for_action("win.preferences", ["<Primary>comma"])
        self.set_accels_for_action("win.toggle-sidebar", ["F9"])
        self.set_accels_for_action("win.toggle-menu", ["F10"])
