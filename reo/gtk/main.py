import sys

import gi
from gi.repository import Gio
from gi.repository import Gtk

from .window import ReoGtkWindow

gi.require_version("Gtk", "3.0")


class Application(Gtk.Application):
    def __init__(self):
        """Initialize the application."""

        super().__init__(
            application_id="com.github.lastweakness.reo-gtk",
            flags=Gio.ApplicationFlags.FLAGS_NONE,
        )

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

            search_selected_action = Gio.SimpleAction.new(
                "search-selected", None)
            search_selected_action.connect("activate",
                                           window.on_search_selected)
            self.add_action(search_selected_action)

        win = self.props.active_window
        if not win:
            win = ReoGtkWindow(application=self)
            setup_actions(win)

        win.present()

    def on_quit(self, _action, _param):
        """Quit the application."""
        self.quit()


def main():
    """Launch the application."""
    app = Application()
    return app.run(sys.argv)
