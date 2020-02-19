#!/usr/bin/python
"""
Reo is a dictionary application made with Python and Gtk+3.

It's a simple script basically. It uses existing tools and as such, easily
works across most Linux distributions without any changes.
"""

import sys
import logging
import argparse  # for CommandLine-Interface (CLI).
import os
from shutil import which  # for checks.
import random  # for Random Words
import lzma
from reo import reo_base, utils
import threading
import configparser

# Readying ArgParser
parser = argparse.ArgumentParser()  # declare parser as the ArgumentParser used
exc_group = parser.add_mutually_exclusive_group()
exc_group.add_argument("-c", "--check", action="store_true", help="Basic dependency checks.")
exc_group.add_argument("-i", "--verinfo", action="store_true", help="Advanced Version Info")
exc_group.add_argument("-gd", "--dark", action="store_true", help="Use GNOME dark theme")
exc_group.add_argument("-gl", "--light", action="store_true", help="Use GNOME light theme")
parser.add_argument("-v", "--verbose", action="store_true", help="Make it scream louder")
parsed = parser.parse_args()
# logging is the most important. You have to let users know everything.
if parsed.verbose:
    level = logging.DEBUG
else:
    level = logging.WARNING
logging.basicConfig(level=level,
                    format="%(asctime)s - [%(levelname)s] [%(threadName)s] (%(module)s:%(lineno)d) %(message)s")

custom_def_fold = utils.CDEF_FOLD
reo_config = utils.CONFIG_FILE
reo_version = utils.VERSION

try:
    import gi  # this is the GObject stuff needed for GTK+
    gi.require_version('Gtk', '3.0')  # inform the PC that we need GTK+ 3.
    from gi.repository import Gtk  # this is the GNOME depends
    from gi.repository import Gdk
    if parsed.check:
        print("PyGObject bindings working")
except ImportError as import_error:
    logging.fatal("Importing GObject failed!")
    if not parsed.check:
        print("Confirm all dependencies by running Reo with '--check' parameter.\n" + str(import_error))
        sys.exit(1)
    elif parsed.check:
        print("Install GObject bindings.\n"
              "For Ubuntu, Debian, etc:\n"
              "'sudo apt install python3-gobject'\n"
              "From extra repo for Arch Linux:\n"
              "'yay -S python-gobject' or 'sudo pacman -S python-gobject'\n"
              "Thanks for trying this out!")

builder = Gtk.Builder()
dark = False
sb = None
viewer = None
max_hide = False
live_search = False
debug = False


def darker():
    """Switch to Dark mode."""
    global dark
    settings = Gtk.Settings.get_default()
    settings.set_property("gtk-application-prefer-dark-theme", True)
    dark = True


def lighter():
    """Switch to Light mode."""
    global dark
    settings = Gtk.Settings.get_default()
    settings.set_property("gtk-application-prefer-dark-theme", False)
    dark = False


custom_def_enable = True
reo_base.fold_gen()
config = configparser.ConfigParser()
if not os.path.exists(reo_config):
    config['General'] = {'LiveSearch': 'no',
                         'CustomDefinitions': 'yes',
                         'Debug': 'no',
                         'ForceWordNet31': 'no'}
    config['UI-gtk'] = {'Theme': 'default',
                        'HideWindowButtonsMaximized': 'no',
                        'DisableCSD': 'no'}
    utils.save_settings(config)
with open(reo_config, 'r') as config_file:
    config.read_file(config_file)


def window_call():
    """Call the window."""
    global sb, viewer
    window = builder.get_object('window')  # main window
    sb = builder.get_object('search_entry')  # Search box
    viewer = builder.get_object('def_view')  # Data Space
    header = builder.get_object('header')  # HeaderBar
    header.set_show_close_button(True)
    if((os.environ.get('GTK_CSD') == '0') and
       (os.environ.get('XDG_SESSION_TYPE') != 'wayland')):
        head_label = builder.get_object('head_label')
        titles = builder.get_object('titles')
        titles.set_margin_end(0)
        titles.set_margin_start(0)
        head_label.destroy()
    pref_box = builder.get_object('pref_buttonbox')
    pref_box.destroy()
    window.set_role('Reo')
    window.set_title('Reo')
    sb.grab_focus()
    window.show_all()


