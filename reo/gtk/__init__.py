#!/usr/bin/python
"""
Reo is a dictionary application made with Python and Gtk+3.

It's a simple script basically. It uses existing tools and as such, easily
works across most Linux distributions without any changes.
"""

import argparse  # for CommandLine-Interface (CLI).
import configparser
import logging
import lzma
import os
import random  # for Random Words
import sys
import threading

from shutil import which  # for checks.

from reo import reo_base, utils

# Readying ArgParser
PARSER = argparse.ArgumentParser()  # declare parser as the ArgumentParser used
exc_group = PARSER.add_mutually_exclusive_group()
exc_group.add_argument("-c", "--check", action="store_true", help="Basic dependency checks.")
exc_group.add_argument("-i", "--verinfo", action="store_true", help="Advanced Version Info")
exc_group.add_argument("-gd", "--dark", action="store_true", help="Use GNOME dark theme")
exc_group.add_argument("-gl", "--light", action="store_true", help="Use GNOME light theme")
PARSER.add_argument("-v", "--verbose", action="store_true", help="Make it scream louder")
PARSED = PARSER.parse_args()
# logging is the most important. You have to let users know everything.
if PARSED.verbose:
    DEBUG = True
else:
    DEBUG = False

CUSTOM_DEF_FOLD = utils.CDEF_FOLD
REO_CONFIG = utils.CONFIG_FILE
REO_VERSION = utils.VERSION

try:
    import gi  # this is the GObject stuff needed for GTK+
    gi.require_version('Gtk', '3.0')  # inform the PC that we need GTK+ 3.
    from gi.repository import Gtk  # this is the GNOME depends
    from gi.repository import Gdk
    if PARSED.check:
        print("PyGObject bindings working")
except ImportError as import_error:
    print("Importing GObject failed!")
    if not PARSED.check:
        print("Confirm all dependencies by running Reo with '--check' parameter.\n" + str(import_error))
        sys.exit(1)
    elif PARSED.check:
        print("Install GObject bindings.\n"
              "For Ubuntu, Debian, etc:\n"
              "'sudo apt install python3-gobject'\n"
              "From extra repo for Arch Linux:\n"
              "'yay -S python-gobject' or 'sudo pacman -S python-gobject'\n"
              "Thanks for trying this out!")

BUILDER = Gtk.Builder()
DARK = False
MAX_HIDE = False
LIVE_SEARCH = False


def darker():
    """Switch to Dark mode."""
    settings = Gtk.Settings.get_default()
    settings.set_property("gtk-application-prefer-dark-theme", True)
    return True


def lighter():
    """Switch to Light mode."""
    settings = Gtk.Settings.get_default()
    settings.set_property("gtk-application-prefer-dark-theme", False)
    return False


CUSTOM_DEF_ENABLE = True
reo_base.fold_gen()
CONFIG = configparser.ConfigParser()
if not os.path.exists(REO_CONFIG):
    CONFIG['General'] = {'LiveSearch': 'no',
                         'CustomDefinitions': 'yes',
                         'Debug': 'no',
                         'ForceWordNet31': 'no'}
    CONFIG['UI-gtk'] = {'Theme': 'default',
                        'HideWindowButtonsMaximized': 'no',
                        'DisableCSD': 'no'}
    utils.save_settings(CONFIG)
with open(REO_CONFIG, 'r') as CONFIG_FILE:
    CONFIG.read_file(CONFIG_FILE)


def window_call():
    """Call the window."""
    window = BUILDER.get_object('window')  # main window
    search_box = BUILDER.get_object('search_entry')  # Search box
    header = BUILDER.get_object('header')  # HeaderBar
    header.set_show_close_button(True)
    if os.environ.get('GTK_CSD') == '0' and os.environ.get('XDG_SESSION_TYPE') != 'wayland':
        head_label = BUILDER.get_object('head_label')
        titles = BUILDER.get_object('titles')
        titles.set_margin_end(0)
        titles.set_margin_start(0)
        head_label.destroy()
    pref_box = BUILDER.get_object('pref_buttonbox')
    pref_box.destroy()
    window.set_role('Reo')
    window.set_title('Reo')
    search_box.grab_focus()
    window.show_all()


