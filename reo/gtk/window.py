import os
import random

from gi.repository import Gdk, Gtk

from reo import base, utils
from reo.gtk.settings_window import SettingsWindow
from reo.settings import Settings

PATH = os.path.dirname(__file__)


@Gtk.Template(filename=f'{PATH}/ui/window.ui')
class ReoGtkWindow(Gtk.ApplicationWindow):
    __gtype_name__ = 'ReoGtkWindow'

    clear_button = Gtk.Template.Child('clear_button')
    def_view = Gtk.Template.Child('def_view')
    search_entry = Gtk.Template.Child('search_entry')
    search_button = Gtk.Template.Child('search_button')
    speak_button = Gtk.Template.Child('speak_button')
    menu_button = Gtk.Template.Child('reo_menu_button')
    header_bar = Gtk.Template.Child('header_bar')

    term = None
    searched_term = None
    wn_future = base.get_wn_file()

    def __init__(self, **kwargs):
        """Initialize the window."""
        super().__init__(**kwargs)

        builder = Gtk.Builder.new_from_file(f'{PATH}/ui/menu.xml')
        menu = builder.get_object("reo-menu")

        popover = Gtk.Popover.new_from_model(self.menu_button, menu)
        self.menu_button.set_popover(popover)
        self.search_entry.grab_focus()

        self.connect("notify::is-maximized", self.on_state_change)
        self.clear_button.connect("clicked", self.on_clear_press)
        self.search_button.connect("clicked", self.on_search_press)
        self.search_entry.connect("activate", self.on_search_press)
        self.search_entry.connect("changed", self.on_text_change)
        self.speak_button.connect("clicked", self.on_speak_press)

    def on_about(self, _action, _param):
        """Show the about window."""
        about_dialog = Gtk.AboutDialog(
            transient_for=self,
            modal=True
        )
        about_dialog.set_logo_icon_name("accessories-dictionary")
        about_dialog.set_program_name("Reo GTK")
        about_dialog.set_version(utils.VERSION)
        about_dialog.set_comments(
            "Reo is a dictionary application that uses dictd, dict-wn and "
            "eSpeak-ng to provide a complete user interface."
        )
        about_dialog.set_authors(["Mufeed Ali", ])
        about_dialog.set_license_type(Gtk.License.MIT_X11)
        about_dialog.set_website("http://lastweakness.github.io/reo")
        about_dialog.set_copyright("Copyright © 2016-2020 Mufeed Ali")
        about_dialog.connect('response', lambda dialog, response: dialog.destroy())
        about_dialog.present()

    def on_clear_press(self, _button):
        """Clear all text in the window."""
        self.def_view.get_buffer().set_text("")
        self.search_entry.set_text("")

    def on_paste_search(self, _action, _param):
        """Search text in clipboard."""
        text = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD).wait_for_text()
        self.search_entry.set_text(text)
        if not text == '' and not text.isspace():
            self.on_search_press()
            self.search_entry.grab_focus()

    def on_preferences(self, _action, _param):
        """Show settings window."""
        window = SettingsWindow(transient_for=self)
        window.connect("destroy", self.on_preferences_destroy)
        window.load_settings()
        window.present()

    def on_preferences_destroy(self, _window):
        """Refresh view when Preferences window is closed. Only necessary for definition now."""
        if self.searched_term:
            self.on_search_press(pass_check=True)

    def on_random_word(self, _action, _param):
        """Search a random word from the wordlist."""
        self.search_entry.set_text(random.choice(self.wn_future.result()[1]))
        self.on_search_press()
        self.search_entry.grab_focus()

    def on_search_press(self, _button=None, pass_check=False):
        """Pass data to search function and set TextView data."""
        if pass_check:
            text = self.searched_term
        else:
            text = self.search_entry.get_text().strip()
        except_list = ('fortune -a', 'cowfortune')
        if pass_check or not text == self.searched_term or text in except_list:
            self.def_view.get_buffer().set_text("")
            self.searched_term = text
            if not text.strip() == '':
                last_iter = self.def_view.get_buffer().get_end_iter()
                out = self.__search(text)
                if out is not None:
                    self.def_view.get_buffer().insert_markup(last_iter, out, -1)

    def on_search_selected(self, _action, _param):
        """Search selected text from inside or outside the window."""
        text = Gtk.Clipboard.get(Gdk.SELECTION_PRIMARY).wait_for_text()
        text = text.replace('-\n         ', '-').replace('\n', ' ')
        text = text.replace('         ', '')
        self.search_entry.set_text(text)
        if not text == '' and not text.isspace():
            self.on_search_press()
            self.search_entry.grab_focus()

    def on_shortcuts(self, _action, _param):
        """Launch the Keyboard Shortcuts window."""
        builder = Gtk.Builder.new_from_file(f'{PATH}/ui/shortcuts_window.ui')
        builder.get_object("shortcuts").set_transient_for(self)
        builder.get_object("shortcuts").show()

    def on_speak_press(self, _button):
        """Say the search entry out loud with espeak speech synthesis."""
        speed = '120'  # To change eSpeak-ng audio speed.
        text = self.searched_term
        if text:
            base.read_term(text, speed)
        else:
            self._new_error(
                "Do a search first!",
                "You have to search for something first. "
            )

    def on_state_change(self, _window, _state):
        """Detect changes to the window state and adapt."""
        if Settings.get().gtk_max_hide and not os.environ.get('GTK_CSD') == '0':
            if self.props.is_maximized:
                self.header_bar.set_show_close_button(False)
            else:
                self.header_bar.set_show_close_button(True)

    def on_text_change(self, _entry):
        """Detect changes to text and do live search if enabled."""
        if Settings.get().live_search:
            self.on_search_press()

    def _new_error(self, primary_text, seconday_text):
        """Show an error dialog."""
        dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.OK, primary_text)
        dialog.format_secondary_text(seconday_text)
        dialog.run()
        dialog.destroy()

    def __search(self, search_text):
        """Clean input text, give errors and pass data to reactor."""
        text = search_text.strip().strip('<>".-?`![](){}/\\:;,*').rstrip("'")
        cleaner = ['(', ')', '<', '>', '[', ']']
        for item in cleaner:
            text = text.replace(item, '')
        if not text == '' and not text.isspace():
            return self.__reactor(text)
        self._new_error(
            "Invalid Input",
            "Reo thinks that your input was actually just a bunch of useless characters. "
            "And so, an 'Invalid Characters' error."
        )
        self.searched_term = None
        return None

    def __reactor(self, text):
        """Check easter eggs and set variables."""
        if Settings.get().gtk_dark_font:
            sencol = "cyan"  # Color of sentences in Dark mode
            wordcol = "lightgreen"  # Color of: Similar Words,