def load_settings():
    """Load all settings from the config file."""
    global max_hide, live_search, wn_version, wn_check_once, custom_def_enable, debug
    live_check = builder.get_object('live_check')
    custom_def_check = builder.get_object('custom_def_check')
    debug_check = builder.get_object('debug_check')
    force_wn_31 = builder.get_object('force_wn_31')
    light_radio = builder.get_object('light_radio')
    dark_radio = builder.get_object('dark_radio')
    default_radio = builder.get_object('default_radio')
    max_hide_check = builder.get_object('max_hide_check')
    no_csd_check = builder.get_object('no_csd_check')
    live_check.set_active(config.getboolean('General', 'LiveSearch'))
    live_search = config.getboolean('General', 'LiveSearch')
    custom_def_check.set_active(config.getboolean('General', 'CustomDefinitions'))
    custom_def_enable = config.getboolean('General', 'CustomDefinitions')
    debug_check.set_active(config.getboolean('General', 'Debug'))
    debug = config.getboolean('General', 'Debug')
    force_wn_31.set_active(config.getboolean('General', 'ForceWordNet31'))
    if config.getboolean('General', 'ForceWordNet31'):
        logging.info("Using WordNet 3.1 as per local config")
        wn_version = '3.1'
        wn_check_once = True
    if config['UI-gtk']['Theme'] == "default":
        default_radio.set_active(True)
    elif config['UI-gtk']['Theme'] == "dark":
        dark_radio.set_active(True)
        darker()
    elif config['UI-gtk']['Theme'] == "light":
        light_radio.set_active(True)
        lighter()
    max_hide_check.set_active(config.getboolean('UI-gtk', 'HideWindowButtonsMaximized'))
    max_hide = config.getboolean('UI-gtk', 'HideWindowButtonsMaximized')
    no_csd_check.set_active(config.getboolean('UI-gtk', 'DisableCSD'))


def apply_settings():
    """Apply the settings globally."""
    global live_search, max_hide, wn_version, wn_check_once, custom_def_enable, debug
    live_check = builder.get_object('live_check')
    custom_def_check = builder.get_object('custom_def_check')
    debug_check = builder.get_object('debug_check')
    force_wn_31 = builder.get_object('force_wn_31')
    light_radio = builder.get_object('light_radio')
    dark_radio = builder.get_object('dark_radio')
    default_radio = builder.get_object('default_radio')
    max_hide_check = builder.get_object('max_hide_check')
    no_csd_check = builder.get_object('no_csd_check')
    config.set('General', 'LiveSearch', utils.boot_to_str(live_check.get_active()))
    live_search = live_check.get_active()
    config.set('General', 'CustomDefinitions', utils.boot_to_str(custom_def_check.get_active()))
    custom_def_enable = custom_def_check.get_active()
    config.set('General', 'Debug', utils.boot_to_str(debug_check.get_active()))
    debug = debug_check.get_active()
    config.set('General', 'ForceWordNet31', utils.boot_to_str(force_wn_31.get_active()))
    if force_wn_31.get_active():
        logging.info("Using WordNet 3.1 as per local config")
        wn_version = '3.1'
        wn_check_once = True
    if default_radio.get_active():
        config.set('UI-gtk', 'Theme', "default")
    elif dark_radio.get_active():
        config.set('UI-gtk', 'Theme', "dark")
        darker()
    elif light_radio.get_active():
        config.set('UI-gtk', 'Theme', "light")
        lighter()
    config.set('UI-gtk', 'HideWindowButtonsMaximized', utils.boot_to_str(max_hide_check.get_active()))
    max_hide = max_hide_check.get_active()
    config.set('UI-gtk', 'DisableCSD', utils.boot_to_str(no_csd_check.get_active()))
    utils.save_settings(config)


if not parsed.verinfo and not parsed.check:
    GtkSettings = Gtk.Settings.get_default()
    if (GtkSettings.get_property("gtk-application-prefer-dark-theme") or
            GtkSettings.get_property("gtk-theme-name").lower().endswith('-dark')):
        darker()
    else:
        lighter()
    PATH = os.path.dirname(os.path.realpath(__file__))
    GLADEFILE = PATH + "/ui/reo.ui"
    # GLADEFILE = "/usr/share/reo/reo.ui"
    builder.add_from_file(GLADEFILE)
    window_call()
    load_settings()
    if parsed.dark:
        darker()
    elif parsed.light:
        lighter()


wn_version = '3.1'
wn_check_once = False
wn = None
searched = None


def wn_check():
    """Check if WordNet is properly installed."""
    global wn_version, wn_check_once, wn
    if not wn_check_once:
        wn_version = reo_base.wn_ver_check()
        logging.info(f"Using WordNet {wn_version}")
        wn_check_once = True
    wn = str(lzma.open(utils.get_word_list(wn_version), 'r').read()).split('\\n')


def check_bin(bin_to_check):
    """Check presence of required binaries."""
    try:
        which(bin_to_check)
        print(bin_to_check + " seems to be installed. OK.")
        bin_check = True
    except Exception as ex:
        logging.fatal(f"{bin_to_check} is not installed! Dependency missing!{str(ex)}")
        bin_check = False
    return bin_check


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


if parsed.verinfo:
    reo_base.verinfo()
    sys.exit()
if parsed.check:
    dep_check()