def load_settings():
    """Load all settings from the config file."""
    global MAX_HIDE, LIVE_SEARCH, WN_VERSION, WN_CHECK_ONCE, CUSTOM_DEF_ENABLE, DEBUG, DARK
    live_check = BUILDER.get_object('live_check')
    custom_def_check = BUILDER.get_object('custom_def_check')
    debug_check = BUILDER.get_object('debug_check')
    force_wn_31 = BUILDER.get_object('force_wn_31')
    light_radio = BUILDER.get_object('light_radio')
    dark_radio = BUILDER.get_object('dark_radio')
    default_radio = BUILDER.get_object('default_radio')
    max_hide_check = BUILDER.get_object('max_hide_check')
    no_csd_check = BUILDER.get_object('no_csd_check')
    live_check.set_active(CONFIG.getboolean('General', 'LiveSearch'))
    LIVE_SEARCH = CONFIG.getboolean('General', 'LiveSearch')
    custom_def_check.set_active(CONFIG.getboolean('General', 'CustomDefinitions'))
    CUSTOM_DEF_ENABLE = CONFIG.getboolean('General', 'CustomDefinitions')
    debug_check.set_active(CONFIG.getboolean('General', 'Debug'))
    if not PARSED.verbose:
        DEBUG = CONFIG.getboolean('General', 'Debug')
    force_wn_31.set_active(CONFIG.getboolean('General', 'ForceWordNet31'))
    if CONFIG.getboolean('General', 'ForceWordNet31'):
        logging.info("Using WordNet 3.1 as per local config")
        WN_VERSION = '3.1'
        WN_CHECK_ONCE = True
    if CONFIG['UI-gtk']['Theme'] == "default":
        default_radio.set_active(True)
    elif CONFIG['UI-gtk']['Theme'] == "dark":
        dark_radio.set_active(True)
        DARK = darker()
    elif CONFIG['UI-gtk']['Theme'] == "light":
        light_radio.set_active(True)
        DARK = lighter()
    max_hide_check.set_active(CONFIG.getboolean('UI-gtk', 'HideWindowButtonsMaximized'))
    MAX_HIDE = CONFIG.getboolean('UI-gtk', 'HideWindowButtonsMaximized')
    no_csd_check.set_active(CONFIG.getboolean('UI-gtk', 'DisableCSD'))


def apply_settings():
    """Apply the settings globally."""
    global LIVE_SEARCH, MAX_HIDE, WN_VERSION, WN_CHECK_ONCE, CUSTOM_DEF_ENABLE, DEBUG, DARK
    live_check = BUILDER.get_object('live_check')
    custom_def_check = BUILDER.get_object('custom_def_check')
    debug_check = BUILDER.get_object('debug_check')
    force_wn_31 = BUILDER.get_object('force_wn_31')
    light_radio = BUILDER.get_object('light_radio')
    dark_radio = BUILDER.get_object('dark_radio')
    default_radio = BUILDER.get_object('default_radio')
    max_hide_check = BUILDER.get_object('max_hide_check')
    no_csd_check = BUILDER.get_object('no_csd_check')
    CONFIG.set('General', 'LiveSearch', utils.boot_to_str(live_check.get_active()))
    LIVE_SEARCH = live_check.get_active()
    CONFIG.set('General', 'CustomDefinitions', utils.boot_to_str(custom_def_check.get_active()))
    CUSTOM_DEF_ENABLE = custom_def_check.get_active()
    CONFIG.set('General', 'Debug', utils.boot_to_str(debug_check.get_active()))
    if not PARSED.verbose:
        DEBUG = debug_check.get_active()
    CONFIG.set('General', 'ForceWordNet31', utils.boot_to_str(force_wn_31.get_active()))
    if force_wn_31.get_active():
        logging.info("Using WordNet 3.1 as per local config")
        WN_VERSION = '3.1'
        WN_CHECK_ONCE = True
    if default_radio.get_active():
        CONFIG.set('UI-gtk', 'Theme', "default")
    elif dark_radio.get_active():
        CONFIG.set('UI-gtk', 'Theme', "dark")
        DARK = darker()
    elif light_radio.get_active():
        CONFIG.set('UI-gtk', 'Theme', "light")
        DARK = lighter()
    CONFIG.set('UI-gtk', 'HideWindowButtonsMaximized', utils.boot_to_str(max_hide_check.get_active()))
    MAX_HIDE = max_hide_check.get_active()
    CONFIG.set('UI-gtk', 'DisableCSD', utils.boot_to_str(no_csd_check.get_active()))
    utils.save_settings(CONFIG)


