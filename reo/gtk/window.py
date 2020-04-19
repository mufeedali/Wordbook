import os
import random

from gi.repository import Gdk, Gtk

from reo import reo_base, utils

PATH = os.path.dirname(__file__)


@Gtk.Template(filename=f'{PATH}/ui/window.ui')
class ReoGtkWindow(Gtk.ApplicationWindow):
    __gtype_name__ = 'ReoGtkWindow'

    def_view = Gtk.Template.Child('def_view')
    search_entry = Gtk.Template.Child('search_entry')
    search_button = Gtk.Template.Child('search_button')
    clear_button = Gtk.Template.Child('clear_button')
    menu_button = Gtk.Template.Child('reo_menu_button')

    term = None
    searched = False
    dark = True
    wn_future = reo_base.get_wn_file()

    def __init__(self, dark=False, **kwargs):
        """Initialize the window."""
        super().__init__(**kwargs)

        builder = Gtk.Builder.new_from_file(f'{PATH}/ui/menu.xml')
        menu = builder.get_object("reo-menu")

        popover = Gtk.Popover.new_from_model(self.menu_button, menu)
        self.menu_button.set_popover(popover)

        self.search_button.connect("clicked", self.on_search_press)
        self.search_entry.connect("activate", self.on_search_press)
        self.clear_button.connect("clicked", self.on_clear_press)

        self.dark = dark

    def on_search_selected(self, _action, _param):
        """Search selected text from inside or outside the window."""
        text = Gtk.Clipboard.get(Gdk.SELECTION_PRIMARY).wait_for_text()
        text = text.replace('-\n         ', '-').replace('\n', ' ')
        text = text.replace('         ', '')
        self.search_entry.set_text(text)
        if not text == '' and not text.isspace():
            self.on_search_press()
            self.search_entry.grab_focus()

    def on_paste_search(self, _action, _param):
        """Search text in clipboard."""
        text = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD).wait_for_text()
        self.search_entry.set_text(text)
        if not text == '' and not text.isspace():
            self.on_search_press()
            self.search_entry.grab_focus()

    def on_random_word(self, _action, _param):
        """Search a random word from the wordlist."""
        self.search_entry.set_text(random.choice(self.wn_future.result()[1]))
        self.on_search_press()
        self.search_entry.grab_focus()

    def on_clear_press(self, _button):
        """Clear all text in the window."""
        self.def_view.get_buffer().set_text("")
        self.search_entry.set_text("")

    def on_search_press(self, _button=None, pass_check=False):
        """Pass data to search function and set TextView data."""
        text = self.search_entry.get_text().strip()
        except_list = ['fortune -a', 'cowfortune']
        if not text == self.term or pass_check or text in except_list:
            self.def_view.get_buffer().set_text("")
            self.term = text
            if not text.strip() == '':
                last_iter = self.def_view.get_buffer().get_end_iter()
                out = self.__search(text)
                if out is not None:
                    self.def_view.get_buffer().insert_markup(last_iter, out, -1)

    def __search(self, search_text):
        """Clean input text, give errors and pass data to reactor."""
        text = search_text.strip().strip('<>".-?`![](){}/\\:;,*').rstrip("'")
        cleaner = ['(', ')', '<', '>']
        for item in cleaner:
            text = text.replace(item, '')
        if not text == '' and not text.isspace():
            return self.__reactor(text)
        dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.OK, 'Invalid Input')
        dialog.format_secondary_text(
            "Reo thinks that your input was actually just a bunch of useless characters. "
            "And so, an 'Invalid Characters' error."
        )
        dialog.run()
        dialog.destroy()
        return None

    def __reactor(self, text):
        """Check easter eggs and set variables."""
        if self.dark:
            sencol = "cyan"  # Color of sentences in Dark mode
            wordcol = "lightgreen"  # Color of: Similar Words,
#                                     Synonyms and Antonyms.
        else:
            sencol = "blue"  # Color of sentences in regular
            wordcol = "green"  # Color of: Similar Words, Synonyms, Antonyms.
        wn_list = [
            '00-database-allchars',
            '00-database-info',
            '00-database-short',
            '00-database-url'
        ]
        if text in wn_list:
            return f"<tt> Running Reo with WordNet {self.wn_future.result()[0]}</tt>"
        if text == 'fortune -a':
            return reo_base.get_fortune()
        if text == 'cowfortune':
            return reo_base.get_cowfortune()
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
            self.searched = True
            return reo_base.generate_definition(text, wordcol, sencol, "pango")
        return None

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
