# SPDX-FileCopyrightText: 2016-2025 Mufeed Ali <me@mufeed.dev>
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import random
import sys
import threading
import time
from enum import Enum, auto
from gettext import gettext as _
from html import escape
from typing import TYPE_CHECKING

from gi.repository import Adw, Gdk, Gio, GLib, GObject, Gtk
from rapidfuzz import fuzz, process
from wn import Error
from wn.util import ProgressHandler

from wordbook import base, utils
from wordbook.settings import Settings
from wordbook.settings_window import SettingsDialog

if TYPE_CHECKING:
    from typing import Any, Literal


class SearchStatus(Enum):
    NONE = auto()
    SUCCESS = auto()
    FAILURE = auto()
    RESET = auto()


class Page(str, Enum):
    CONTENT = "content_page"
    DOWNLOAD = "download_page"
    NETWORK_FAIL = "network_fail_page"
    SEARCH_FAIL = "search_fail_page"
    SPINNER = "spinner_page"
    WELCOME = "welcome_page"


class HistoryObject(GObject.Object):
    term = ""
    is_favorite = False

    def __init__(self, term, is_favorite=False):
        super().__init__()
        self.term = term
        self.is_favorite = is_favorite


class ProgressUpdater(ProgressHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._last_update_time = 0
        self._update_interval = 0.1

    def update(self, n: int = 1, force: bool = False):
        """Update the progress bar with throttling."""
        self.kwargs["count"] += n

        # Throttle UI updates
        current_time = time.time()
        if not force and (current_time - self._last_update_time) < self._update_interval:
            return

        self._last_update_time = current_time

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
    _definitions_listbox: Gtk.ListBox = Gtk.Template.Child("definitions_listbox")  # type: ignore
    _pronunciation_view: Gtk.Label = Gtk.Template.Child("pronunciation_view")  # type: ignore
    _term_view: Gtk.Label = Gtk.Template.Child("term_view")  # type: ignore
    _network_fail_status_page: Adw.StatusPage = Gtk.Template.Child("network_fail_status_page")  # type: ignore
    _search_fail_status_page: Adw.StatusPage = Gtk.Template.Child("search_fail_status_page")  # type: ignore
    _search_fail_description_label: Gtk.Label = Gtk.Template.Child("search_fail_description_label")  # type: ignore
    _retry_button: Gtk.Button = Gtk.Template.Child("retry_button")  # type: ignore
    _exit_button: Gtk.Button = Gtk.Template.Child("exit_button")  # type: ignore
    _clear_history_button: Gtk.Button = Gtk.Template.Child("clear_history_button")  # type: ignore
    _favorites_filter_button: Gtk.ToggleButton = Gtk.Template.Child("favorites_filter_button")  # type: ignore

    _style_manager: Adw.StyleManager | None = None

    _wn_downloader: base.WordnetDownloader = base.WordnetDownloader()
    _wn_instance: base.wn.Wordnet | None = None
    _wn_wordlist: list[str] = []

    _doubled: bool = False
    _completion_request_count: int = 0
    _searched_term: str | None = None
    _search_history: Gio.ListStore | None = None
    _search_queue: list[str] = []
    _last_search_fail: bool = False
    _active_thread: threading.Thread | None = None
    _primary_clipboard_text: str | None = None
    _show_favorites_only: bool = False

    # Initialize history delay timer for live search
    _history_delay_timer = None
    _pending_history_text = None

    # Auto-paste queuing
    _auto_paste_queued: bool = False

    def __init__(self, term="", auto_paste_requested=False, **kwargs):
        """Initialize the window."""
        super().__init__(**kwargs)

        self.set_default_size(Settings.get().window_width, Settings.get().window_height)

        self.lookup_term = term
        self.auto_paste_requested = auto_paste_requested

        app = self.get_application()
        if app.development_mode is True:
            self.get_style_context().add_class("devel")
        self.set_default_icon_name(app.app_id)

        self.setup_widgets()
        self.setup_actions()

    def setup_widgets(self):
        """Setup the widgets in the window."""
        self._search_history = Gio.ListStore.new(HistoryObject)
        self._history_listbox.bind_model(self._search_history, self._create_label)
        self._search_history.connect("items-changed", self._on_history_items_changed)

        # Connect signal to apply CSS classes when rows are created
        self._history_listbox.connect("row-activated", self._on_history_item_activated)

        self.connect("notify::is-active", self._on_is_active_changed)
        self.connect("unrealize", self._on_destroy)
        self._key_ctrlr.connect("key-pressed", self._on_key_pressed)

        self._search_fail_description_label.connect("activate-link", self._on_link_activated)
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

        # Completions
        # FIXME: Remove use of EntryCompletion
        self.completer = Gtk.EntryCompletion()
        self.completer.set_popup_single_match(True)
        self.completer.set_text_column(0)
        self.completer.set_popup_completion(not Settings.get().live_search)
        self.completer.set_popup_set_width(True)
        self._search_entry.set_completion(self.completer)

        # Load History.
        history_items = [HistoryObject(term, Settings.get().is_favorite(term)) for term in Settings.get().history]
        self._search_history.splice(0, 0, history_items)

        # Update clear button sensitivity
        self._update_clear_button_sensitivity()

        # Set search button visibility.
        self.search_button.set_visible(not Settings.get().live_search)
        if not Settings.get().live_search:
            self.set_default_widget(self.search_button)

        def_extra_menu_model = Gio.Menu.new()
        item = Gio.MenuItem.new(_("Search Selected Text"), "win.search-selected")
        def_extra_menu_model.append_item(item)
        self._def_extra_menu_model = def_extra_menu_model

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

        toggle_favorites_action: Gio.SimpleAction = Gio.SimpleAction.new("toggle-favorites", None)
        toggle_favorites_action.connect("activate", self.on_toggle_favorites)
        self.add_action(toggle_favorites_action)

        clipboard: Gdk.Clipboard = self.get_primary_clipboard()
        clipboard.connect("changed", self.on_clipboard_changed)

    def _get_theme_colors(self) -> str:
        """Get word and sentence colors based on current theme."""
        if self._style_manager.get_dark():
            return base.DARK_MODE_SENTENCE_COLOR
        else:
            return base.LIGHT_MODE_SENTENCE_COLOR

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

    def on_paste_search(self, _action=None, _param=None):
        """Search text in clipboard."""
        clipboard = Gdk.Display.get_default().get_clipboard()

        def on_paste(_clipboard: Gdk.Clipboard, result: Gio.AsyncResult):
            """Callback for the clipboard paste."""
            try:
                text = clipboard.read_text_finish(result)
                if text is not None:
                    text = base.clean_search_terms(text)
                if text and text.strip() and not text.isspace():
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
        if self._wn_wordlist:
            random_word = random.choice(self._wn_wordlist)
            random_word = random_word.replace("_", " ")
            self.trigger_search(random_word)
        else:
            # Fallback - show a message that wordlist is still loading
            self._new_error(_("Wordlist Loading"), _("The word list is still loading. Please try again in a moment."))

    def on_search_selected(self, _action, _param):
        """Search selected text from inside or outside the window."""
        self.trigger_search(self._primary_clipboard_text)

    def on_toggle_favorites(self, _action, _param):
        """Toggle between showing all history and favorites only."""
        self._toggle_favorites_filter()

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
                    GLib.idle_add(self._clear_definitions)

                    out = self._search(text)

                    if out is None:
                        status = SearchStatus.RESET
                        continue

                    def validate_result(text, result_data) -> Literal[SearchStatus.SUCCESS]:
                        # Add to history (with delay for live search)
                        if Settings.get().live_search:
                            self._add_to_history_delayed(text)
                        else:
                            self._add_to_history(text)

                        GLib.idle_add(self._populate_definitions, result_data)
                        return SearchStatus.SUCCESS

                    if out["result"] is not None:
                        status = validate_result(text, out["result"])
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
            suggestions = process.extract(
                self._searched_term,
                self._wn_wordlist if self._wn_wordlist else [],
                limit=5,
                scorer=fuzz.QRatio,
            )

            suggestion_links = [
                f'<a href="search;{suggestion.replace("_", " ")}">{suggestion.replace("_", " ")}</a>'
                for suggestion, score, _ in suggestions
                if score > 70
            ]

            if suggestion_links:
                suggestions_markup = f"Did you mean: {', '.join(suggestion_links)}?"
                GLib.idle_add(self._search_fail_description_label.set_markup, suggestions_markup)
                GLib.idle_add(self._search_fail_description_label.show)
            else:
                GLib.idle_add(self._search_fail_description_label.set_markup, "")
                GLib.idle_add(self._search_fail_description_label.hide)

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

    def queue_auto_paste(self):
        """Queue auto-paste or execute it immediately if window is active."""
        if self.props.is_active:
            GLib.idle_add(self.on_paste_search)
        else:
            self._auto_paste_queued = True

    def _on_is_active_changed(self, *_args):
        """Handle window becoming active and execute queued auto-paste if needed."""
        if self._auto_paste_queued and self.props.is_active:
            self._auto_paste_queued = False
            GLib.idle_add(self.on_paste_search)

    def _on_destroy(self, _window: Gtk.Window):
        """Detect closing of the window."""
        # Cancel any pending history delay timer
        if self._history_delay_timer is not None:
            GLib.source_remove(self._history_delay_timer)
            self._history_delay_timer = None

        # Extract history from the search history store
        history_list = []
        if self._search_history:
            for i in range(self._search_history.get_n_items()):
                item = self._search_history.get_item(i)
                if item:
                    history_list.append(item.term)

        width, height = self.get_default_size()
        settings_to_update = {
            "history": history_list[-10:],
            "window_width": width,
            "window_height": height,
        }
        Settings.get().batch_update(settings_to_update)

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
        """Clear non-favorited items from the search history."""
        # Remove non-favorited items from the UI store
        for i in reversed(range(self._search_history.get_n_items())):
            item = self._search_history.get_item(i)
            if not item.is_favorite:
                self._search_history.remove(i)

        self._update_clear_button_sensitivity()

    def _update_clear_button_sensitivity(self):
        """Update the sensitivity of the clear history button."""
        has_history = self._search_history.get_n_items() > 0 if self._search_history else False
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

    def _on_history_item_activated(self, _widget, row: Gtk.ListBoxRow):
        """Handle history item clicks."""
        index = row.get_index()
        history_object: HistoryObject = self._search_history.get_item(index)
        if history_object:
            self.trigger_search(history_object.term)

    def _on_history_items_changed(self, store, position, removed, added):
        """Apply styling to newly added rows."""
        # Only run for additions
        if added > 0:
            GLib.idle_add(self._apply_styling_to_new_rows, store, position, added)

    def _apply_styling_to_new_rows(self, store, position, added):
        """Wait for rows to be created, then apply styling."""
        for i in range(position, position + added):
            item = store.get_item(i)
            row = self._history_listbox.get_row_at_index(i)
            if row:
                self._update_row_visuals(row, item)
        return False  # Do not repeat

    def _on_retry_clicked(self, _widget):
        """Handle retry button click in network failure page."""
        self._wn_downloader.delete_wn()
        self._start_download()

    def _add_to_queue(self, text: str, pass_check: bool = False):
        """Add search term to queue."""
        if self._search_queue:
            self._search_queue.pop(0)
        self._search_queue.append(text)

        if self._active_thread is None:
            # If there is no active thread, create one and start it.
            self._active_thread = threading.Thread(target=self.threaded_search, args=[pass_check], daemon=True)
            self._active_thread.start()

    def _add_to_history(self, text):
        """Add text to history, moving it to the top if it already exists."""
        # Remove if it exists to avoid duplicates
        for i in range(self._search_history.get_n_items()):
            item = self._search_history.get_item(i)
            if item.term == text:
                self._search_history.remove(i)
                break

        # Add to the top
        is_favorite = Settings.get().is_favorite(text)
        history_object = HistoryObject(text, is_favorite)
        self._search_history.insert(0, history_object)

        self._update_clear_button_sensitivity()

    def _add_to_history_delayed(self, text):
        """Add text to history after a 2-seconds delay, cancelling any previous delay."""
        # Cancel any existing timer
        if self._history_delay_timer is not None:
            GLib.source_remove(self._history_delay_timer)
            self._history_delay_timer = None

        # Store the text to be added
        self._pending_history_text = text

        # Set up a new timer to add to history after 2 seconds (2000ms)
        self._history_delay_timer = GLib.timeout_add(2000, self._execute_delayed_history_add)

    def _execute_delayed_history_add(self):
        """Execute the delayed history addition."""
        if self._pending_history_text is not None:
            self._add_to_history(self._pending_history_text)
            self._pending_history_text = None

        self._history_delay_timer = None
        return False  # Don't repeat the timer

    def _on_speak_clicked(self, _button):
        """Say the search entry out loud with espeak speech synthesis."""
        base.read_term(
            self._searched_term,
            speed="120",
            accent=Settings.get().pronunciations_accent.code,
        )

    def _create_label(self, element):
        """Create labels for history list."""
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, visible=True, spacing=8)

        # Main content box for the term
        content_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, visible=True)
        content_box.set_hexpand(True)

        label = Gtk.Label(
            label=element.term,
            margin_top=8,
            margin_bottom=8,
            margin_start=8,
            margin_end=8,
            halign=Gtk.Align.START,
        )
        content_box.append(label)

        # Favorite button
        favorite_button = Gtk.Button(
            icon_name="starred-symbolic" if element.is_favorite else "non-starred-symbolic",
            margin_top=4,
            margin_bottom=4,
            margin_end=4,
            valign=Gtk.Align.CENTER,
        )
        favorite_button.add_css_class("flat")
        favorite_button.add_css_class("circular")

        # Connect the favorite button click
        favorite_button.connect("clicked", self._on_favorite_toggled, element)

        box.append(content_box)
        box.append(favorite_button)

        return box

    def _on_favorite_toggled(self, button: Gtk.Button, item: HistoryObject):
        """Toggle favorite status for a term and update the UI dynamically."""
        settings = Settings.get()

        # The new state is the opposite of the current state
        is_now_favorite = not item.is_favorite
        item.is_favorite = is_now_favorite

        if is_now_favorite:
            settings.add_favorite(item.term)
        else:
            settings.remove_favorite(item.term)

        # Get the row and update its visuals
        row = button.get_ancestor(Gtk.ListBoxRow)
        if row:
            self._update_row_visuals(row, item)

    def _update_row_visuals(self, row: Gtk.ListBoxRow, item: HistoryObject):
        """Update the icon and visibility of a history row."""
        # Update favorite button icon
        box = row.get_child()
        favorite_button: Gtk.ToggleButton = box.get_last_child()
        favorite_button.set_icon_name("starred-symbolic" if item.is_favorite else "non-starred-symbolic")

        # Update CSS class
        if item.is_favorite:
            row.add_css_class("favorite-item")
        else:
            row.remove_css_class("favorite-item")

        # Handle visibility when the favorites filter is active
        row.set_visible(not self._show_favorites_only or item.is_favorite)

    def _toggle_favorites_filter(self):
        """Toggle between showing all history and favorites only."""
        self._show_favorites_only = not self._show_favorites_only
        self._favorites_filter_button.set_active(self._show_favorites_only)
        self._favorites_filter_button.set_icon_name(
            "starred-symbolic" if self._show_favorites_only else "non-starred-symbolic"
        )

        for i in range(self._search_history.get_n_items()):
            item = self._search_history.get_item(i)
            row = self._history_listbox.get_row_at_index(i)
            if row:
                row.set_visible(not self._show_favorites_only or item.is_favorite)

    def _new_error(self, primary_text, secondary_text) -> None:
        """Show an error dialog."""
        dialog = Adw.AlertDialog.new(primary_text, secondary_text)
        dialog.add_response("dismiss", _("Dismiss"))
        dialog.choose(self)

    def _page_switch(self, page: str) -> bool:
        """Switch main stack pages."""
        utils.log_info(f"Switching to page: {page}")
        if page == "content_page":
            GLib.idle_add(self._main_scroll.get_vadjustment().set_value, 0)
        GLib.idle_add(self._main_stack.set_visible_child_name, page)
        return False

    def _search(self, search_text: str) -> dict[str, Any] | None:
        """Clean input text, give errors and pass data to formatter."""
        text = base.clean_search_terms(search_text)
        if not text == "" and not text.isspace():
            if self._wn_instance:
                return base.format_output(
                    text,
                    self._wn_instance,
                    accent=Settings.get().pronunciations_accent.code,
                )
            else:
                # WordNet instance not ready yet
                return None
        if not Settings.get().live_search:
            GLib.idle_add(
                self._new_error,
                _("Invalid input"),
                _("Nothing definable was found in your search input"),
            )
        self._searched_term = None
        return None

    def _update_completions(self, text):
        """Update completions from wordlist."""
        while self._completion_request_count > 0:
            completer_liststore = Gtk.ListStore(str)
            _complete_list = []

            # Only provide completions if wordlist is loaded
            if self._wn_wordlist:
                for item in self._wn_wordlist:
                    if len(_complete_list) >= 10:
                        break
                    item = item.replace("_", " ")
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
        """Download and initialize WordNet data."""
        self._set_header_sensitive(False)

        # Step 1 & 2: Check if database exists
        if self._wn_downloader.check_status():
            # Step 3: Database exists, try to init wordnet and load word list
            self._init_wordnet()
        else:
            # Step 4: Database not present, download it
            self._start_download()

    def _start_download(self):
        """Start the WordNet download process."""
        self._page_switch(Page.DOWNLOAD)
        self.download_status_page.set_description(_("Downloading WordNet…"))
        threading.Thread(target=self._download_wordnet_thread, daemon=True).start()

    def _init_wordnet(self):
        """Initialize WordNet instance."""

        def handle_init_failure():
            """Called if WordNet init fails - trigger download."""
            GLib.idle_add(self._handle_init_failure)

        wn_future = base.get_wn_instance(handle_init_failure)
        wn_future.add_done_callback(self._on_wordnet_init_complete)

    def _handle_init_failure(self):
        """Handle WordNet initialization failure by deleting and re-downloading."""
        self._wn_downloader.delete_wn()
        self._start_download()

    def _on_wordnet_init_complete(self, future):
        """Handle completion of WordNet initialization."""
        if future.exception():
            # Exception already handled by the reloader callback
            return

        try:
            self._wn_instance = future.result()
            if not self._wn_instance:
                utils.log_warning("WordNet instance is None, triggering download")
                self._handle_init_failure()
                return

            # WordNet instance is ready - proceed to welcome screen
            self._complete_initialization()

            # Start loading wordlist in background using _threadpool
            wordlist_future = base.get_wn_wordlist(self._wn_instance)
            wordlist_future.add_done_callback(self._on_wordlist_loaded)

        except Exception as e:
            utils.log_warning(f"Error getting WordNet instance: {e}")
            self._handle_init_failure()

    def _on_wordlist_loaded(self, future):
        """Handle completion of wordlist loading."""
        if future.exception():
            utils.log_error(f"Error loading wordlist: {future.exception()}")
            return

        try:
            wordlist = future.result()
            GLib.idle_add(self._on_wordlist_loaded_success, wordlist)
        except Exception as e:
            utils.log_error(f"Error getting wordlist result: {e}")

    def _on_wordlist_loaded_success(self, wordlist):
        """Handle successful wordlist loading."""
        self._wn_wordlist = wordlist
        utils.log_info(f"Wordlist loaded with {len(self._wn_wordlist)} words. Completions now available.")

    def _complete_initialization(self):
        """Complete the initialization process and show the welcome screen."""
        self._set_header_sensitive(True)
        self._page_switch(Page.WELCOME)

        # Handle initial actions
        if self.lookup_term:
            self.trigger_search(self.lookup_term)
        elif Settings.get().auto_paste_on_launch or self.auto_paste_requested:
            self.queue_auto_paste()
        self._search_entry.grab_focus_without_selecting()

    def _download_wordnet_thread(self):
        """Download WordNet in a background thread."""
        try:
            self._wn_downloader.download(ProgressUpdater)
            GLib.idle_add(self._on_download_complete)
        except Error as err:
            GLib.idle_add(self._on_download_failed, err)

    def _on_download_complete(self):
        """Handle successful WordNet download."""
        # Step 5: Download complete, go to Welcome screen and load word list
        self.download_status_page.set_title(_("Ready."))
        self._init_wordnet()

    def _on_download_failed(self, error):
        """Handle failed WordNet download."""
        self._network_fail_status_page.set_description(f"<small><tt>Error: {error}</tt></small>")
        utils.log_warning(error)
        self._page_switch(Page.NETWORK_FAIL)

    def _clear_definitions(self) -> None:
        """Clear all definitions from the listbox."""
        while (child := self._definitions_listbox.get_first_child()) is not None:
            self._definitions_listbox.remove(child)

    def _create_definition_widget(self, pos: str, synsets: list[dict[str, Any]]) -> Gtk.Widget:
        """Create a widget for a part of speech with its definitions."""
        # Main container for this part of speech
        pos_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=12,
            margin_top=12,
            margin_bottom=12,
            margin_start=12,
            margin_end=12,
        )

        # Create the part of speech header
        pos_header = Gtk.Label()
        pos_header.set_markup(f"<span size='large' weight='bold'>{pos}</span>")
        pos_header.set_xalign(0.0)
        pos_box.append(pos_header)

        # Group synsets by name
        synset_groups: dict[str, list[dict[str, Any]]] = {}
        for synset in sorted(synsets, key=lambda k: k["name"]):
            name = synset["name"]
            if name not in synset_groups:
                synset_groups[name] = []
            synset_groups[name].append(synset)

        # Create definition entries
        sentence_color = self._get_theme_colors()

        # Track the overall definition number across all synset groups
        overall_definition_number = 1
        total_synsets = len([s for group in synset_groups.values() for s in group])

        for synset_name, group_synsets in synset_groups.items():
            definition_number = 1  # Reset definition number for display

            # Add synset name header if different from the main term
            if len(synset_groups) > 1:
                synset_header = Gtk.Label()
                synset_header.set_markup(f"<span weight='bold'>{synset_name}</span>")
                synset_header.set_xalign(0.0)
                synset_header.set_margin_top(8)
                pos_box.append(synset_header)

            for synset in group_synsets:
                # Definition container with horizontal layout for number and content
                def_main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
                def_main_box.set_margin_start(12)

                # Definition number as a separate widget
                number_label = Gtk.Label()
                number_label.set_markup(f"<b>{definition_number}</b>")
                number_label.set_valign(Gtk.Align.START)
                number_label.set_margin_top(2)
                number_label.set_size_request(20, -1)  # Fixed width for alignment
                def_main_box.append(number_label)

                # Content container (definition, examples, related words)
                content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
                content_box.set_hexpand(True)

                # Definition text
                def_label = Gtk.Label()
                def_label.set_markup(f'<span size="large">{escape(synset["definition"])}</span>')
                def_label.set_wrap(True)
                def_label.set_xalign(0.0)
                def_label.set_selectable(True)
                def_label.set_extra_menu(self._def_extra_menu_model)

                # Double-click to search support
                click = Gtk.GestureClick.new()
                click.connect("pressed", self._on_def_press_event)
                click.connect("stopped", self._on_def_stop_event)
                def_label.add_controller(click)

                content_box.append(def_label)

                # Examples
                for example in synset.get("examples", []):
                    example_label = Gtk.Label(
                        label=f'<span foreground="{sentence_color}" style="italic">{example}</span>',
                        use_markup=True,
                        wrap=True,
                        xalign=0.0,
                        selectable=True,
                    )
                    example_label.set_extra_menu(self._def_extra_menu_model)

                    # Double-click to search support
                    click = Gtk.GestureClick.new()
                    click.connect("pressed", self._on_def_press_event)
                    click.connect("stopped", self._on_def_stop_event)
                    example_label.add_controller(click)

                    content_box.append(example_label)

                # Related words (synonyms, antonyms, etc.) as buttons
                for relation_type, relation_key in [
                    ("Synonyms", "syn"),
                    ("Antonyms", "ant"),
                    ("Similar to", "sim"),
                    ("Also see", "also_sees"),
                ]:
                    words = synset.get(relation_key, [])
                    if words:
                        relation_box = self._create_relation_widget(relation_type, words)
                        if relation_box:
                            content_box.append(relation_box)

                def_main_box.append(content_box)
                pos_box.append(def_main_box)

                # Add spacing between definitions
                if overall_definition_number < total_synsets:
                    spacer = Gtk.Separator(
                        margin_top=4,
                        margin_bottom=4,
                    )
                    pos_box.append(spacer)

                definition_number += 1
                overall_definition_number += 1

        return pos_box

    def _create_relation_widget(self, relation_type: str, words: list[str]) -> Gtk.Widget | None:
        """Create a widget for related words (synonyms, antonyms, etc.) with buttons."""
        if not words:
            return None

        # Wrap box for inline label and word buttons
        wrap_box = Adw.WrapBox(
            valign=Gtk.Align.START,
            line_spacing=6,
            child_spacing=6,
        )

        # Add the relation type label as the first item
        type_label = Gtk.Label()
        type_label.set_markup(f"<span weight='bold'>{relation_type}:</span>")
        type_label.set_xalign(0.0)
        type_label.set_valign(Gtk.Align.CENTER)
        wrap_box.append(type_label)

        for word in words:
            button = Gtk.Button(label=word, css_classes=["lemma-button"])
            button.connect("clicked", self._on_word_button_clicked, word)
            wrap_box.append(button)

        return wrap_box

    def _on_word_button_clicked(self, _button: Gtk.Button, word: str) -> None:
        """Handle clicking on a word button to search for that word."""
        self._search_entry.set_text(word)
        self._search_entry.emit("activate")

    def _populate_definitions(self, result: dict[str, Any]) -> None:
        """Populate the definitions listbox."""
        self._clear_definitions()

        for pos, synsets in result.items():
            if synsets:  # Only add if there are definitions for this POS
                pos_widget = self._create_definition_widget(pos, synsets)
                self._definitions_listbox.append(pos_widget)