if not PARSED.verinfo and not PARSED.check:
    GtkSettings = Gtk.Settings.get_default()
    if (GtkSettings.get_property("gtk-application-prefer-dark-theme") or
            GtkSettings.get_property("gtk-theme-name").lower().endswith('-dark')):
        DARK = darker()
    else:
        DARK = lighter()
    PATH = os.path.dirname(os.path.realpath(__file__))
    GLADEFILE = PATH + "/ui/reo.ui"
    # GLADEFILE = "/usr/share/reo/reo.ui"
    BUILDER.add_from_file(GLADEFILE)
    window_call()
    load_settings()
    reo_base.log_init(DEBUG)
    if DEBUG:
        level = logging.DEBUG
    else:
        level = logging.WARNING
    logging.basicConfig(level=level,
                        format="%(asctime)s - [%(levelname)s] [%(threadName)s] (%(module)s:%(lineno)d) %(message)s")
    if PARSED.dark:
        DARK = darker()
    elif PARSED.light:
        DARK = lighter()


WN_VERSION = '3.1'
WN_CHECK_ONCE = False
WN = None


def wn_check():
    """Check if WordNet is properly installed."""
    global WN_VERSION, WN_CHECK_ONCE, WN
    if not WN_CHECK_ONCE:
        WN_VERSION = reo_base.wn_ver_check()
        logging.info("Using WordNet %s", WN_VERSION)
        WN_CHECK_ONCE = True
    WN = str(lzma.open(utils.get_word_list(WN_VERSION), 'r').read()).split('\\n')


def check_bin(bin_to_check):
    """Check presence of required binaries."""
    bin_check = which(bin_to_check)
    print(bin_to_check + " seems to be installed. OK.")
    if bin_check:
        return True
    return False


def print_checks(espeak_ng, dict_check, dictd, wn_dict):
    """Print result of all checks."""
    if espeak_ng and dict_check and dictd and wn_dict:
        print("Everything Looks Perfect!\n"
              "You should be able to run it without any issues!")
    elif espeak_ng and dict_check and dictd and not wn_dict:
        print("WordNet's data file is missing. Re-install 'dict-wn'.\n"
              "For Ubuntu, Debian, etc:\n"
              "'sudo apt install dict-wn'\n"
              "From AUR for Arch Linux:\n"
              "'yay -S dict-wn'\n"
              "Everything else (NOT everything) looks fine...\n"
              "... BUT you can't run it.")
    elif espeak_ng and not dict_check and not dictd and not wn_dict:
        print("dict and dictd (client and server) are missing.. install it."
              "\nFor Ubuntu, Debian, etc:\n"
              "'sudo apt install dictd dict-wn'\n"
              "From community repo for Arch Linux (but WordNet from AUR):\n"
              "'yay -S dictd dict-wn'\n"
              "That should point you in the right direction to getting \n"
              "it to work.")
    elif not espeak_ng and not dict_check and not dictd and not wn_dict:
        print("ALL bits and pieces are Missing...\n"
              "For Ubuntu, Debian, etc:\n"
              "'sudo apt install espeak-ng dictd dict-wn'\n"
              "From community repo for Arch Linux (but WordNet from AUR):\n"
              "'yay -S espeak-ng dictd dict-wn'\n"
              "Go on, get it working now!")
    elif not espeak_ng and dict_check and dictd and wn_dict:
        print("Everything except eSpeak-ng is working...\n"
              "For Ubuntu, Debian, etc:\n"
              "'sudo apt install espeak-ng'\n"
              "From community repo for Arch Linux:\n"
              "'yay -S espeak-ng' or 'sudo pacman -S espeak-ng'\n"
              "It should be alright then.")
    elif not espeak_ng and dict_check and dictd and wn_dict:
        print("eSpeak-ng is missing and WordNet might not work as intended.\n"
              + "Install 'espeak-ng' and re-install the 'dict-wn' package.\n"
              "For Ubuntu, Debian, etc:\n"
              "'sudo apt install espeak-ng dict-wn'\n"
              "From AUR for Arch Linux:\n"
              "'yay -S espeak-ng dict-wn'\n"
              "Everything else (NOT everything) looks fine.\n"
              "Go on, try and run it!")
    elif not espeak_ng and dict_check and dictd and not wn_dict:
        print("eSpeak-ng is missing and WordNet's data file is missing. Re-install 'dict-wn'.\n"
              "For Ubuntu, Debian, etc:\n"
              "'sudo apt install espeak-ng dict-wn'\n"
              "From AUR for Arch Linux:\n"
              "'yay -S espeak-ng dict-wn'\n"
              "Everything else (NOT everything) looks fine BUT you can't run it.")


def dep_check():
    """Check requirements but not thoroughly."""
    espeak_ng = check_bin('espeak-ng')
    dict_check = check_bin('dict')
    dictd = check_bin('dictd')
    if os.path.exists('/usr/share/dictd/wn.dict.dz'):
        print('WordNet database seems to be installed. OK.')
        wn_dict = True
    else:
        logging.warning("WordNet database is not found! Probably won't work.")
        wn_dict = False
    print_checks(espeak_ng, dict_check, dictd, wn_dict)
    sys.exit()


