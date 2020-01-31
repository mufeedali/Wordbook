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
mgroup = parser.add_mutually_exclusive_group()
mgroup.add_argument("-c", "--check", action="store_true",
                    help="Basic dependancy checks.")
mgroup.add_argument("-i", "--verinfo", action="store_true",
                    help="Advanced Version Info")
mgroup.add_argument("-gd", "--dark", action="store_true",
                    help="Use GNOME dark theme")
mgroup.add_argument("-gl", "--light", action="store_true",
                    help="Use GNOME light theme")
parser.add_argument("-v", "--verbose", action="store_true",
                    help="Make it scream louder")
parsed = parser.parse_args()
# logging is the most important. You have to let users know everything.
if(parsed.verbose):
    level = logging.DEBUG
else:
    level = logging.WARNING
logging.basicConfig(level=level, format="%(asctime)s - " +
                    "[%(levelname)s] [%(threadName)s] (%(module)s:" +
                    "%(lineno)d) %(message)s")

cdef_fold = utils.CDEF_FOLD
reo_config = utils.CONFIG_FILE
reo_version = utils.VERSION

try:
    import gi  # this is the GObject stuff needed for GTK+
    gi.require_version('Gtk', '3.0')  # inform the PC that we need GTK+ 3.
    import gi.repository.Gtk as Gtk  # this is the GNOME depends
    import gi.repository.Gdk as Gdk
    if parsed.check:
        print("PyGOject bindings working")
except ImportError as ierr:
    logging.fatal("Importing GObject failed!")
    if not parsed.check:
        print("Confirm all dependencies by running " +
              "Reo with '--check' parameter.\n" +
              ierr)
        sys.exit(1)
    elif parsed.check:
        print("Install GObject bindings.\n" +
              "For Ubuntu, Debian, etc:\n" +
              "'sudo apt install python3-gobject'\n" +
              "From extra repo for Arch Linux:\n" +
              "'pacaur -S python-gobject' or 'sudo pacman -S python-gobject'" +
              "\nThanks for trying this out!")
builder = Gtk.Builder()


def darker():
    """Switch to Dark mode."""
    global dark
    settings = Gtk.Settings.get_default()
    settings.set_property("gtk-application-prefer-dark-theme", True)
    current_theme = settings.get_property("gtk-theme-name")
    if not current_theme.endswith('-dark'):
        new_theme = current_theme + "-dark"
        settings.set_property("gtk-theme-name", new_theme)
    dark = True


def lighter():
    """Switch to Light mode."""
    global dark
    settings = Gtk.Settings.get_default()
    settings.set_property("gtk-application-prefer-dark-theme", False)
    current_theme = settings.get_property("gtk-theme-name")
    if current_theme.endswith('-dark'):
        new_theme = current_theme[:-5]
        settings.set_property("gtk-theme-name", new_theme)
    dark = False


cdefenable = True
reo_base.foldGen()
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


def windowcall():
    """Call the window."""
    global sb, viewer
    window = builder.get_object('window')  # main window
    sb = builder.get_object('searchEntry')  # Search box
    viewer = builder.get_object('defView')  # Data Space
    header = builder.get_object('header')  # Headerbar
    header.set_show_close_button(True)
    if((os.environ.get('GTK_CSD') == '0') and
       (os.environ.get('XDG_SESSION_TYPE') != 'wayland')):
        headlabel = builder.get_object('headlabel')
        titles = builder.get_object('titles')
        titles.set_margin_end(0)
        titles.set_margin_start(0)
        headlabel.destroy()
    pbox = builder.get_object('pref_buttonbox')
    pbox.destroy()
    window.set_role('Reo')
    window.set_title('Reo')
    sb.grab_focus()
    window.show_all()