#                                     Synonyms and Antonyms.
        else:
            sencol = "blue"  # Color of sentences in regular
            wordcol = "green"  # Color of: Similar Words, Synonyms, Antonyms.
        wn_list = (
            '00-database-allchars',
            '00-database-info',
            '00-database-short',
            '00-database-url'
        )
        if text in wn_list:
            return f"<tt> Running Reo with WordNet {self.wn_future.result()[0]}</tt>"
        if text == 'fortune -a':
            return base.get_fortune()
        if text == 'cowfortune':
            return base.get_cowfortune()
        if text == 'reo':
            return str(
                "<tt>Pronunciation: <b>/ɹˈiːəʊ/</b>\n"
                "  <b>Reo</b> ~ <i>Japanese Word</i>\n"
                "  <b>1:</b> Name of this application, chosen kind of at random.\n"
                "  <b>2:</b> Japanese word meaning 'Wise Center'\n"
                " <b>Similar Words:</b>\n"
                f" <i><span foreground=\"{wordcol}\">  ro, re, roe, redo, reno, oreo, ceo, leo, neo, rho, rio, reb,"
                " red, ref, rem, rep, res, ret, rev, rex</span></i></tt>"
            )
        if text in ('crash now', 'close now'):
            self.destroy()
            return None
        if text and not text.isspace():
            return base.generate_definition(text, wordcol, sencol, cdef=Settings.get().cdef, markup="pango")
        return None
