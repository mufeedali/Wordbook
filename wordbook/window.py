# SPDX-FileCopyrightText: 2016-2025 Mufeed Ali <me@mufeed.dev>
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import os
import random
import sys
import threading
from enum import Enum
from gettext import gettext as _
from html import escape
from typing import TYPE_CHECKING

from gi.repository import Adw, Gdk, Gio, GLib, GObject, Gtk
from wn import Error
from wn.util import ProgressHandler

from wordbook import base, utils
from wordbook.settings import Settings
from wordbook.settings_window import SettingsDialog

if TYPE_CHECKING:
    from typing import Any, Literal


@Gtk.Template(resource_path=f"{utils.RES_PATH}/ui/window.ui")
class WordbookWindow(Adw.ApplicationWindow):
    __gtype_name__ = "WordbookWindow"

    search_button: Gtk.Button = Gtk.Template.Child("search_button")  # type: ignore
    download_status_page: Adw.StatusPage = Gtk.Template.Child("download_status_page")  # type: ignore
    loading_progress: Gtk.ProgressBar = Gtk.Template.Child("loading_progress")  # type: ignore

    _key_ctrlr: Gtk.EventControllerKey = Gtk.Template.Child("key_ctrlr")  # type: ignore
    _title_clamp: Adw.Clamp = Gtk.Template.Child("title_clamp")  # type: ignore
    _split_view_toggle_button: Gtk.ToggleButton = Gtk.Template.Child("split_view_toggle_button")  # type: ignore
    _search_entry: Gtk.Entry = Gtk.Template.Child("search_entry")  # type: ignore
    _speak_button: Gtk.Button = Gtk.Template.Child("speak_button")  # type: ignore
    _menu_button: Gtk.MenuButton = Gtk.Template.Child("wordbook_menu_button")  # type: ignore
    _main_split_view: Adw.OverlaySplitView = Gtk.Template.Child("main_split_view")  # type: ignore
    _history_listbox: Gtk.ListBox = Gtk.Template.Child("history_listbox")  # type: ignore
    _main_stack: Adw.ViewStack = Gtk.Template.Child("main_stack")  # type: ignore
    _main_scroll: Gtk.ScrolledWindow = Gtk.Template.Child("main_scroll")  # type: ignore
    _def_view: Gtk.Label = Gtk.Template.Child("def_view")  # type: ignore
    _def_ctrlr: Gtk.GestureClick = Gtk.Template.Child("def_ctrlr")  # type: ignore
    _pronunciation_view: Gtk.Label = Gtk.Template.Child("pronunciation_view")  # type: ignore
    _term_view: Gtk.Label = Gtk.Template.Child("term_view")  # type: ignore
    _network_fail_status_page: Adw.StatusPage = Gtk.Template.Child("network_fail_status_page")  # type: ignore
    _retry_button: Gtk.Button = Gtk.Template.Child("retry_button")  # type: ignore
    _exit_button: Gtk.Button = Gtk.Template.Child("exit_button")  # type: ignore
    _clear_history_button: Gtk.Button = Gtk.Template.Child("clear_history_button")  # type: ignore

    _style_manager: Adw.StyleManager | None = None

    _wn_downloader: base.WordnetDownloader = base.WordnetDownloader()
    _wn_future = None

    _doubled: bool = False
    _completion_request_count: int = 0
    _searched_term: str | None = None
    _search_history = None
    _search_history_list = []
    _search_queue = []
    _last_search_fail = False
    _active_thread = None
    _primary_clipboard_text = None

    def __init__(self, term="", **kwargs):
        """Initialize the window."""
        super().__init__(**kwargs)

        self.lookup_term = term

        if Gio.Application.get_default().development_mode is True:
            self.get_style_context().add_class("devel")
        self.set_default_icon_name(Gio.Application.get_default().app_id)

        self.setup_widgets()
        self.setup_actions()

    def setup_widgets(self):
        """Setup the widgets in the window."""
        self._search_history = Gio.ListStore.new(HistoryObject)
        self._history_listbox.bind_model(self._search_history, self._create_label)

        self.connect("unrealize", self._on_destroy)
        self._key_ctrlr.connect("key-pressed", self._on_key_pressed)
        self._history_listbox.connect("row-activated", self._on_history_item_activated)

        self._def_ctrlr.connect("pressed", self._on_def_press_event)
        self._def_ctrlr.connect("stopped", self._on_def_stop_event)
        self._def_view.connect("activate-link", self._on_link_activated)

        self.search_button.connect("clicked", self.on_search_clicked)
        self._search_entry.connect("changed", self._on_entry_changed)
        self._speak_button.connect("clicked", self._on_speak_clicked)
        self._retry_button.connect("clicked", self._on_retry_clicked)
        self._exit_button.connect("clicked", self._on_exit_clicked)
        self._clear_history_button.connect("clicked", self._on_clear_history)

        self._main_split_view.bind_property(
            "show-sidebar",
            self._split_view_toggle_button,
            "active",
            GObject.BindingFlags.BIDIRECTIONAL | GObject.BindingFlags.SYNC_CREATE,
        )

        self._style_manager = self.get_application().get_style_manager()
        self._style_manager.connect("notify::dark", self._on_dark_style)

        # Loading and setup.
        self._dl_wn()
        if self._wn_downloader.check_status():
            self._wn_future = base.get_wn_file(self._retry_dl_wn)
            self._set_header_sensitive(True)
            self._page_switch(Page.WELCOME)
            if self.lookup_term:
                self.trigger_search(self.lookup_term)
            self._search_entry.grab_focus_without_selecting()

        # Completions
        # FIXME: Remove use of EntryCompletion
        self.completer = Gtk.EntryCompletion()
        self.completer.set_popup_single_match(False)
        self.completer.set_text_column(0)
        self.completer.set_popup_completion(not Settings.get().live_search)
        self.completer.set_popup_set_width(True)
        self._search_entry.set_completion(self.completer)

        # Load History.
        self._search_history_list = Settings.get().history
        for text in self._search_history_list:
            history_object = HistoryObject(text)
            self._search_history.insert(0, history_object)

        # Update clear button sensitivity
        self._update_clear_button_sensitivity()

        # Set search button visibility.
        self.search_button.set_visible(not Settings.get().live_search)
        if not Settings.get().live_search:
            self.set_default_widget(self.search_button)

        def_extra_menu_model = Gio.Menu.new()
        item = Gio.MenuItem.new("Search Selected Text", "win.search-selected")
        def_extra_menu_model.append_item(item)

        # Set the extra menu model for the label
        self._def_view.set_extra_menu(def_extra_menu_model)

    def setup_actions(self):
        """Setup the Gio actions for the application window."""
        paste_search_action: Gio.SimpleAction = Gio.SimpleAction.new("paste-search", None)
        paste_search_action.connect("activate", self.on_paste_search)
        self.add_action(paste_search_action)

        preferences_action: Gio.SimpleAction = Gio.SimpleAction.new("preferences", None)
        preferences_action.connect("activate", self.on_preferences)
        self.add_action(preferences_action)

        random_word_action: Gio.SimpleAction = Gio.SimpleAction.new("random-word", None)
        random_word_action.connect("activate", self.on_random_word)
        self.add_action(random_word_action)

        search_selected_action: Gio.SimpleAction = Gio.SimpleAction.new("search-selected", None)
        search_selected_action.connect("activate", self.on_search_selected)
        search_selected_action.set_enabled(False)
        self.add_action(search_selected_action)

        clipboard: Gdk.Clipboard = self.get_primary_clipboard()
        clipboard.connect("changed", self.on_clipboard_changed)

    def on_clipboard_changed(self, clipboard: Gdk.Clipboard | None):
        clipboard = Gdk.Display.get_default().get_primary_clipboard()

        def on_selection(_clipboard, result):
            """Callback for the text selection."""
            try:
                text = clipboard.read_text_finish(result)
                if text is not None and not text.strip() == "" and not text.isspace():
                    text = text.replace("         ", "").replace("\n", "")
                    self._primary_clipboard_text = text
                    self.lookup_action("search-selected").props.enabled = True
                else:
                    self._primary_clipboard_text = None
                    self.lookup_action("search-selected").props.enabled = False
            except GLib.GError:
                # Usually happens when clipboard is empty or unsupported data type
                self._primary_clipboard_text = None
                self.lookup_action("search-selected").props.enabled = False

        cancellable = Gio.Cancellable()
        clipboard.read_text_async(cancellable, on_selection)

    def on_paste_search(self, _action, _param):
        """Search text in clipboard."""
        clipboard = Gdk.Display.get_default().get_clipboard()

        def on_paste(_clipboard, result):
            """Callback for the clipboard paste."""
            try:
                text = clipboard.read_text_finish(result)
                text = base.clean_search_terms(text)
                if text is not None and not text.strip() == "" and not text.isspace():
                    self.trigger_search(text)
            except GLib.GError:
                # Usually happens when clipboard is empty or unsupported data type
                pass

        cancellable = Gio.Cancellable()
        clipboard.read_text_async(cancellable, on_paste)

    def on_preferences(self, _action, _param):
        """Show settings window."""
        window = SettingsDialog(self)
        window.present(self)

    def on_random_word(self, _action, _param):
        """Search a random word from the wordlist."""
        random_word = random.choice(self._wn_future.result()["list"])
        random_word = random_word.replace("_", " ")
        self.trigger_search(random_word)

    def on_search_selected(self, _action, _param):
        """Search selected text from inside or outside the window."""
        self.trigger_search(self._primary_clipboard_text)

    def on_search_clicked(self, _button=None, pass_check=False, text=None):
        """Pass data to search function and set TextView data."""
        if text is None:
            text = self._search_entry.get_text().strip()
        self._page_switch(Page.SPINNER)
        self._add_to_queue(text, pass_check)

    def threaded_search(self, pass_check=False):
        """Manage a single thread to search for each term."""
        except_list = ("fortune -a", "cowfortune")
        status = SearchStatus.NONE
        while self._search_queue:
            text = self._search_queue.pop(0)
            orig_term = self._searched_term
            self._searched_term = text
            if text and (pass_check or not text == orig_term or text in except_list):
                if not text.strip() == "":
                    GLib.idle_add(self._def_view.set_markup, "")

                    out = self._search(text)

                    if out is None:
                        status = SearchStatus.RESET
                        continue

                    def validate_result(text, out_string) -> Literal[SearchStatus.SUCCESS]:
                        # Add to history
                        history_object = HistoryObject(text)
                        if text not in self._search_history_list:
                            self._search_history_list.append(text)
                            self._search_history.insert(0, history_object)
                            self._update_clear_button_sensitivity()

                        GLib.idle_add(self._def_view.set_markup, out_string)
                        return SearchStatus.SUCCESS

                    if out["out_string"] is not None:
                        status = validate_result(text, out["out_string"])
                    elif out["result"] is not None:
                        status = validate_result(text, self._process_result(out["result"]))
                    else:
                        status = SearchStatus.FAILURE
                        self._last_search_fail = True
                        continue

                    term_view_text = f'<span size="large" weight="bold">{out["term"].strip()}</span>'
                    GLib.idle_add(
                        self._term_view.set_markup,
                        term_view_text,
                    )
                    GLib.idle_add(
                        self._term_view.set_tooltip_markup,
                        term_view_text,
                    )

                    pron = "<i>" + out["pronunciation"].strip().replace("\n", "") + "</i>"
                    GLib.idle_add(
                        self._pronunciation_view.set_markup,
                        pron,
                    )
                    GLib.idle_add(
                        self._pronunciation_view.set_tooltip_markup,
                        pron,
                    )

                    if text not in except_list:
                        GLib.idle_add(self._speak_button.set_visible, True)

                    self._last_search_fail = False
                    continue

                status = SearchStatus.RESET
                continue

            if text and text == orig_term and not self._last_search_fail:
                status = SearchStatus.SUCCESS
                continue

            if text and text == orig_term and self._last_search_fail:
                status = SearchStatus.FAILURE
                continue

            status = SearchStatus.RESET

        if status == SearchStatus.SUCCESS:
            self._page_switch(Page.CONTENT)
        elif status == SearchStatus.FAILURE:
            self._page_switch(Page.SEARCH_FAIL)
        elif status == SearchStatus.RESET:
            self._page_switch(Page.WELCOME)

        self._active_thread = None

    def trigger_search(self, text):
        """Trigger search action."""
        GLib.idle_add(self._search_entry.set_text, text)
        GLib.idle_add(self.on_search_clicked, None, False, text)

    def _on_dark_style(self, _object, _param):
        """Refresh definition view when switching dark theme."""
        if self._searched_term is not None:
            self.on_search_clicked(pass_check=True, text=self._searched_term)

    def _on_def_press_event(self, _click, n_press, _x, _y):
        """Handle double click on definition view."""
        if Settings.get().double_click:
            self._doubled = n_press == 2
        else:
            self._doubled = False

    def _on_def_stop_event(self, _click):
        """Search on double click."""
        if self._doubled:
            clipboard = Gdk.Display.get_default().get_primary_clipboard()

            def on_paste(_clipboard, result):
                text = clipboard.read_text_finish(result)
                text = base.clean_search_terms(text)
                if text is not None and not text.strip() == "" and not text.isspace():
                    self.trigger_search(text)

            cancellable = Gio.Cancellable()
            clipboard.read_text_async(cancellable, on_paste)

    def _on_destroy(self, _window):
        """Detect closing of the window."""
        Settings.get().history = self._search_history_list[-10:]

    def _on_entry_changed(self, _entry):
        """Detect changes to text and do live search if enabled."""

        self._completion_request_count += 1
        if self._completion_request_count == 1:
            threading.Thread(
                target=self._update_completions,
                args=[self._search_entry.get_text()],
                daemon=True,
            ).start()

        if Settings.get().live_search:
            GLib.idle_add(self.on_search_clicked)

    def _on_clear_history(self, _widget):
        """Clear the search history."""
        self._search_history.remove_all()
        self._search_history_list = []
        Settings.get().history = []
        self._update_clear_button_sensitivity()

    def _update_clear_button_sensitivity(self):
        """Update the sensitivity of the clear history button."""
        has_history = len(self._search_history_list) > 0
        self._clear_history_button.set_sensitive(has_history)

    @staticmethod
    def _on_exit_clicked(_widget):
        """Handle exit button click in network failure page."""
        sys.exit()

    def _on_link_activated(self, _widget, data):
        """Search for terms that are marked as hyperlinks."""
        if data.startswith("search;"):
            GLib.idle_add(self._search_entry.set_text, data[7:])
            self.on_search_clicked(text=data[7:])
        return Gdk.EVENT_STOP

    def _on_key_pressed(self, _button, keyval, _keycode, state):
        """Handle key press events for quick search."""
        modifiers = state & Gtk.accelerator_get_default_mod_mask()
        shift_mask = Gdk.ModifierType.SHIFT_MASK
        unicode_key_val = Gdk.keyval_to_unicode(keyval)
        if (
            GLib.unichar_isgraph(chr(unicode_key_val))
            and modifiers in (shift_mask, 0)
            and not self._search_entry.is_focus()
        ):
            self._search_entry.grab_focus_without_selecting()
            text = self._search_entry.get_text() + chr(unicode_key_val)
            self._search_entry.set_text(text)
            self._search_entry.set_position(len(text))
            return Gdk.EVENT_STOP
        return Gdk.EVENT_PROPAGATE

    def _on_history_item_activated(self, _widget, row):
        """Handle history item clicks."""
        term = row.get_first_child().get_first_child().get_label()
        self.trigger_search(term)

    def _on_retry_clicked(self, _widget):
        """Handle retry button click in network failure page."""
        self._page_switch(Page.DOWNLOAD)
        self._dl_wn()

    def _add_to_queue(self, text, pass_check=False):
        """Add search term to queue."""
        if self._search_queue:
            self._search_queue.pop(0)
        self._search_queue.append(text)

        if self._active_thread is None:
            # If there is no active thread, create one and start it.
            self._active_thread = threading.Thread(target=self.threaded_search, args=[pass_check], daemon=True)
            self._active_thread.start()

    def _on_speak_clicked(self, _button):
        """Say the search entry out loud with espeak speech synthesis."""
        base.read_term(
            self._searched_term,
            speed="120",
            accent=Settings.get().pronunciations_accent,
        )

    def progress_complete(self):
        """Run upon completion of loading."""
        GLib.idle_add(self.download_status_page.set_title, _("Ready."))
        self._wn_future = base.get_wn_file(self._retry_dl_wn)
        GLib.idle_add(self._set_header_sensitive, True)
        self._page_switch(Page.WELCOME)
        if self.lookup_term:
            self.trigger_search(self.lookup_term)
        self._search_entry.grab_focus_without_selecting()

    @staticmethod
    def _create_label(element):
        """Create labels for history list."""
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, visible=True)
        label = Gtk.Label(
            label=element.term,
            margin_top=8,
            margin_bottom=8,
            margin_start=8,
            margin_end=8,
        )
        box.append(label)
        return box

    def _new_error(self, primary_text, secondary_text) -> Adw.AlertDialog:
        """Show an error dialog."""
        dialog = Adw.AlertDialog.new(primary_text, secondary_text)
        dialog.add_response("dismiss", _("Dismiss"))
        dialog.choose(self)

    def _page_switch(self, page):
        """Switch main stack pages."""
        if page == "content_page":
            GLib.idle_add(self._main_scroll.get_vadjustment().set_value, 0)
        if self._main_stack.get_visible_child_name == page:
            return True
        GLib.idle_add(self._main_stack.set_visible_child_name, page)
        return False

    def _process_result(self, result: dict):
        """Process results from wn."""
        out_string = ""
        word_color = result["word_color"]
        sentence_color = result["sentence_color"]
        first = True
        for pos in result.keys():
            i = 0
            orig_synset = None
            if pos not in ("word_color", "sentence_color") and result[pos]:
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
                    out_string += f"\n  <b>{i}</b>: {synset['definition']}"

                    for example in synset["examples"]:
                        out_string += f'\n        <span foreground="{sentence_color}">{example}</span>'

                    pretty_syn = self._process_word_links(synset["syn"], word_color)
                    if pretty_syn:
                        out_string += f"\n        Synonyms:<i> {pretty_syn}</i>"

                    pretty_ant = self._process_word_links(synset["ant"], word_color)
                    if pretty_ant:
                        out_string += f"\n        Antonyms:<i> {pretty_ant}</i>"

                    pretty_sims = self._process_word_links(synset["sim"], word_color)
                    if pretty_sims:
                        out_string += f"\n        Similar to:<i> {pretty_sims}</i>"

                    pretty_alsos = self._process_word_links(synset["also_sees"], word_color)
                    if pretty_alsos:
                        out_string += f"\n        Also see:<i> {pretty_alsos}</i>"
        return out_string

    @staticmethod
    def _process_word_links(word_list, word_color):
        """Process word links like synonyms, antonyms, etc."""
        pretty_list = []
        for word in word_list:
            pretty_list.append(f'<span foreground="{word_color}"><a href="search;{word}">{word}</a></span>')
        if pretty_list:
            pretty_list = ", ".join(pretty_list)
            return pretty_list
        return ""

    def _search(self, search_text: str) -> dict[str, Any] | None:
        """Clean input text, give errors and pass data to formatter."""
        text = base.clean_search_terms(search_text)
        if not text == "" and not text.isspace():
            return base.format_output(
                text,
                self._style_manager.get_dark(),
                self._wn_future.result()["instance"],
                Settings.get().cdef,
                accent=Settings.get().pronunciations_accent,
            )
        if not Settings.get().live_search:
            GLib.idle_add(
                self._new_error,
                _("Invalid input"),
                _("Nothing definable was found in your search input"),
            )
        self._searched_term = None
        return None

    def _update_completions(self, text):
        """Update completions from wordlist and cdef folder."""
        while self._completion_request_count > 0:
            completer_liststore = Gtk.ListStore(str)
            _complete_list = []

            for item in self._wn_future.result()["list"]:
                if len(_complete_list) >= 10:
                    break
                item = item.replace("_", " ")
                if item.lower().startswith(text.lower()) and item not in _complete_list:
                    _complete_list.append(item)

            if Settings.get().cdef:
                for item in os.listdir(utils.CDEF_DIR):
                    # FIXME: There is no indicator that this is a custom definition
                    # Not a priority but a nice-to-have.
                    if len(_complete_list) >= 10:
                        break
                    item = escape(item).replace("_", " ")
                    if item.lower().startswith(text.lower()) and item not in _complete_list:
                        _complete_list.append(item)

            _complete_list = sorted(_complete_list, key=str.casefold)
            for item in _complete_list:
                completer_liststore.append((item,))

            self._completion_request_count -= 1
            GLib.idle_add(self.completer.set_model, completer_liststore)
            GLib.idle_add(self.completer.complete)

    def _set_header_sensitive(self, status):
        """Disable/enable header buttons."""
        self._title_clamp.set_sensitive(status)
        self._split_view_toggle_button.set_sensitive(status)
        self._menu_button.set_sensitive(status)

    def _dl_wn(self):
        """Download WordNet data."""
        self._set_header_sensitive(False)
        if not self._wn_downloader.check_status():
            self.download_status_page.set_description(_("Downloading WordNet…"))
            threading.Thread(target=self._try_dl_wn).start()

    def _try_dl_wn(self):
        """Attempt to download WordNet data."""
        try:
            self._wn_downloader.download(ProgressUpdater)
        except Error as err:
            self._network_fail_status_page.set_description(f"<small><tt>Error: {err}</tt></small>")
            utils.log_warning(err)
            self._page_switch(Page.NETWORK_FAIL)

    def _retry_dl_wn(self):
        """Re-download WordNet data in event of failure."""
        self._page_switch(Page.DOWNLOAD)
        self._wn_downloader.delete_db()
        self._dl_wn()
        self.download_status_page.set_description(
            _("Re-downloading WordNet database")
            + "\n"
            + _("Just a database upgrade.")
            + "\n"
            + _("This shouldn't happen too often.")
        )


class SearchStatus(Enum):
    NONE = 0
    SUCCESS = 1
    FAILURE = 2
    RESET = 3


class Page(str, Enum):
    CONTENT = "content_page"
    DOWNLOAD = "download_page"
    NETWORK_FAIL = "network_fail_page"
    SEARCH_FAIL = "search_fail_page"
    SPINNER = "spinner_page"
    WELCOME = "welcome_page"


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
                Gio.Application.get_default().win.download_status_page.set_description,
                _("Building Database…"),
            )
        else:
            GLib.idle_add(
                Gio.Application.get_default().win.download_status_page.set_description,
                message,
            )

    def close(self):
        """Signal the completion of building the WordNet database."""
        if self.kwargs["message"] not in ("Download", "Read"):
            Gio.Application.get_default().win.progress_complete()