def load_settings():
    """Load all settings from the config file."""
    global maxhide, livesearch, wnver, wncheckonce, cdefenable, debug
    live_check = builder.get_object('live_check')
    cdef_check = builder.get_object('cdef_check')
    debug_check = builder.get_object('debug_check')
    forcewn31 = builder.get_object('forcewn31')
    light_radio = builder.get_object('light_radio')
    dark_radio = builder.get_object('dark_radio')
    default_radio = builder.get_object('default_radio')
    maxhide_check = builder.get_object('maxhide_check')
    nocsd_check = builder.get_object('nocsd_check')
    live_check.set_active(config.getboolean('General', 'LiveSearch'))
    livesearch = config.getboolean('General', 'LiveSearch')
    cdef_check.set_active(config.getboolean('General', 'CustomDefinitions'))
    cdefenable = config.getboolean('General', 'CustomDefinitions')
    debug_check.set_active(config.getboolean('General', 'Debug'))
    debug = config.getboolean('General', 'Debug')
    forcewn31.set_active(config.getboolean('General', 'ForceWordNet31'))
    if config.getboolean('General', 'ForceWordNet31'):
        logging.info("Using WordNet 3.1 as per local config")
        wnver = '3.1'
        wncheckonce = True
    if config['UI-gtk']['Theme'] == "default":
        default_radio.set_active(True)
    elif config['UI-gtk']['Theme'] == "dark":
        dark_radio.set_active(True)
        darker()
    elif config['UI-gtk']['Theme'] == "light":
        light_radio.set_active(True)
        lighter()
    maxhide_check.set_active(config.getboolean('UI-gtk',
                                               'HideWindowButtonsMaximized'))
    maxhide = config.getboolean('UI-gtk', 'HideWindowButtonsMaximized')
    nocsd_check.set_active(config.getboolean('UI-gtk', 'DisableCSD'))


def apply_settings():
    """Apply the settings globally."""
    global livesearch, maxhide, wnver, wncheckonce, cdefenable, debug
    live_check = builder.get_object('live_check')
    cdef_check = builder.get_object('cdef_check')
    debug_check = builder.get_object('debug_check')
    forcewn31 = builder.get_object('forcewn31')
    light_radio = builder.get_object('light_radio')
    dark_radio = builder.get_object('dark_radio')
    default_radio = builder.get_object('default_radio')
    maxhide_check = builder.get_object('maxhide_check')
    nocsd_check = builder.get_object('nocsd_check')
    config.set('General', 'LiveSearch',
               utils.bool_str(live_check.get_active()))
    livesearch = live_check.get_active()
    config.set('General', 'CustomDefinitions',
               utils.bool_str(cdef_check.get_active()))
    cdefenable = cdef_check.get_active()
    config.set('General', 'Debug', utils.bool_str(debug_check.get_active()))
    debug = debug_check.get_active()
    config.set('General', 'ForceWordNet31',
               utils.bool_str(forcewn31.get_active()))
    if forcewn31.get_active():
        logging.info("Using WordNet 3.1 as per local config")
        wnver = '3.1'
        wncheckonce = True
    if default_radio.get_active():
        config.set('UI-gtk', 'Theme', "default")
    elif dark_radio.get_active():
        config.set('UI-gtk', 'Theme', "dark")
        darker()
    elif light_radio.get_active():
        config.set('UI-gtk', 'Theme', "light")
        lighter()
    config.set('UI-gtk', 'HideWindowButtonsMaximized',
               utils.bool_str(maxhide_check.get_active()))
    maxhide = maxhide_check.get_active()
    config.set('UI-gtk', 'DisableCSD',
               utils.bool_str(nocsd_check.get_active()))
    utils.save_settings(config)


if not parsed.verinfo and not parsed.check:
    GtkSettings = Gtk.Settings.get_default()
    if (GtkSettings.get_property("gtk-application-prefer-dark-theme") or
            GtkSettings.get_property("gtk-theme-name").endswith('-dark')):
        darker()
    else:
        lighter()
    PATH = os.path.dirname(os.path.realpath(__file__))
    GLADEFILE = PATH + "/ui/reo.ui"
    # GLADEFILE = "/usr/share/reo/reo.ui"
    builder.add_from_file(GLADEFILE)
    windowcall()
    load_settings()
    if parsed.dark:
        darker()
    elif parsed.light:
        lighter()


wnver = '3.1'
wncheckonce = False


def wncheck():
    """Check if WordNet is properly installed."""
    global wnver, wncheckonce, wn
    if not wncheckonce:
        wnver = reo_base.wnvercheck()
        logging.info("Using WordNet " + wnver)
        wncheckonce = True
    wn = str(lzma.open(utils.get_wordlist(wnver), 'r').read()).split('\\n')