term = None  # Last searched item.
threading.Thread(target=wn_check).start()


class GUI:
    """Define all UI actions and sub-actions."""

    @staticmethod
    def on_window_destroy(window):
        """Clear all windows."""
        Gtk.main_quit()

    @staticmethod
    def state_changed(window, state):
        """Detect changes to the window state and adapt."""
        header = builder.get_object('header')
        if max_hide and not os.environ.get('GTK_CSD') == '0':
            if "MAXIMIZED" in str(state.new_window_state):
                header.set_show_close_button(False)
            else:
                header.set_show_close_button(True)

    @staticmethod
    def pref_launch(pref_item):
        """Open Preferences Window."""
        pref_dialog = builder.get_object('pref_dialog')
        response = pref_dialog.run()
        load_settings()
        if response in (Gtk.ResponseType.DELETE_EVENT, Gtk.ResponseType.CANCEL):
            pref_dialog.hide()
        elif response == Gtk.ResponseType.OK:
            pref_dialog.hide()

    def apply_click(self, apply_button):
        """Apply settings only."""
        apply_settings()
        self.search_click(pass_check=True)

    def ok_click(self, ok_button):
        """Apply settings and hide dialog."""
        pref_dialog = builder.get_object('pref_dialog')
        pref_dialog.response(-5)
        apply_settings()
        self.search_click(pass_check=True)

    @staticmethod
    def cancel_button_clicked(cancel_button):
        """Hide settings dialog."""
        pref_dialog = builder.get_object('pref_dialog')
        pref_dialog.response(-6)

    @staticmethod
    def icon_press(menu_about):
        """Open About Window."""
        about = builder.get_object('aboutReo')
        about.set_version(reo_version)
        response = about.run()
        if response in (Gtk.ResponseType.DELETE_EVENT, Gtk.ResponseType.CANCEL):
            about.hide()

    def sst(self, menu_sst):
        """Search selected text."""
        text = Gtk.Clipboard.get(Gdk.SELECTION_PRIMARY).wait_for_text()
        text = text.replace('-\n         ', '-').replace('\n', ' ')
        text = text.replace('         ', '')
        sb.set_text(text)
        if not text == '' and not text.isspace():
            self.search_click()
            sb.grab_focus()

    def paste_search(self, menu_paste):
        """Search text in clipboard."""
        text = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD).wait_for_text()
        sb.set_text(text)
        if not text == '' and not text.isspace():
            self.search_click()
            sb.grab_focus()

    @staticmethod
    def new_ced(title, primary, secondary):
        """Show error dialog."""
        large_ced_text = builder.get_object('large_ced_text')
        small_ced_text = builder.get_object('small_ced_text')
        ced = builder.get_object('ced')
        ced.set_title(title)
        large_ced_text.set_label(primary)
        small_ced_text.set_label(secondary)
        response = ced.run()
        if response in (Gtk.ResponseType.DELETE_EVENT, Gtk.ResponseType.OK):
            ced.hide()

    def search_click(self, search_button=None, pass_check=False):
        """Pass data to search function and set TextView data."""
        global term
        text = sb.get_text().strip()
        except_list = ['fortune -a', 'cowfortune']
        if not text == term or pass_check or text in except_list:
            viewer.get_buffer().set_text("")
            if not text.strip() == '':
                last_iter = viewer.get_buffer().get_end_iter()
                out = self.search(text)
                term = text
                viewer.get_buffer().insert_markup(last_iter, out, -1)

    def search(self, search_box):
        """Clean input text, give errors and pass data to reactor."""
        if (not search_box.strip('<>"?`![]()/\\:;,') == '' and
                not search_box.isspace() and not search_box == ''):
            text = search_box.strip().strip('<>"?`![]()/\\:;,*')
            return self.reactor(text)
        elif (search_box.strip('<>"?`![]()/\\:;,') == '' and
              not search_box.isspace() and
              not search_box == ''):
            logging.error("Invalid Characters.")
            self.new_ced('Error: Invalid Input!', 'Invalid Characters!',
                         "Reo thinks that your input was actually \njust a bunch of useless characters."
                         "\nSo, 'Invalid Characters' error!")

    def reactor(self, text):
        """Check easter eggs and set variables."""
        global searched
        if dark:
            sencol = "cyan"  # Color of sentences in Dark mode
            wordcol = "lightgreen"  # Color of: Similar Words,
