# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2016-2021 Mufeed Ali <fushinari@protonmail.com>
# SPDX-License-Identifier: GPL-3.0-or-later

import os
import random
import threading
from html import escape, unescape

from gettext import gettext as _
from gi.repository import Gdk, Gio, GLib, GObject, Gtk, Handy
from wn import Error
from wn.util import ProgressHandler

from wordbook import base, utils
from wordbook.settings_window import SettingsWindow
from wordbook.settings import Settings


@Gtk.Template(resource_path=f"{utils.RES_PATH}/ui/window.ui")
class WordbookGtkWindow(Handy.ApplicationWindow):
    __gtype_name__ = "WordbookGtkWindow"

    _header_bar = Gtk.Template.Child("header_bar")
    _title_clamp = Gtk.Template.Child("title_clamp")
    _flap_toggle_button = Gtk.Template.Child("flap_toggle_button")
    _search_entry = Gtk.Template.Child("search_entry")
    search_button = Gtk.Template.Child("search_button")
    _speak_button = Gtk.Template.Child("speak_button")
    _menu_button = Gtk.Template.Child("wordbook_menu_button")
    _flap = Gtk.Template.Child("main_flap")
    _recents_listbox = Gtk.Template.Child("recents_listbox")
    _clamp = Gtk.Template.Child("main_clamp")
    _clamped_box = Gtk.Template.Child("clamped_box")
    _stack = Gtk.Template.Child("main_stack")
    loading_label = Gtk.Template.Child("loading_label")
    loading_progress = Gtk.Template.Child("loading_progress")
    _main_scroll = Gtk.Template.Child("main_scroll")
    _def_view = Gtk.Template.Child("def_view")
    _pronunciation_view = Gtk.Template.Child("pronunciation_view")
    _term_view = Gtk.Template.Child("term_view")

    _complete_list = []
    _completion_request_count = 0
    _pasted = False
    searched_term = None
    _wn_downloader = base.WordnetDownloader()
    _wn_future = None

    _search_history = None
    _search_history_list = []
    _search_queue = []
    _last_search_fail = False
    _active_thread = None

    def __init__(self, term="", **kwargs):
        """Initialize the window."""
        super().__init__(**kwargs)

        self.lookup_term = term

        if Gio.Application.get_default().development_mode is True:
            self.get_style_context().add_class("devel")
        self.set_default_icon_name(Gio.Application.get_default().app_id)

        builder = Gtk.Builder.new_from_resource(
            resource_path=f"{utils.RES_PATH}/ui/menu.ui"
        )
        menu = builder.get_object("wordbook-menu")

        popover = Gtk.Popover.new_from_model(self._menu_button, model=menu)
        self._menu_button.set_popover(popover)

        self._search_history = Gio.ListStore.new(HistoryObject)
        self._recents_listbox.bind_model(self._search_history, self.__create_label)

        self.connect("destroy", self._on_destroy)
        self.connect("key-press-event", self._on_key_press_event)
        self._recents_listbox.connect("row-activated", self._on_recents_activated)
        self._def_view.connect("button-press-event", self._on_def_event)
        self._def_view.connect("activate-link", self._on_link_activated)
        self.search_button.connect("clicked", self.on_search_clicked)
        self._search_entry.connect("changed", self._on_entry_changed)
        self._search_entry.connect("drag-data-received", self._on_drag_received)
        self._search_entry.connect("paste-clipboard", self._on_paste_done)
        self._speak_button.connect("clicked", self._on_speak_clicked)

        self._flap.bind_property(
            "reveal-flap",
            self._flap_toggle_button,
            "active",
            GObject.BindingFlags.BIDIRECTIONAL | GObject.BindingFlags.SYNC_CREATE,
        )

        # Loading and setup.
        self.__wn_loader()
        if self._wn_downloader.check_status():
            self._wn_future = base.get_wn_file(self.__reloader)
            self.__set_header_sensitive(True)
            self.__page_switch("welcome_page")
            if self.lookup_term:
                self.trigger_search(self.lookup_term)
            else:
                GLib.idle_add(self._search_entry.grab_focus)

        # Completions. This is kept separate because it uses its own weird logic.
        # This and related code might need refactoring later on.
        self.completer = Gtk.EntryCompletion()
        self.completer_liststore = Gtk.ListStore(str)
        self.completer.set_text_column(0)
        self.completer.set_model(self.completer_liststore)
        self.completer.set_popup_completion(not Settings.get().live_search)
        self.completer.set_popup_set_width(True)
        self._search_entry.set_completion(self.completer)
        self.completer.connect("action-activated", self._on_entry_completed)

        # Load History.
        self._search_history_list = Settings.get().history
        for text in self._search_history_list:
            history_object = HistoryObject(text)
            self._search_history.insert(0, history_object)

        # Set search button visibility.
        self.search_button.set_visible(not Settings.get().live_search)

    def on_about(self, _action, _param):
        """Show the about window."""
        about_dialog = Gtk.AboutDialog(transient_for=self, modal=True)
        about_dialog.set_logo_icon_name(Gio.Application.get_default().app_id)
        about_dialog.set_program_name(_("Wordbook"))
        about_dialog.set_version(Gio.Application.get_default().version)
        about_dialog.set_comments(_("Lookup definitions of any English term."))
        about_dialog.set_authors(
            [
                "Mufeed Ali",
            ]
        )
        about_dialog.set_license_type(Gtk.License.GPL_3_0)
        about_dialog.set_website("https://www.github.com/fushinari/wordbook")
        about_dialog.set_copyright(_("Copyright © 2016–2021 Mufeed Ali"))
        about_dialog.connect("response", lambda dialog, response: dialog.destroy())
        about_dialog.present()

    def on_paste_search(self, _action, _param):
        """Search text in clipboard."""
        text = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD).wait_for_text()
        text = base.cleaner(text)
        if text is not None and not text.strip() == "" and not text.isspace():
            self.trigger_search(text)

    def on_preferences(self, _action, _param):
        """Show settings window."""
        window = SettingsWindow(parent=self, transient_for=self)
        window.present()

    def on_random_word(self, _action, _param):
        """Search a random word from the wordlist."""
        random_word = random.choice(self._wn_future.result()["list"])
        random_word = random_word.replace("_", " ")
        self.trigger_search(random_word)

    def on_search_selected(self, _action, _param):
        """Search selected text from inside or outside the window."""
        text = Gtk.Clipboard.get(Gdk.SELECTION_PRIMARY).wait_for_text()
        if text is not None and not text.strip() == "" and not text.isspace():
            text = text.replace("         ", "").replace("\n", "")
            self.trigger_search(text)

    def on_shortcuts(self, _action, _param):
        """Launch the Keyboard Shortcuts window."""
        builder = Gtk.Builder.new_from_resource(
            resource_path=f"{utils.RES_PATH}/ui/shortcuts_window.ui"
        )
        shortcuts_window = builder.get_object("shortcuts")
        shortcuts_window.set_transient_for(self)
        shortcuts_window.show()

    def on_search_clicked(self, _button=None, pass_check=False, text=None):
        """Pass data to search function and set TextView data."""
        if text is None:
            text = self._search_entry.get_text().strip()
        self.__page_switch("spinner_page")
        self._add_to_queue(text, pass_check)

    def threaded_search(self, pass_check=False):
        except_list = ("fortune -a", "cowfortune")
        status = None
        while self._search_queue:
            text = self._search_queue.pop(0)
            orig_term = self.searched_term
            self.searched_term = text
            if text and (pass_check or not text == orig_term or text in except_list):

                if not text.strip() == "":
                    out = self.__search(text)

                    if out is None:
                        status = "welcome"
                        continue

                    def success_result(text, out_string):
                        # Add to history
                        history_object = HistoryObject(text)
                        if text not in self._search_history_list:
                            self._search_history_list.append(text)
                            self._search_history.insert(0, history_object)

                        GLib.idle_add(self._def_view.set_markup, out_string)
                        return "done"

                    if out["out_string"] is not None:
                        status = success_result(text, out["out_string"])
                    elif out["result"] is not None:
                        status = success_result(
                            text, self.__process_result(out["result"])
                        )
                    else:
                        status = "fail"
                        self._last_search_fail = True
                        continue

                    GLib.idle_add(
                        self._term_view.set_markup,
                        f'<span size="large" weight="bold">{out["term"].strip()}</span>',
                    )
                    pron = out["pronunciation"].strip().replace("\n", "")
                    GLib.idle_add(
                        self._pronunciation_view.set_markup,
                        f"<i>{pron}</i>",
                    )

                    if text not in except_list:
                        GLib.idle_add(self._speak_button.set_visible, True)

                    self._last_search_fail = False
                    continue

                status = "welcome"
                continue

            if text and text == orig_term and not self._last_search_fail:
                status = "done"
                continue

            if text and text == orig_term and self._last_search_fail:
                status = "fail"
                continue

            status = "welcome"

        if status == "done":
            self.__page_switch("content_page")
        elif status == "fail":
            self.__page_switch("fail_page")
        elif status == "welcome":
            self.__page_switch("welcome_page")
        self._active_thread = None

    def trigger_search(self, text):
        """Trigger search action."""
        GLib.idle_add(self._search_entry.set_text, text)
        GLib.idle_add(self.on_search_clicked, text=text)
        GLib.idle_add(self._search_entry.grab_focus)

    def _on_def_event(self, _eventbox, event):
        """Search on double click."""
        if (
            Settings.get().double_click
            and event.type == Gdk.EventType.DOUBLE_BUTTON_PRESS
        ):
            text = Gtk.Clipboard.get(Gdk.SELECTION_PRIMARY).wait_for_text()
            if text is not None and not text.strip() == "" and not text.isspace():
                text = text.split(" ")[0]
                self.trigger_search(text)

    def _on_destroy(self, _window):
        """Detect closing of the window."""
        Settings.get().history = self._search_history_list[-10:]

    def _on_drag_received(self, _widget, _drag_context, _x, _y, _data, _info, _time):
        """Search on receiving drag and drop event."""
        self._search_entry.set_text("")
        GLib.idle_add(self.__entry_cleaner)
        GLib.idle_add(self._search_entry.set_position, -1)
        GLib.idle_add(self.on_search_clicked)

    def _on_entry_changed(self, _entry):
        """Detect changes to text and do live search if enabled."""
        self._completion_request_count += 1
        if self._completion_request_count == 1:
            threading.Thread(
                target=self.__update_completions,
                args=[self._search_entry.get_text()],
                daemon=True,
            ).start()
        if self._pasted is True:
            self.__entry_cleaner()
            self._pasted = False
        if Settings.get().live_search:
            GLib.idle_add(self.on_search_clicked)

    def _on_entry_completed(self, _entry_completion, index):
        """Enter text into the entry using completions."""
        text = (
            self._complete_list[index]
            .replace("<i>", "")
            .replace("</i>", "")
            .replace("<b>", "")
            .replace("</b>", "")
        )
        self._search_entry.set_text(unescape(text))
        self._search_entry.set_position(-1)
        GLib.idle_add(self.on_search_clicked)

    def _on_key_press_event(self, _widget, event):
        """Focus onto the search entry when needed (quick search)."""
        modifiers = event.get_state() & Gtk.accelerator_get_default_mod_mask()

        shift_mask = Gdk.ModifierType.SHIFT_MASK
        key_unicode = Gdk.keyval_to_unicode(event.keyval)
        if GLib.unichar_isgraph(chr(key_unicode)) and modifiers in (shift_mask, 0):
            self._search_entry.grab_focus_without_selecting()

    def _on_link_activated(self, _widget, data):
        """Search for terms that are marked as hyperlinks."""
        if data.startswith("search;"):
            GLib.idle_add(self._search_entry.set_text, data[7:])
            self.on_search_clicked(text=data[7:])

    def _on_paste_done(self, _widget):
        """Cleanup pasted data."""
        self._pasted = True

    def _on_recents_activated(self, _widget, row):
        term = row.get_child().get_children()[0].get_label()
        self.trigger_search(term)

    def _add_to_queue(self, text, pass_check=False):
        if self._search_queue:
            self._search_queue.pop(0)
        self._search_queue.append(text)

        if self._active_thread is None:
            # If there is no active thread, create one and start it.
            self._active_thread = threading.Thread(
                target=self.threaded_search, args=[pass_check], daemon=True
            )
            self._active_thread.start()

    def _on_speak_clicked(self, _button):
        """Say the search entry out loud with espeak speech synthesis."""
        base.read_term(
            self.searched_term,
            speed="120",
            accent=Settings.get().pronunciations_accent,
        )

    def progress_complete(self):
        """Run upon completion of loading."""
        GLib.idle_add(self.loading_label.set_label, _("Ready."))
        self._wn_future = base.get_wn_file(self.__reloader)
        GLib.idle_add(self.__set_header_sensitive, True)
        self.__page_switch("welcome_page")
        if self.lookup_term:
            self.trigger_search(self.lookup_term)
        else:
            GLib.idle_add(self._search_entry.grab_focus)

    @staticmethod
    def __create_label(element):
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, visible=True)
        label = Gtk.Label(label=element.term, margin=8, visible=True)
        box.add(label)
        return box

    def __entry_cleaner(self):
        term = self._search_entry.get_text()
        self._search_entry.set_text(base.cleaner(term))

    def __new_error(self, primary_text, seconday_text):
        """Show an error dialog."""
        dialog = Gtk.MessageDialog(
            self, 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.OK, primary_text
        )
        dialog.format_secondary_text(seconday_text)
        dialog.run()
        dialog.destroy()

    def __page_switch(self, page):
        if page == "content_page":
            GLib.idle_add(self._main_scroll.get_vadjustment().set_value, 0)
        if self._stack.get_visible_child_name == page:
            return True
        GLib.idle_add(self._stack.set_visible_child_name, page)
        return False

    def __process_result(self, result: dict):
        out_string = ""
        word_col = result["word_col"]
        sen_col = result["sen_col"]
        first = True
        for pos in result.keys():
            i = 0
            orig_synset = None
            if pos not in ("word_col", "sen_col") and result[pos]:
                for synset in sorted(result[pos], key=lambda k: k["name"]):
                    synset_name = synset["name"]
                    if orig_synset is None:
                        i = 1
                        if not first:
                            out_string += "\n\n"
                        out_string += f"{synset_name} ~ <b>{pos}</b>"
                        orig_synset = synset_name
                        first = False
                    elif synset_name != orig_synset:
                        i = 1
                        out_string += f"\n\n{synset_name} ~ <b>{pos}</b>"
                        orig_synset = synset_name
                    else:
                        i += 1
                    out_string += f'\n  <b>{i}</b>: {synset["definition"]}'

                    for example in synset["examples"]:
                        out_string += (
                            f'\n        <span foreground="{sen_col}">{example}</span>'
                        )

                    pretty_syn = self.__process_word_links(synset["syn"], word_col)
                    if pretty_syn:
                        out_string += f"\n        Synonyms:<i> {pretty_syn}</i>"

                    pretty_ant = self.__process_word_links(synset["ant"], word_col)
                    if pretty_ant:
                        out_string += f"\n        Antonyms:<i> {pretty_ant}</i>"

                    pretty_sims = self.__process_word_links(synset["sim"], word_col)
                    if pretty_sims:
                        out_string += f"\n        Similar to:<i> {pretty_sims}</i>"

                    pretty_alsos = self.__process_word_links(
                        synset["also_sees"], word_col
                    )
                    if pretty_alsos:
                        out_string += f"\n        Also see:<i> {pretty_alsos}</i>"
        return out_string

    def __process_word_links(self, word_list, word_col):
        pretty_list = []
        for word in word_list:
            pretty_list.append(
                f'<span foreground="{word_col}">'
                f'<a href="search;{word}">{word}</a>'
                "</span>"
            )
        if pretty_list:
            pretty_list = ", ".join(pretty_list)
            return pretty_list
        return ""

    def __search(self, search_text):
        """Clean input text, give errors and pass data to reactor."""
        text = base.cleaner(search_text)
        if not text == "" and not text.isspace():
            return base.reactor(
                text,
                Settings.get().gtk_dark_font,
                self._wn_future.result()["instance"],
                Settings.get().cdef,
                accent=Settings.get().pronunciations_accent,
            )
        if not Settings.get().live_search:
            GLib.idle_add(
                self.__new_error,
                _("Invalid input"),
                _("Nothing definable was found in your search input"),
            )
        self.searched_term = None
        return None

    def __update_completions(self, text):
        while self._completion_request_count > 0:
            while len(self._complete_list) > 0:
                GLib.idle_add(self.completer.delete_action, 0)
                self._complete_list.pop(0)

            for item in self._wn_future.result()["list"]:
                if len(self._complete_list) >= 10:
                    break
                item = item.replace("_", " ")
                if (
                    item.lower().startswith(text.lower())
                    and item not in self._complete_list
                ):
                    self._complete_list.append(item)

            if Settings.get().cdef:
                for item in os.listdir(utils.CDEF_DIR):
                    if len(self._complete_list) >= 10:
                        break
                    item = escape(item).replace("_", " ")
                    if item in self._complete_list:
                        self._complete_list.remove(item)
                    if item.lower().startswith(text.lower()):
                        self._complete_list.append(f"<i>{item}</i>")

            self._complete_list = sorted(self._complete_list, key=str.casefold)
            for item in self._complete_list:
                GLib.idle_add(
                    self.completer.insert_action_markup,
                    self._complete_list.index(item),
                    item,
                )

            self._completion_request_count -= 1

    def __try_dl(self):
        try:
            self._wn_downloader.download(ProgressUpdater)
        except Error:
            GLib.idle_add(self.loading_label.set_text, _("Download failed :("))
            GLib.idle_add(self.loading_progress.set_visible, False)

    def __set_header_sensitive(self, status):
        self._title_clamp.set_sensitive(status)
        self._flap_toggle_button.set_sensitive(status)
        # self._menu_button.set_sensitive(status)

    def __wn_loader(self):
        self.__set_header_sensitive(False)
        if not self._wn_downloader.check_status():
            self.loading_label.set_text(_("Downloading WordNet…"))
            threading.Thread(target=self.__try_dl).start()

    def __reloader(self):
        self.__page_switch("download_page")
        self._wn_downloader.delete_db()
        self.__wn_loader()
        self.loading_label.set_markup(
            _("Re-downloading WordNet database")
            + '\n<span size="small">'
            + _("Just a database upgrade.")
            + "\n"
            + _("This shouldn't happen too often.")
            + "</span>"
        )


class HistoryObject(GObject.Object):
    term = ""

    def __init__(self, term):
        super().__init__()
        self.term = term


class ProgressUpdater(ProgressHandler):
    def update(self, n: int = 1, force: bool = False):
        """Update the progress bar."""
        self.kwargs["count"] += n
        if self.kwargs["total"] > 0:
            progress_fraction = self.kwargs["count"] / self.kwargs["total"]
            GLib.idle_add(
                Gio.Application.get_default().win.loading_progress.set_fraction,
                progress_fraction,
            )

    @staticmethod
    def flash(message):
        """Update the progress label."""
        if message == "Database":
            GLib.idle_add(
                Gio.Application.get_default().win.loading_label.set_label,
                _("Building Database…"),
            )
        else:
            GLib.idle_add(
                Gio.Application.get_default().win.loading_label.set_label,
                message,
            )

    def close(self):
        """Signal the completion of building the WordNet database."""
        if self.kwargs["message"] != "Download":
            Gio.Application.get_default().win.progress_complete()