def CheckBin(bintocheck):
    """Check presence of required binaries."""
    try:
        which(bintocheck)
        print(bintocheck + " seems to be installed. OK.")
        bincheck = True
    except Exception as ex:
        logging.fatal(bintocheck + " is not installed! Dependancy missing!" +
                      str(ex))
        bincheck = False
    return bincheck


def PrintChecks(espeakng, dictc, dictd, wndict):
    """Print result of all checks."""
    if (espeakng and dictc and dictd and wndict):
        print("Everything Looks Perfect!\n" +
              "You should be able to run it without any issues!")
    elif (espeakng and dictc and dictd and not wndict):
        print("WordNet's data file is missing. Re-install 'dict-wn'.\n" +
              "For Ubuntu, Debian, etc:\n" +
              "'sudo apt install dict-wn'\n" +
              "From AUR for Arch Linux:\n" +
              "'pacaur -S dict-wn'\n" +
              "Everything else (NOT everything) looks fine...\n" +
              "... BUT you can't run it.")
    elif (espeakng and not dictc and not dictd and not wndict):
        print("dict and dictd (client and server) are missing.. install it." +
              "\nFor Ubuntu, Debian, etc:\n" +
              "'sudo apt install dictd dict-wn'\n" +
              "From community repo for Arch Linux (but WordNet from AUR):\n" +
              "'pacaur -S dictd dict-wn'\n" +
              "That should point you in the right direction to getting \n" +
              "it to work.")
    elif (not espeakng and not dictc and not dictd and not wndict):
        print("ALL bits and pieces are Missing...\n" +
              "For Ubuntu, Debian, etc:\n" +
              "'sudo apt install espeak-ng dictd dict-wn'\n" +
              "From community repo for Arch Linux (but WordNet from AUR):\n" +
              "'pacaur -S espeak-ng dictd dict-wn'\n" +
              "Go on, get it working now!")
    elif (not espeakng and dictc and dictd and wndict):
        print("Everything except eSpeak-ng is working...\n" +
              "For Ubuntu, Debian, etc:\n" +
              "'sudo apt install espeak-ng'\n" +
              "From community repo for Arch Linux:\n" +
              "'pacaur -S espeak-ng' or 'sudo pacman -S espeak-ng'\n" +
              "It should be alright then.")
    elif (not espeakng and dictc and dictd and wndict):
        print("eSpeak-ng is missing and WordNet might not work as intended.\n"
              + "Install 'espeak-ng' and re-install the 'dict-wn' package.\n" +
              "For Ubuntu, Debian, etc:\n" +
              "'sudo apt install espeak-ng dict-wn'\n" +
              "From AUR for Arch Linux:\n" +
              "'pacaur -S espeak-ng dict-wn'\n" +
              "Everything else (NOT everything) looks fine.\n" +
              "Go on, try and run it!")
    elif (not espeakng and dictc and dictd and not wndict):
        print("eSpeak-ng is missing and WordNet's data file is missing." +
              "Re-install 'dict-wn'.\n" +
              "For Ubuntu, Debian, etc:\n" +
              "'sudo apt install espeak-ng dict-wn'\n" +
              "From AUR for Arch Linux:\n" +
              "'pacaur -S espeak-ng dict-wn'\n" +
              "Everything else (NOT everything) looks" +
              " fine BUT you can't run it.")


def syscheck():
    """Check requirements but not thoroughly."""
    espeakng = CheckBin('espeak-ng')
    dictc = CheckBin('dict')
    dictd = CheckBin('dictd')
    if os.path.exists('/usr/share/dictd/wn.dict.dz'):
        print('WordNet databse seems to be installed. OK.')
        wndict = True
    else:
        logging.warning("WordNet database is not found! Probably won't work.")
        wndict = False
    PrintChecks(espeakng, dictc, dictd, wndict)
    sys.exit()


if parsed.verinfo:
    reo_base.verinfo()
    sys.exit()
if parsed.check:
    syscheck()
term = None  # Last searched item.
threading.Thread(target=wncheck).start()