if PARSED.verinfo:
    reo_base.verinfo()
    sys.exit()
if PARSED.check:
    dep_check()

threading.Thread(target=wn_check).start()


class GUI:
    """Define all UI actions and sub-actions."""
    searched = False
    term = None  # Last searched item.
    def_viewer = BUILDER.get_object('def_view')  # Data Space
    search_box = BUILDER.get_object('search_entry')  # Search box

    @staticmethod
    def on_window_destroy(*args):
        """Clear all windows."""
        Gtk.main_quit()

    @staticmethod
    def state_changed(window, state):
        """Detect changes to the window state and adapt."""
        header = BUILDER.get_object('header')
        if MAX_HIDE and not os.environ.get('GTK_CSD') == '0':
            if "MAXIMIZED" in str(state.new_window_state):
                header.set_show_close_button(False)
            else:
                header.set_show_close_button(True)

    @staticmethod
    def pref_launch(*args):
        """Open Preferences Window."""
        pref_dialog = BUILDER.get_object('pref_dialog')
        response = pref_dialog.run()
        load_settings()
        if response in (Gtk.ResponseType.DELETE_EVENT, Gtk.ResponseType.CANCEL):
            pref_dialog.hide()
        elif response == Gtk.ResponseType.OK:
            pref_dialog.hide()

    def apply_click(self, *args):
        """Apply settings only."""
        apply_settings()
        self.search_click(pass_check=True)

    def ok_click(self, *args):
        """Apply settings and hide dialog."""
        pref_dialog = BUILDER.get_object('pref_dialog')
        pref_dialog.response(-5)
        apply_settings()
        self.search_click(pass_check=True)

    @staticmethod
    def cancel_button_clicked(*args):
        """Hide settings dialog."""
        pref_dialog = BUILDER.get_object('pref_dialog')
        pref_dialog.response(-6)

    @staticmethod
    def icon_press(*args):
        """Open About Window."""
        about = BUILDER.get_object('aboutReo')
        about.set_version(REO_VERSION)
        response = about.run()
        if response in (Gtk.ResponseType.DELETE_EVENT, Gtk.ResponseType.CANCEL):
            about.hide()

    def sst(self, *args):
        """Search selected text."""
        text = Gtk.Clipboard.get(Gdk.SELECTION_PRIMARY).wait_for_text()
        text = text.replace('-\n         ', '-').replace('\n', ' ')
        text = text.replace('         ', '')
        self.search_box.set_text(text)
        if not text == '' and not text.isspace():
            self.search_click()
            self.search_box.grab_focus()

    def paste_search(self, *args):
        """Search text in clipboard."""
        text = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD).wait_for_text()
        self.search_box.set_text(text)
        if not text == '' and not text.isspace():
            self.search_click()
            self.search_box.grab_focus()

    @staticmethod
    def new_ced(title, primary, secondary):
        """Show error dialog."""
        large_ced_text = BUILDER.get_object('large_ced_text')
        small_ced_text = BUILDER.get_object('small_ced_text')
        ced = BUILDER.get_object('ced')
        ced.set_title(title)
        large_ced_text.set_label(primary)
        small_ced_text.set_label(secondary)
        response = ced.run()
        if response in (Gtk.ResponseType.DELETE_EVENT, Gtk.ResponseType.OK):
            ced.hide()

    def search_click(self, search_button=None, pass_check=False):
        """Pass data to search function and set TextView data."""
        text = self.search_box.get_text().strip()
        except_list = ['fortune -a', 'cowfortune']
        if not text == self.term or pass_check or text in except_list:
            self.def_viewer.get_buffer().set_text("")
            self.term = text
            if not text.strip() == '':
                last_iter = self.def_viewer.get_buffer().get_end_iter()
                out = self.search(text)
                if out is not None:
                    self.def_viewer.get_buffer().insert_markup(last_iter, out, -1)

    def search(self, search_text):
        """Clean input text, give errors and pass data to reactor."""
        text = search_text.strip().strip('<>"-?`![](){}/\\:;,*').rstrip("'")
        if not text == '' and not text.isspace():
            return self.reactor(text)
        logging.error("Invalid Characters.")
        self.new_ced('Error: Invalid Input!', 'Invalid Characters!',
                     "Reo thinks that your input was actually \njust a bunch of useless characters."
                     "\nSo, 'Invalid Characters' error!")
        return None

    def reactor(self, text):
        """Check easter eggs and set variables."""
        if DARK:
            sencol = "cyan"  # Color of sentences in Dark mode
            wordcol = "lightgreen"  # Color of: Similar Words,