#                                     Synonyms and Antonyms.
        else:
            sencol = "blue"  # Color of sentences in regular
            wordcol = "green"  # Color of: Similar Words, Synonyms, Antonyms.
        skip = ['00-database-allchars', '00-database-info', '00-database-long',
                '00-database-short', '00-database-url']
        if text in skip:
            return f"<tt> Running Reo with WordNet {wn_version}</tt>"
        elif text == 'fortune -a':
            return reo_base.fortune()
        elif text == 'cowfortune':
            return reo_base.cowfortune()
        elif text in ('crash now', 'close now'):
            Gtk.main_quit()
        elif text == 'reo':
            reo_def = str("<tt>Pronunciation: <b>/ɹˈiːəʊ/</b>\n  <b>Reo</b> ~ <i>Japanese Word</i>\n  <b>1:</b> Name "
                          "of this application, chosen kind of at random.\n  <b>2:</b> Japanese word meaning 'Wise"
                          f" Center'\n <b>Similar Words:</b>\n <i><span foreground=\"{wordcol}\">  ro, "
                          "re, roe, redo, reno, oreo, ceo, leo, neo, rho, rio, reb, red, ref, rem, rep, res,"
                          " ret, rev, rex</span></i></tt>")
            return reo_def
        if text and not text.isspace():
            searched = True
            return self.generator(text, wordcol, sencol)

    @staticmethod
    def custom_def(text, wordcol, sencol):
        """Present custom definition when available."""
        with open(custom_def_fold + '/' + text, 'r') as def_file:
            custom_def_read = def_file.read()
            re_list = {"<i>($WORDCOL)</i>": wordcol, "<i>($SENCOL)</i>": sencol,
                       "($WORDCOL)": wordcol, "($SENCOL)": sencol,
                       "$WORDCOL": wordcol, "$SENCOL": sencol}
            for i, j in re_list.items():
                custom_def_read = custom_def_read.replace(i, j)
            if "\n[warninghide]" in custom_def_read:
                custom_def_read = custom_def_read.replace("\n[warninghide]", "")
                return custom_def_read
            else:
                return(custom_def_read + '\n<span foreground="#e6292f">NOTE: This is a Custom definition. No one'
                       ' is to be held responsible for errors in this.</span>')

    def generator(self, text, wordcol, sencol):
        """Check if custom definition exists."""
        if os.path.exists(custom_def_fold + '/' + text.lower()) and custom_def_enable:
            return self.custom_def(text, wordcol, sencol)
        else:
            return reo_base.data_obtain(text, wordcol, sencol, "pango", debug)

    @staticmethod
    def ced_ok(ced_ok):
        """Generate OK response from error dialog."""
        ced = builder.get_object('ced')
        ced.response(Gtk.ResponseType.OK)

    def random_word(self, menu_rand):
        """Choose a random word and pass it to the search box."""
        rw = random.choice(wn)
        sb.set_text(rw.strip())
        self.search_click()
        sb.grab_focus()

    @staticmethod
    def clear(clear_button):
        """Clear text in the Search box and the Data space."""
        sb.set_text("")
        viewer.get_buffer().set_text("")

    def audio(self, audio_button):
        """Say the search entry out loud with espeak speech synthesis."""
        speed = '120'  # To change eSpeak-ng audio speed.
        text = sb.get_text().strip()
        if searched and not text == '':
            reo_base.read_term(speed, sb.get_text().strip())
        elif text == '' or text.isspace():
            self.new_ced("Umm..?", "Umm..?", "Reo can't find any text there! You sure \nyou typed something?")
        elif not searched:
            self.new_ced("Sorry!!", "Sorry!!",
                         "I'm sorry but you have to do a search first \nbefore trying to  listen to it."
                         " I mean, Reo \nis <b>NOT</b> a Text-To-Speech Software!")

    def changed(self, search_entry):
        """Detect changes to Search box and clean or do live searching."""
        global searched
        searched = False
        sb.set_text(sb.get_text().replace('\n', ' '))
        sb.set_text(sb.get_text().replace('         ', ''))
        if live_search:
            self.search_click()

    @staticmethod
    def quit(menu_quit):
        """Quit using menu."""
        Gtk.main_quit()

    @staticmethod
    def save_def(menu_save):
        """Save definition using FileChooser dialog."""
        def_dialog = Gtk.FileChooserDialog("Save Definition as...", builder.get_object('window'),
                                           Gtk.FileChooserAction.SAVE,
                                           ("Save", Gtk.ResponseType.OK, "Cancel", Gtk.ResponseType.CANCEL))
        response = def_dialog.run()
        if response in (Gtk.ResponseType.DELETE_EVENT, Gtk.ResponseType.CANCEL):
            def_dialog.hide()
        elif response == Gtk.ResponseType.OK:
            with open(def_dialog.get_filename(), 'w') as sf:
                start_iter = viewer.get_buffer().get_start_iter()
                last_iter = viewer.get_buffer().get_end_iter()
                sf.write(viewer.get_buffer().get_text(start_iter, last_iter, 'false'))
            def_dialog.hide()


def main():
    """Run the Gtk UI."""
    builder.connect_signals(GUI())
    Gtk.main()


if __name__ == '__main__':
    main()