class GUI:
    """Define all UI actions and sub-actions."""

    def on_window_destroy(self, window):
        """Clear all windows."""
        Gtk.main_quit()

    def state_changed(self, window, state):
        """Detect changes to the window state and adapt."""
        header = builder.get_object('header')
        if maxhide and not (os.environ.get('GTK_CSD') == '0'):
            if ("MAXIMIZED" in str(state.new_window_state)):
                header.set_show_close_button(False)
            else:
                header.set_show_close_button(True)

    def pref_launch(self, pref_item):
        """Open Preferences Window."""
        pref_diag = builder.get_object('pref_diag')
        response = pref_diag.run()
        load_settings()
        if (response == Gtk.ResponseType.DELETE_EVENT or
                response == Gtk.ResponseType.CANCEL):
            pref_diag.hide()
        elif (response == Gtk.ResponseType.OK):
            pref_diag.hide()

    def apply_click(self, apply_button):
        """Apply settings only."""
        apply_settings()
        self.searchClick(passcheck=True)

    def ok_click(self, ok_button):
        """Apply settings and hide dialog."""
        pref_diag = builder.get_object('pref_diag')
        pref_diag.response(-5)
        apply_settings()
        self.searchClick(passcheck=True)

    def cancel_button_clicked(self, cancel_button):
        """Hide settings dialog."""
        pref_diag = builder.get_object('pref_diag')
        pref_diag.response(-6)

    def icon_press(self, imagemenuitem4):
        """Open About Window."""
        about = builder.get_object('aboutReo')
        about.set_version(reo_version)
        response = about.run()
        if (response == Gtk.ResponseType.DELETE_EVENT or
                response == Gtk.ResponseType.CANCEL):
            about.hide()

    def sst(self, imagemenuitem1):
        """Search selected text."""
        text = Gtk.Clipboard.get(Gdk.SELECTION_PRIMARY).wait_for_text()
        text = text.replace('-\n         ', '-').replace('\n', ' ')
        text = text.replace('         ', '')
        sb.set_text(text)
        if not text == '' and not text.isspace():
            self.searchClick()
            sb.grab_focus()

    def paste_search(self, pastensearch):
        """Search text in clipboard."""
        text = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD).wait_for_text()
        sb.set_text(text)
        if not text == '' and not text.isspace():
            self.searchClick()
            sb.grab_focus()

    def newced(self, title, primary, secondary):
        """Show error dialog."""
        cept = builder.get_object('cept')
        cest = builder.get_object('cest')
        ced = builder.get_object('ced')
        ced.set_title(title)
        cept.set_label(primary)
        cest.set_label(secondary)
        response = ced.run()
        if (response == Gtk.ResponseType.DELETE_EVENT or
                response == Gtk.ResponseType.OK):
            ced.hide()

    def searchClick(self, searchButton=None, passcheck=False):
        """Pass data to search function and set TextView data."""
        global term
        text = sb.get_text().strip()
        exceptlist = ['fortune -a', 'cowfortune']
        if not text == term or passcheck or text in exceptlist:
            viewer.get_buffer().set_text("")
            if not text.strip() == '':
                lastiter = viewer.get_buffer().get_end_iter()
                out = self.search(text)
                term = text
                viewer.get_buffer().insert_markup(lastiter, out, -1)

    def search(self, sb):
        """Clean input text, give errors and pass data to reactor."""
        if (not sb.strip('<>"?`![]()/\\:;,') == '' and
                not sb.isspace() and not sb == ''):
            text = sb.strip().strip('<>"?`![]()/\\:;,')
            return self.reactor(text)
        elif (sb.strip('<>"?`![]()/\\:;,') == '' and
              not sb.isspace() and
              not sb == ''):
            logging.error("Invalid Characters.")
            self.newced('Error: Invalid Input!', 'Invalid Characters!',
                        "Reo thinks that your input was actually \nju" +
                        "st a bunch of useless characters. \nSo, 'Inva" +
                        "lid Characters' error!")

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
            return "<tt> Running Reo with WordNet " + wnver + "</tt>"
        elif text == 'fortune -a':
            return reo_base.fortune()
        elif text == 'cowfortune':
            return reo_base.cowfortune()
        elif text == 'crash now' or text == 'close now':
            Gtk.main_quit()
        elif text == 'reo':
            reodef = str("<tt>Pronunciation: <b>/ɹˈiːəʊ/</b>\n  <b>Reo</b>" +
                         " ~ <i>Japanese Word</i>\n  <b>1:</b> Name " +
                         "of this application, chosen kind of at random." +
                         "\n  <b>2:</b> Japanese word meaning 'Wise" +
                         " Center'\n <b>Similar Words:</b>\n <i><" +
                         "span foreground=\"" + wordcol + "\">  ro, " +
                         "re, roe, redo, reno, oreo, ceo, leo, neo, " +
                         "rho, rio, reb, red, ref, rem, rep, res," +
                         " ret, rev, rex</span></i></tt>")
            return reodef
        if text and not text.isspace():
            searched = True
            return self.generator(text, wordcol, sencol)

    def cdef(self, text, wordcol, sencol):
        """Present custom definition when available."""
        with open(cdef_fold + '/' + text, 'r') as cdfile:
            cdefread = cdfile.read()
            relist = {"<i>($WORDCOL)</i>": wordcol, "<i>($SENCOL)</i>": sencol,
                      "($WORDCOL)": wordcol, "($SENCOL)": sencol,
                      "$WORDCOL": wordcol, "$SENCOL": sencol}
            for i, j in relist.items():
                cdefread = cdefread.replace(i, j)
            if "\n[warninghide]" in cdefread:
                cdefread = cdefread.replace("\n[warninghide]", "")
                return cdefread
            else:
                return(cdefread + '\n<span foreground="#e6292f">' +
                       'NOTE: This is a Custom definition. No one' +
                       ' is to be held responsible for errors in' +
                       ' this.</span>')

    def generator(self, text, wordcol, sencol):
        """Check if custom definition exists."""
        if os.path.exists(cdef_fold + '/' + text.lower()) and cdefenable:
            return self.cdef(text, wordcol, sencol)
        else:
            return reo_base.dataObtain(text, wordcol, sencol, "pango", debug)

    def cedok(self, cedok):
        """Generate OK response from error dialog."""
        ced = builder.get_object('ced')
        ced.response(Gtk.ResponseType.OK)

    def randword(self, mnurand):
        """Choose a random word and pass it to the search box."""
        rw = random.choice(wn)
        sb.set_text(rw.strip())
        self.searchClick()
        sb.grab_focus()

    def clear(self, clearButton):
        """Clear text in the Search box and the Data space."""
        sb.set_text("")
        viewer.get_buffer().set_text("")

    def audio(self, audioButton):
        """Say the search entry out loud with espeak speech synthesis."""
        speed = '120'  # To change eSpeak-ng audio speed.
        text = sb.get_text().strip()
        if searched and not text == '':
            reo_base.readTerm(speed, sb.get_text().strip())
        elif text == '' or text.isspace():
            self.newced("Umm..?", "Umm..?", "Reo can't find any text" +
                        " there! You sure \nyou typed something?")
        elif not searched:
            self.newced("Sorry!!", "Sorry!!",
                        "I'm sorry but you have to do a search" +
                        " first \nbefore trying to  listen to it." +
                        " I mean, Reo \nis <b>NOT</b> a Text-To" +
                        "-Speech Software!")

    def changed(self, searchEntry):
        """Detect changes to Search box and clean or do live searching."""
        global searched
        searched = False
        sb.set_text(sb.get_text().replace('\n', ' '))
        sb.set_text(sb.get_text().replace('         ', ''))
        if livesearch:
            self.searchClick()

    def quitb(self, imagemenuitem10):
        """Quit using menu."""
        Gtk.main_quit()

    def savedef(self, imagemenuitem2):
        """Save definition using FileChooser dialog."""
        defdiag = Gtk.FileChooserDialog("Save Definition as...",
                                        builder.get_object('window'),
                                        Gtk.FileChooserAction.SAVE,
                                        ("Save", Gtk.ResponseType.OK,
                                         "Cancel", Gtk.ResponseType.CANCEL))
        response = defdiag.run()
        if (response == Gtk.ResponseType.DELETE_EVENT or
                response == Gtk.ResponseType.CANCEL):
            defdiag.hide()
        elif response == Gtk.ResponseType.OK:
            sf = open(defdiag.get_filename(), 'w')
            startiter = viewer.get_buffer().get_start_iter()
            lastiter = viewer.get_buffer().get_end_iter()
            sf.write(viewer.get_buffer().get_text(startiter, lastiter,
                                                  'false'))
            sf.close()
            defdiag.hide()


def main():
    """Run the Gtk UI."""
    builder.connect_signals(GUI())
    Gtk.main()


if __name__ == '__main__':
    main()
