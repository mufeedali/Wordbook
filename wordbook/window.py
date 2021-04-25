# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2016-2021 Mufeed Ali <fushinari@protonmail.com>
# SPDX-License-Identifier: GPL-3.0-or-later

import os
import random
import threading
from html import escape, unescape

from gi.repository import Gdk, Gio, GLib, GObject, Gtk, Handy
from wn.util import ProgressHandler

from wordbook import base, utils
from wordbook.settings_window import SettingsWindow
from wordbook.settings import Settings


@Gtk.Template(resource_path=f"{utils.RES_PATH}/ui/window.ui")
class WordbookGtkWindow(Handy.ApplicationWindow):
    __gtype_name__ = "WordbookGtkWindow"

    _header_bar = Gtk.Template.Child("header_bar")
    _flap_toggle_button = Gtk.Template.Child("flap_toggle_button")
    _search_entry = Gtk.Template.Child("search_entry")
    _search_button = Gtk.Template.Child("search_button")
    _speak_button = Gtk.Template.Child("speak_button")
    _menu_button = Gtk.Template.Child("wordbook_menu_button")
    _flap = Gtk.Template.Child("main_flap")
    _recents_listbox = Gtk.Template.Child("recents_listbox")
    _clamp = Gtk.Template.Child("main_clamp")
    _clamped_box = Gtk.Template.Child("clamped_box")
    _stack = Gtk.Template.Child("main_stack")
    loading_label = Gtk.Template.Child("loading_label")
    loading_progress = Gtk.Template.Child("loading_progress")
    _def_view = Gtk.Template.Child("def_view")
    _pronunciation_view = Gtk.Template.Child("pronunciation_view")
    _term_view = Gtk.Template.Child("term_view")

    _complete_list = []
    _completion_request_count = 0
    _pasted = False
    searched_term = None
    _wn_downloader = base.WordnetDownloader()
    _wn_future = None

    _search_history = []
    _search_queue = []
    _last_search_fail = False
    _active_thread = None

    def __init__(self, term="", **kwargs):
        """Initialize the window."""
        super().__init__(**kwargs)

        self.lookup_term = term

        if Gio.Application.get_default().development_mode is True:
            self.get_style_context().add_class("devel")
        self.set_default_icon_name(utils.APP_ID)

        builder = Gtk.Builder.new_from_resource(
            resource_path=f"{utils.RES_PATH}/ui/menu.xml"
        )
        menu = builder.get_object("wordbook-menu")

        popover = Gtk.Popover.new_from_model(self._menu_button, model=menu)
        self._menu_button.set_popover(popover)

        self.connect("key-press-event", self._on_key_press_event)
        self._recents_listbox.connect("row-activated", self._on_recents_activated)
        self._def_view.connect("button-press-event", self._on_def_event)
        self._def_view.connect("activate-link", self._on_link_activated)
        self._search_button.connect("clicked", self.on_search_clicked)
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
            self._header_bar.set_sensitive(True)
            self.__page_switch("welcome_page")
            if self.lookup_term:
                self.trigger_search(self.lookup_term)

        # Completions. This is kept separate because it uses its own weird logic.
        # This and related code might need refactoring later on.
        self.completer = Gtk.EntryCompletion()
        self.completer_liststore = Gtk.ListStore(str)
        self.completer.set_text_column(0)
        self.completer.set_model(self.completer_liststore)
        self.completer.set_popup_completion(not Settings.get().live_search)
        self.completer.get_popup_completion()
        self._search_entry.set_completion(self.completer)
        self.completer.connect("action-activated", self._on_entry_completed)

    def on_about(self, _action, _param):
        """Show the about window."""
        about_dialog = Gtk.AboutDialog(transient_for=self, modal=True)
        about_dialog.set_logo_icon_name(utils.APP_ID)
        about_dialog.set_program_name("Wordbook")
        about_dialog.set_version(Gio.Application.get_default().version)
        about_dialog.set_comments("Wordbook is a dictionary application.")
        about_dialog.set_authors(
            [
                "Mufeed Ali",
            ]
        )
        about_dialog.set_license_type(Gtk.License.GPL_3_0)
        about_dialog.set_website("https://www.github.com/fushinari/wordbook")
        about_dialog.set_copyright("Copyright © 2016-2021 Mufeed Ali")
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

                    if out["definition"] is not None:
                        # Add to history
                        if text not in self._search_history:
                            row = Handy.ActionRow(visible=True, activatable=True)
                            row.set_title(text)
                            row.set_hexpand(False)
                            GLib.idle_add(self._recents_listbox.add, row)
                        self._search_history.append(text)

                        status = "done"
                        out_text = base.clean_pango(f'{out["definition"]}')
                        GLib.idle_add(self._def_view.set_markup, out_text)
                    else:
                        status = "fail"
                        self._last_search_fail = True
                        continue

                    GLib.idle_add(
                        self._term_view.set_markup,
                        f'<span size="large" weight="bold">{out["term"].strip()}</span>',
                    )
                    GLib.idle_add(
                        self._pronunciation_view.set_markup,
                        f'<i>{out["pronunciation"].strip()}</i>',
                    )

                    if text not in except_list and out["term"] != "Lookup failed.":
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
        term = row.get_title()
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
        GLib.idle_add(self.loading_label.set_label, "Ready.")
        self._wn_future = base.get_wn_file(self.__reloader)
        GLib.idle_add(self._header_bar.set_sensitive, True)
        self.__page_switch("welcome_page")
        if self.lookup_term:
            self.trigger_search(self.lookup_term)

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
        if self._stack.get_visible_child_name == page:
            return True
        GLib.idle_add(self._stack.set_visible_child_name, page)
        return False

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
                "Invalid Input",
                "Wordbook thinks that your input was actually just a bunch of useless "
                "characters. And so, an 'Invalid Characters' error.",
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
                if item.lower().startswith(text.lower()):
                    self._complete_list.append(item.replace("_", " "))

            for item in os.listdir(utils.CDEF_DIR):
                if len(self._complete_list) >= 10:
                    break
                item = escape(item).replace("_", " ")
                if item in self._complete_list:
                    self._complete_list.remove(item)
                if item.lower().startswith(text.lower()):
                    self._complete_list.append(f"<i>{item}</i>")

            self._complete_list = sorted(self._complete_list)
            for item in self._complete_list:
                GLib.idle_add(
                    self.completer.insert_action_markup,
                    self._complete_list.index(item),
                    item,
                )

            self._completion_request_count -= 1

    def __wn_loader(self):
        self._header_bar.set_sensitive(False)
        if not self._wn_downloader.check_status():
            self.loading_label.set_text("Downloading WordNet...")
            threading.Thread(
                target=self._wn_downloader.download, args=[ProgressUpdater]
            ).start()

    def __reloader(self):
        self.__page_switch("download_page")
        self._wn_downloader.delete_db()
        self.__wn_loader()
        self.loading_label.set_markup(
            "Re-downloading WordNet database\n"
            '<span size="small">Just a database upgrade.\n'
            "This shouldn't happen too often.</span>"
        )


class ProgressUpdater(ProgressHandler):
    def update(self, n):
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
                "Building Database...",
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