#                                     Synonyms and Antonyms.
        else:
            sencol = "blue"  # Color of sentences in regular
            wordcol = "green"  # Color of: Similar Words, Synonyms, Antonyms.
        skip = ['00-database-allchars', '00-database-info', '00-database-long', '00-database-short', '00-database-url']
        if text in skip:
            return f"<tt> Running Reo with WordNet {WN_VERSION}</tt>"
        if text == 'fortune -a':
            return reo_base.fortune()
        if text == 'cowfortune':
            return reo_base.cowfortune()
        if text in ('crash now', 'close now'):
            Gtk.main_quit()
            return None
        if text == 'reo':
            reo_def = str("<tt>Pronunciation: <b>/ɹˈiːəʊ/</b>\n  <b>Reo</b> ~ <i>Japanese Word</i>\n  <b>1:</b> Name "
                          "of this application, chosen kind of at random.\n  <b>2:</b> Japanese word meaning 'Wise"
                          f" Center'\n <b>Similar Words:</b>\n <i><span foreground=\"{wordcol}\">  ro, "
                          "re, roe, redo, reno, oreo, ceo, leo, neo, rho, rio, reb, red, ref, rem, rep, res,"
                          " ret, rev, rex</span></i></tt>")
            return reo_def
        if text and not text.isspace():
            self.searched = True
            return self.generator(text, wordcol, sencol)
        return None

    @staticmethod
    def custom_def(text, wordcol, sencol):
        """Present custom definition when available."""
        with open(CUSTOM_DEF_FOLD + '/' + text, 'r') as def_file:
            custom_def_read = def_file.read()
            re_list = {"<i>($WORDCOL)</i>": wordcol, "<i>($SENCOL)</i>": sencol,
                       "($WORDCOL)": wordcol, "($SENCOL)": sencol,
                       "$WORDCOL": wordcol, "$SENCOL": sencol}
            for i, j in re_list.items():
                custom_def_read = custom_def_read.replace(i, j)
            if "\n[warninghide]" in custom_def_read:
                custom_def_read = custom_def_read.replace("\n[warninghide]", "")
                return custom_def_read
            return(custom_def_read + '\n<span foreground="#e6292f">NOTE: This is a Custom definition. No one is to be'
                   ' held responsible for errors in this.</span>')

    def generator(self, text, wordcol, sencol):
        """Check if custom definition exists."""
        if os.path.exists(CUSTOM_DEF_FOLD + '/' + text.lower()) and CUSTOM_DEF_ENABLE:
            return self.custom_def(text, wordcol, sencol)
        return reo_base.data_obtain(text, wordcol, sencol, "pango")

    @staticmethod
    def ced_ok(*args):
        """Generate OK response from error dialog."""
        ced = BUILDER.get_object('ced')
        ced.response(Gtk.ResponseType.OK)

    def random_word(self, *args):
        """Choose a random word and pass it to the search box."""
        rw = random.choice(WN)
        self.search_box.set_text(rw.strip())
        self.search_click()
        self.search_box.grab_focus()

    def clear(self, *args):
        """Clear text in the Search box and the Data space."""
        self.search_box.set_text("")
        self.def_viewer.get_buffer().set_text("")

    def audio(self, *args):
        """Say the search entry out loud with espeak speech synthesis."""
        speed = '120'  # To change eSpeak-ng audio speed.
        text = self.search_box.get_text().strip()
        if self.searched and not text == '':
            reo_base.read_term(self.search_box.get_text().strip(), speed)
        elif text == '' or text.isspace():
            self.new_ced("Umm..?", "Umm..?", "Reo can't find any text there! You sure \nyou typed something?")
        elif not self.searched:
            self.new_ced("Sorry!!", "Sorry!!",
                         "I'm sorry but you have to do a search first \nbefore trying to  listen to it."
                         " I mean, Reo \nis <b>NOT</b> a Text-To-Speech Software!")

    def changed(self, *args):
        """Detect changes to Search box and clean or do live searching."""
        self.searched = False
        self.search_box.set_text(self.search_box.get_text().replace('\n', ' '))
        self.search_box.set_text(self.search_box.get_text().replace('         ', ''))
        if LIVE_SEARCH:
            self.search_click()

    @staticmethod
    def quit(menu_quit):
        """Quit using menu."""
        Gtk.main_quit()


def main():
    """Run the Gtk UI."""
    BUILDER.connect_signals(GUI())
    Gtk.main()


if __name__ == '__main__':
    main()
