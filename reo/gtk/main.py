import sys

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gio, GLib, Gtk

from reo.gtk.window import ReoGtkWindow
from reo import reo_base


class Application(Gtk.Application):
    debug = False
    verinfo = False
    dark = False

    def __init__(self):
        """Initialize the application."""

        super().__init__(
            application_id='com.github.lastweakness.reo',
            flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE
        )
        self.add_main_option("dark", ord("d"), GLib.OptionFlags.NONE,
                             GLib.OptionArg.NONE, "Use Dark mode", None)
        self.add_main_option("light", ord("l"), GLib.OptionFlags.NONE,
                             GLib.OptionArg.NONE, "Use Light mode", None)
        self.add_main_option("verinfo", ord("i"), GLib.OptionFlags.NONE,
                             GLib.OptionArg.NONE, "Advanced version info", None)
        self.add_main_option("verbose", ord("v"), GLib.OptionFlags.NONE,
                             GLib.OptionArg.NONE, "Make it scream louder", None)

    @staticmethod
    def darker():
        """Switch to Dark mode."""
        settings = Gtk.Settings.get_default()
        settings.set_property("gtk-application-prefer-dark-theme", True)
        return True

    def do_activate(self):
        """Activate the application."""

        def setup_actions(window):
            """Setup the Gio actions for the application."""
            quit_action = Gio.SimpleAction.new("quit", None)
            quit_action.connect("activate", self.on_quit)
            self.add_action(quit_action)

            about_action = Gio.SimpleAction.new("about", None)
            about_action.connect("activate", window.on_about)
            self.add_action(about_action)

            random_word_action = Gio.SimpleAction.new("random-word", None)
            random_word_action.connect("activate", window.on_random_word)
            self.add_action(random_word_action)

            paste_search_action = Gio.SimpleAction.new("paste-search", None)
            paste_search_action.connect("activate", window.on_paste_search)
            self.add_action(paste_search_action)

            search_selected_action = Gio.SimpleAction.new("search-selected", None)
            search_selected_action.connect("activate", window.on_search_selected)
            self.add_action(search_selected_action)

            self.add_accelerator('<Primary>s', 'app.search-selected', None)
            self.add_accelerator('<Primary>r', 'app.random-word', None)
            self.add_accelerator('<Primary><Shift>v', 'app.paste-search', None)

        win = self.props.active_window
        if not win:
            win = ReoGtkWindow(
                application=self,
                dark=self.dark,
                title='Reo',
                icon_name='accesories-dictionary'
            )
            setup_actions(win)

        win.present()

    def do_command_line(self, command_line):
        """Parse commandline arguments."""
        options = command_line.get_options_dict().end().unpack()
        if "verinfo" in options:
            reo_base.verinfo()
            return 0
        if "verbose" in options:
            reo_base.log_init(True)
        if "dark" in options:
            self.dark = self.darker()
        elif "light" in options:
            self.dark = self.lighter()
        self.activate()
        return 0

    def do_startup(self):
        """Manage startup of the application."""
        Gtk.Application.do_startup(self)

        GLib.set_application_name('Reo')
        GLib.set_prgname('com.github.lastweakness.reo')

    @staticmethod
    def lighter():
        """Switch to Light mode."""
        settings = Gtk.Settings.get_default()
        settings.set_property("gtk-application-prefer-dark-theme", False)
        return False

    def on_quit(self, _action, _param):
        """Quit the application."""
        self.quit()


def main():
    """Launch the application."""
    app = Application()
    return app.run(sys.argv)
