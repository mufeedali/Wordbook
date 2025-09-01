# SPDX-FileCopyrightText: 2016-2025 Mufeed Ali <me@mufeed.dev>
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import random
import sys
import threading
import time
from enum import Enum, auto
from gettext import gettext as _
from typing import TYPE_CHECKING

from gi.repository import Adw, Gdk, Gio, GLib, GObject, Gtk, Pango
from rapidfuzz import fuzz, process
from wn import Error
from wn.util import ProgressHandler

from wordbook import base, utils
from wordbook.settings import Settings
from wordbook.settings_window import SettingsDialog

if TYPE_CHECKING:
    from typing import Any


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
        self._update_interval = 0.1  # 100ms

    def update(self, n: int = 1, force: bool = False):
        """Update the progress bar, but throttle UI updates to avoid performance issues."""
        self.kwargs["count"] += n

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
        """Update the progress label on the download page."""
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
    _history_stack: Gtk.ListBox = Gtk.Template.Child("history_stack")  # type: ignore
    _history_listbox: Gtk.ListBox = Gtk.Template.Child("history_listbox")  # type: ignore
    _main_stack: Adw.ViewStack = Gtk.Template.Child("main_stack")  # type: ignore
    _toast_overlay: Adw.ToastOverlay = Gtk.Template.Child("toast_overlay")  # type: ignore
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
    _active_thread: threading.Thread | None = None
    _search_cancellation_event: threading.Event | None = None
    _primary_clipboard_text: str | None = None
    _show_favorites_only: bool = False

    # A timer is used to delay adding terms to history during live search,
    # preventing every keystroke from being saved.
    _history_delay_timer = None
    _pending_history_text = None

    # A timer for live search to avoid searching on every keystroke.
    _live_search_delay_timer = None

    # A flag to queue auto-pasting until the window is active.
    _auto_paste_queued: bool = False

    def __init__(self, term="", auto_paste_requested=False, **kwargs):
        """Initializes the main application window."""
        super().__init__(**kwargs)

        self.set_default_size(Settings.get().window_width, Settings.get().window_height)

        self.lookup_term = term
        self.auto_paste_requested = auto_paste_requested

        app = self.get_application()
        if app.development_mode:
            self.get_style_context().add_class("devel")
        self.set_default_icon_name(app.app_id)

        self.setup_widgets()
        self.setup_actions()

    def setup_widgets(self):
        """Sets up widgets, binds models, and connects signal handlers."""
        self._search_history = Gio.ListStore.new(HistoryObject)
        self._history_listbox.bind_model(self._search_history, self._create_history_label)
        self._history_listbox.connect("row-activated", self._on_history_item_activated)
        self._search_history.connect("items-changed", self._on_history_items_changed)

        self.connect("notify::is-active", self._on_is_active_changed)
        self.connect("unrealize", self._on_destroy)
        self._key_ctrlr.connect("key-pressed", self._on_key_pressed)

        self._search_fail_description_label.connect("activate-link", self._on_link_activated)
        self.search_button.connect("clicked", self.on_search_clicked)
        self._search_entry.connect("changed", self._on_entry_changed)
        self._search_entry.connect("icon-press", self._on_entry_icon_clicked)
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

        self._dl_wn()

        # FIXME: Remove use of EntryCompletion
        self.completer = Gtk.EntryCompletion()
        self.completer.set_popup_single_match(True)
        self.completer.set_text_column(0)
        self.completer.set_popup_completion(not Settings.get().live_search)
        self.completer.set_popup_set_width(True)
        self._search_entry.set_completion(self.completer)

        history_items = [HistoryObject(term, Settings.get().is_favorite(term)) for term in Settings.get().history]
        self._search_history.splice(0, 0, history_items)

        self._update_clear_button_sensitivity()

        self.search_button.set_visible(not Settings.get().live_search)
        if not Settings.get().live_search:
            self.set_default_widget(self.search_button)

        def_extra_menu_model = Gio.Menu.new()
        item = Gio.MenuItem.new(_("Search Selected Text"), "win.search-selected")
        def_extra_menu_model.append_item(item)
        self._def_extra_menu_model = def_extra_menu_model

    def setup_actions(self):
        """Sets up the Gio actions and accelerators for the application window."""
        paste_search_action = Gio.SimpleAction.new("paste-search", None)
        paste_search_action.connect("activate", self.on_paste_search)
        self.add_action(paste_search_action)

        # Sidebar toggle action
        toggle_sidebar_action = Gio.SimpleAction.new("toggle-sidebar", None)
        toggle_sidebar_action.connect("activate", self.on_toggle_sidebar)
        self.add_action(toggle_sidebar_action)

        # Menu toggle action
        toggle_menu_action = Gio.SimpleAction.new("toggle-menu", None)
        toggle_menu_action.connect("activate", self.on_toggle_menu)
        self.add_action(toggle_menu_action)

        preferences_action = Gio.SimpleAction.new("preferences", None)
        preferences_action.connect("activate", self.on_preferences)
        self.add_action(preferences_action)

        random_word_action = Gio.SimpleAction.new("random-word", None)
        random_word_action.connect("activate", self.on_random_word)
        self.add_action(random_word_action)

        search_selected_action = Gio.SimpleAction.new("search-selected", None)
        search_selected_action.connect("activate", self.on_search_selected)
        search_selected_action.set_enabled(False)
        self.add_action(search_selected_action)

        toggle_favorites_action = Gio.SimpleAction.new("toggle-favorites", None)
        toggle_favorites_action.connect("activate", self.on_toggle_favorites)
        self.add_action(toggle_favorites_action)

        quit_action = Gio.SimpleAction.new("quit", None)
        quit_action.connect("activate", lambda action, param: self.close())
        self.add_action(quit_action)

        clipboard = self.get_primary_clipboard()
        clipboard.connect("changed", self.on_clipboard_changed)

    def on_clipboard_changed(self, clipboard: Gdk.Clipboard | None):
        """Callback for when the primary clipboard (text selection) changes."""
        clipboard = Gdk.Display.get_default().get_primary_clipboard()

        def on_selection(_clipboard, result):
            try:
                text = clipboard.read_text_finish(result)
                if text and text.strip():
                    self._primary_clipboard_text = text.replace("         ", "").replace("\n", "")
                    self.lookup_action("search-selected").props.enabled = True
                else:
                    self._primary_clipboard_text = None
                    self.lookup_action("search-selected").props.enabled = False
            except GLib.GError:
                self._primary_clipboard_text = None
                self.lookup_action("search-selected").props.enabled = False

        cancellable = Gio.Cancellable()
        clipboard.read_text_async(cancellable, on_selection)

    def on_paste_search(self, _action=None, _param=None):
        """Callback for the 'paste-search' action. Pastes and searches clipboard content."""
        clipboard = Gdk.Display.get_default().get_clipboard()

        def on_paste(_clipboard: Gdk.Clipboard, result: Gio.AsyncResult):
            try:
                text = clipboard.read_text_finish(result)
                if text:
                    text = base.clean_search_terms(text)
                if text and text.strip():
                    self.trigger_search(text)
            except GLib.GError:
                pass  # Ignore errors from empty or non-text clipboard

        cancellable = Gio.Cancellable()
        clipboard.read_text_async(cancellable, on_paste)

    def on_preferences(self, _action, _param):
        """Callback for the 'preferences' action. Shows the settings window."""
        window = SettingsDialog(self)
        window.present(self)

    def on_random_word(self, _action, _param):
        """Callback for the 'random-word' action. Searches for a random word."""
        if self._wn_wordlist:
            random_word = random.choice(self._wn_wordlist).replace("_", " ")
            self.trigger_search(random_word)
        else:
            self._new_error(
                _("Wordlist Loading"),
                _("The word list is still loading. Please try again in a moment."),
            )

    def on_search_selected(self, _action, _param):
        """Callback for the 'search-selected' action. Searches for the currently selected text."""
        self.trigger_search(self._primary_clipboard_text)

    def on_toggle_favorites(self, _action, _param):
        """Callback for the 'toggle-favorites' action. Toggles the history filter."""
        self._toggle_favorites_filter()

    def on_search_clicked(self, _button=None, pass_check=False, text=None):
        """Initiates a search, cancelling any previous search."""
        self._clear_definitions()

        if text is None:
            text = self._search_entry.get_text().strip()

        if not text:
            self._page_switch(Page.WELCOME)
            return

        if self._active_thread and self._active_thread.is_alive():
            if self._search_cancellation_event:
                self._search_cancellation_event.set()

        self._page_switch(Page.SPINNER)

        self._search_cancellation_event = threading.Event()
        self._active_thread = threading.Thread(
            target=self.threaded_search,
            args=[text, pass_check, self._search_cancellation_event],
            daemon=True,
        )
        self._active_thread.start()

    def threaded_search(self, text, pass_check, cancellation_event):
        """
        Performs the search in a background thread.
        This prevents the UI from freezing during network or intensive search operations.
        """
        if cancellation_event.is_set():
            return

        self._searched_term = text

        out = self._search(text)

        if cancellation_event.is_set():
            return

        GLib.idle_add(self._on_search_finished, out)

    def _on_search_finished(self, result):
        """Handles the result of a search on the main thread."""
        if not result:
            self._page_switch(Page.WELCOME)
            return

        status = result.get("status", SearchStatus.SUCCESS if result.get("result") else SearchStatus.FAILURE)

        if status == SearchStatus.SUCCESS:
            self._populate_definitions(result["result"])
            self._term_view.set_text(result["term"].strip())
            self._term_view.set_tooltip_text(result["term"].strip())
            self._pronunciation_view.set_text(result["pronunciation"].strip().replace("\n", ""))
            self._pronunciation_view.set_tooltip_text(result["pronunciation"].strip().replace("\n", ""))
            self._speak_button.set_visible(True)
            self._page_switch(Page.CONTENT)

            if Settings.get().live_search:
                self._add_to_history_delayed(result["term"])
            else:
                self._add_to_history(result["term"])

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
                self._search_fail_description_label.set_markup(suggestions_markup)
                self._search_fail_description_label.show()
            else:
                self._search_fail_description_label.set_markup("")
                self._search_fail_description_label.hide()

            self._page_switch(Page.SEARCH_FAIL)
        else:  # RESET or other cases
            self._page_switch(Page.WELCOME)

        self._active_thread = None

    def trigger_search(self, text):
        """A convenience method to trigger a search from other parts of the app."""
        GLib.idle_add(self._search_entry.set_text, text)
        GLib.idle_add(self.on_search_clicked, None, False, text)

    def _on_def_press_event(self, _click, n_press, _x, _y):
        """Handles the first part of a double-click event on the definition view."""
        if Settings.get().double_click:
            self._doubled = n_press == 2
        else:
            self._doubled = False

    def _on_def_stop_event(self, _click):
        """Handles the second part of a double-click, triggering a search if detected."""
        if self._doubled:
            clipboard = Gdk.Display.get_default().get_primary_clipboard()

            def on_paste(_clipboard, result):
                text = clipboard.read_text_finish(result)
                text = base.clean_search_terms(text)
                if text and text.strip():
                    self.trigger_search(text)

            cancellable = Gio.Cancellable()
            clipboard.read_text_async(cancellable, on_paste)

    def queue_auto_paste(self):
        """Queues an auto-paste action, to be executed once the window is active."""
        if self.props.is_active:
            GLib.idle_add(self.on_paste_search)
        else:
            self._auto_paste_queued = True

    def _on_is_active_changed(self, *_args):
        """Executes a queued auto-paste action when the window becomes active."""
        if self._auto_paste_queued and self.props.is_active:
            self._auto_paste_queued = False
            GLib.idle_add(self.on_paste_search)

    def _on_destroy(self, _window: Gtk.Window):
        """Saves window state and history upon closing the window."""
        if self._history_delay_timer is not None:
            GLib.source_remove(self._history_delay_timer)
            self._history_delay_timer = None

        if self._live_search_delay_timer is not None:
            GLib.source_remove(self._live_search_delay_timer)
            self._live_search_delay_timer = None

        history_list = []
        if self._search_history:
            for i in range(self._search_history.get_n_items()):
                item = self._search_history.get_item(i)
                if item:
                    history_list.append(item.term)

        width, height = self.get_default_size()
        settings_to_update = {
            "history": history_list,
            "window_width": width,
            "window_height": height,
        }
        Settings.get().batch_update(settings_to_update)

    def _on_entry_changed(self, _entry):
        """Handles text changes in the search entry, triggering live search and completions."""
        self._completion_request_count += 1
        if self._completion_request_count == 1:
            threading.Thread(
                target=self._update_completions,
                args=[self._search_entry.get_text()],
                daemon=True,
            ).start()

        # Show/hide clear button based on whether there's text
        text = self._search_entry.get_text()
        self._search_entry.props.secondary_icon_name = "edit-clear-symbolic" if text else ""

        if Settings.get().live_search:
            if self._live_search_delay_timer is not None:
                GLib.source_remove(self._live_search_delay_timer)
            self._live_search_delay_timer = GLib.timeout_add(400, self._execute_delayed_search)

    def _on_entry_icon_clicked(self, _widget, icon_position):
        if icon_position == Gtk.EntryIconPosition.SECONDARY:
            self._search_entry.set_text("")

    def _on_clear_history(self, _widget):
        """Clears non-favorited items from the search history."""
        items_to_remove = []
        for i in range(self._search_history.get_n_items()):
            item = self._search_history.get_item(i)
            if not item.is_favorite:
                items_to_remove.append((i, item))

        if not items_to_remove:
            return

        # Remove items from the history, iterating backwards through the indices
        # to ensure that the indices of items yet to be removed are not affected.
        for i, _item in reversed(items_to_remove):
            self._search_history.remove(i)

        self._update_clear_button_sensitivity()

        toast = Adw.Toast.new(_("History cleared"))
        toast.set_button_label(_("Undo"))
        toast.connect("button-clicked", self._on_undo_clear_history, items_to_remove)
        self._toast_overlay.add_toast(toast)

    def _on_undo_clear_history(self, _toast, items_to_restore):
        """Restores the history that was just cleared."""
        for i, item in items_to_restore:
            self._search_history.insert(i, item)

        self._update_clear_button_sensitivity()

    def _update_clear_button_sensitivity(self):
        """
        Updates the sensitivity of the clear history button based on whether
        there is history, and switches the history stack page if needed.
        """
        has_history = self._search_history.get_n_items() > 0 if self._search_history else False
        self._clear_history_button.set_sensitive(has_history)

        # Switch the stack page to 'empty' if no history
        self._history_stack.set_visible_child_name("list" if has_history else "empty")

    @staticmethod
    def _on_exit_clicked(_widget):
        """Callback for the exit button on the network failure page."""
        sys.exit()

    def _on_link_activated(self, _widget, data):
        """Handles clicks on hyperlinks in the UI, such as 'Did you mean' suggestions."""
        if data.startswith("search;"):
            GLib.idle_add(self._search_entry.set_text, data[7:])
            self.on_search_clicked(text=data[7:])
        return Gdk.EVENT_STOP

    def _on_key_pressed(self, _button, keyval, _keycode, state):
        """Handles key presses for quick search functionality when the search entry is not focused."""
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
        """Handles clicks on history items, triggering a search for that term."""
        index = row.get_index()
        history_object: HistoryObject = self._search_history.get_item(index)
        if history_object:
            self.trigger_search(history_object.term)

    def _on_history_items_changed(self, store, position, removed, added):
        """Applies styling to newly added history rows."""
        if added > 0:
            GLib.idle_add(self._apply_styling_to_new_rows, store, position, added)

    def on_toggle_sidebar(self, action, param):
        """Action handler to toggle the sidebar."""
        self._split_view_toggle_button.set_active(not self._split_view_toggle_button.get_active())

    def on_toggle_menu(self, action, param):
        """Action handler to toggle the menu."""
        self._menu_button.grab_focus()
        self._menu_button.set_active(not self._menu_button.get_active())

    def _apply_styling_to_new_rows(self, store, position, added):
        """Waits for rows to be created, then applies styling."""
        for i in range(position, position + added):
            item = store.get_item(i)
            row = self._history_listbox.get_row_at_index(i)
            if row:
                self._update_row_visuals(row, item)
        return False

    def _on_retry_clicked(self, _widget):
        """Handles the retry button click on the network failure page."""
        self._wn_downloader.delete_wn()
        self._start_download()

    def _add_to_history(self, text):
        """Adds a term to the history, moving it to the top if it already exists."""
        for i in range(self._search_history.get_n_items()):
            item = self._search_history.get_item(i)
            if item.term == text:
                self._search_history.remove(i)
                break

        is_favorite = Settings.get().is_favorite(text)
        history_object = HistoryObject(text, is_favorite)
        self._search_history.insert(0, history_object)

        self._update_clear_button_sensitivity()

    def _add_to_history_delayed(self, text):
        """Adds a term to history after a delay, cancelling any previously pending additions."""
        if self._history_delay_timer is not None:
            GLib.source_remove(self._history_delay_timer)

        self._pending_history_text = text
        self._history_delay_timer = GLib.timeout_add(2000, self._execute_delayed_history_add)

    def _execute_delayed_history_add(self):
        """Executes the delayed history addition."""
        if self._pending_history_text is not None:
            self._add_to_history(self._pending_history_text)
            self._pending_history_text = None

        self._history_delay_timer = None
        return False

    def _execute_delayed_search(self):
        """Executes the delayed search."""
        self.on_search_clicked()
        self._live_search_delay_timer = None
        return False

    def _on_speak_clicked(self, _button):
        """Callback for the speak button. Reads the current term aloud in a background thread."""

        def speak():
            if self._searched_term:
                base.read_term(
                    self._searched_term,
                    speed=120,
                    accent=Settings.get().pronunciations_accent.code,
                )

        threading.Thread(target=speak, daemon=True).start()

    def _create_history_label(self, element):
        """Factory method to create a history row widget."""
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, visible=True, spacing=8)

        content_box = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            visible=True,
            tooltip_text=element.term,
        )
        content_box.set_hexpand(True)

        label = Gtk.Label(
            label=element.term,
            ellipsize=Pango.EllipsizeMode.END,
            margin_top=8,
            margin_bottom=8,
            margin_start=8,
            margin_end=8,
            halign=Gtk.Align.START,
        )
        content_box.append(label)

        favorite_button = Gtk.Button(
            icon_name="starred-symbolic" if element.is_favorite else "non-starred-symbolic",
            margin_top=4,
            margin_bottom=4,
            valign=Gtk.Align.CENTER,
            tooltip_text=_("Toggle Favorite"),
        )
        favorite_button.add_css_class("flat")
        favorite_button.add_css_class("circular")
        favorite_button.connect("clicked", self._on_favorite_toggled, element)

        box.append(content_box)
        box.append(favorite_button)

        return box

    def _on_favorite_toggled(self, button: Gtk.Button, item: HistoryObject):
        """Toggles the favorite status of a history item and updates the UI."""
        settings = Settings.get()
        is_now_favorite = not item.is_favorite
        item.is_favorite = is_now_favorite

        if is_now_favorite:
            settings.add_favorite(item.term)
        else:
            settings.remove_favorite(item.term)

        row = button.get_ancestor(Gtk.ListBoxRow)
        if row:
            self._update_row_visuals(row, item)

    def _update_row_visuals(self, row: Gtk.ListBoxRow, item: HistoryObject):
        """Updates the icon, CSS class, and visibility of a history row."""
        box = row.get_child()
        favorite_button: Gtk.ToggleButton = box.get_last_child()
        favorite_button.set_icon_name("starred-symbolic" if item.is_favorite else "non-starred-symbolic")

        row.add_css_class("history-item")
        if item.is_favorite:
            row.add_css_class("favorite-item")
        else:
            row.remove_css_class("favorite-item")

        row.set_visible(not self._show_favorites_only or item.is_favorite)

    def _toggle_favorites_filter(self):
        """Toggles the visibility of history items based on their favorite status."""
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
        """Shows an error dialog."""
        dialog = Adw.AlertDialog.new(primary_text, secondary_text)
        dialog.add_response("dismiss", _("Dismiss"))
        dialog.choose(self)

    def _page_switch(self, page: str) -> bool:
        """Switches the visible page in the main stack."""
        utils.log_info(f"Switching to page: {page}")
        if page == "content_page":
            GLib.idle_add(self._main_scroll.get_vadjustment().set_value, 0)
        GLib.idle_add(self._main_stack.set_visible_child_name, page)
        return False

    def _search(self, search_text: str) -> dict[str, Any] | None:
        """Cleans input text, passes it to the backend for definition, and handles errors."""
        text = base.clean_search_terms(search_text)
        if text and text.strip():
            if self._wn_instance:
                return base.format_output(
                    text,
                    self._wn_instance,
                    accent=Settings.get().pronunciations_accent.code,
                )
            else:
                return None  # WordNet instance not ready yet
        if not Settings.get().live_search:
            GLib.idle_add(
                self._new_error,
                _("Invalid input"),
                _("Nothing definable was found in your search input"),
            )
        self._searched_term = None
        return None

    def _update_completions(self, text):
        """Updates the search entry's completion model based on the current text."""
        while self._completion_request_count > 0:
            completer_liststore = Gtk.ListStore(str)
            _complete_list = []

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
        """Disables or enables header buttons during long-running operations."""
        self._title_clamp.set_sensitive(status)
        self._split_view_toggle_button.set_sensitive(status)
        self._menu_button.set_sensitive(status)

    def _dl_wn(self):
        """
        Manages the WordNet data download and initialization process.
        This is the main entry point for the application's data setup.
        """
        self._set_header_sensitive(False)

        if self._wn_downloader.check_status():
            self._init_wordnet()
        else:
            self._start_download()

    def _start_download(self):
        """Starts the WordNet download process in a background thread."""
        self._page_switch(Page.DOWNLOAD)
        self.download_status_page.set_description(_("Downloading WordNet…"))
        threading.Thread(target=self._download_wordnet_thread, daemon=True).start()

    def _init_wordnet(self):
        """Initializes the WordNet instance, handling potential failures."""

        def handle_init_failure():
            """Callback passed to the backend to handle initialization failures."""
            GLib.idle_add(self._handle_init_failure)

        wn_future = base.get_wn_instance(handle_init_failure)
        wn_future.add_done_callback(self._on_wordnet_init_complete)

    def _handle_init_failure(self):
        """Handles WordNet initialization failure by deleting the data and re-downloading."""
        self._wn_downloader.delete_wn()
        self._start_download()

    def _on_wordnet_init_complete(self, future):
        """Callback for when WordNet initialization is complete."""
        if future.exception():
            return  # Exception is handled by the reloader callback

        try:
            self._wn_instance = future.result()
            if not self._wn_instance:
                utils.log_warning("WordNet instance is None, triggering download")
                self._handle_init_failure()
                return

            self._complete_initialization()

            wordlist_future = base.get_wn_wordlist(self._wn_instance)
            wordlist_future.add_done_callback(self._on_wordlist_loaded)

        except Exception as e:
            utils.log_warning(f"Error getting WordNet instance: {e}")
            self._handle_init_failure()

    def _on_wordlist_loaded(self, future):
        """Callback for when the wordlist has been loaded."""
        if future.exception():
            utils.log_error(f"Error loading wordlist: {future.exception()}")
            return

        try:
            wordlist = future.result()
            GLib.idle_add(self._on_wordlist_loaded_success, wordlist)
        except Exception as e:
            utils.log_error(f"Error getting wordlist result: {e}")

    def _on_wordlist_loaded_success(self, wordlist):
        """Handles successful wordlist loading."""
        self._wn_wordlist = wordlist
        utils.log_info(f"Wordlist loaded with {len(self._wn_wordlist)} words. Completions now available.")

    def _complete_initialization(self):
        """Finalizes the initialization process and shows the main welcome screen."""
        self._set_header_sensitive(True)
        self._page_switch(Page.WELCOME)

        if self.lookup_term:
            self.trigger_search(self.lookup_term)
        elif Settings.get().auto_paste_on_launch or self.auto_paste_requested:
            self.queue_auto_paste()
        self._search_entry.grab_focus_without_selecting()

    def _download_wordnet_thread(self):
        """Downloads WordNet data in a background thread."""
        try:
            self._wn_downloader.download(ProgressUpdater)
            GLib.idle_add(self._on_download_complete)
        except Error as err:
            GLib.idle_add(self._on_download_failed, err)

    def _on_download_complete(self):
        """Callback for successful WordNet download."""
        self.download_status_page.set_title(_("Ready."))
        self._init_wordnet()

    def _on_download_failed(self, error):
        """Callback for failed WordNet download."""
        self._network_fail_status_page.set_description(f"<small><tt>Error: {error}</tt></small>")
        utils.log_warning(error)
        self._page_switch(Page.NETWORK_FAIL)

    def _clear_definitions(self) -> None:
        """Clears all definitions from the listbox."""
        while (child := self._definitions_listbox.get_first_child()) is not None:
            self._definitions_listbox.remove(child)

    def _create_definition_widget(self, pos: str, synsets: list[dict[str, Any]]) -> Gtk.Widget:
        """Creates a widget to display definitions for a specific part of speech."""
        pos_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=12,
            margin_top=12,
            margin_bottom=12,
            margin_start=12,
            margin_end=12,
        )

        pos_header = Gtk.Label(
            label=pos,
            xalign=0.0,
            use_markup=True,
            css_classes=[
                "pos-header",
            ],
        )
        pos_box.append(pos_header)

        synset_groups: dict[str, list[dict[str, Any]]] = {}
        for synset in sorted(synsets, key=lambda k: k["name"]):
            name = synset["name"]
            if name not in synset_groups:
                synset_groups[name] = []
            synset_groups[name].append(synset)

        overall_definition_number = 1
        total_synsets = len([s for group in synset_groups.values() for s in group])

        for synset_name, group_synsets in synset_groups.items():
            definition_number = 1

            if len(synset_groups) > 1:
                synset_header = Gtk.Label(
                    label=synset_name,
                    use_markup=True,
                    xalign=0.0,
                    margin_top=8,
                    css_classes=[
                        "synset-header",
                    ],
                )
                pos_box.append(synset_header)

            for synset in group_synsets:
                def_main_box = Gtk.Box(
                    orientation=Gtk.Orientation.HORIZONTAL,
                    spacing=12,
                )

                number_label = Gtk.Label(
                    label=str(definition_number),
                    use_markup=True,
                    valign=Gtk.Align.START,
                    margin_top=2,
                    css_classes=[
                        "definition-number",
                    ],
                )
                number_label.set_size_request(20, -1)
                def_main_box.append(number_label)

                content_box = Gtk.Box(
                    orientation=Gtk.Orientation.VERTICAL,
                    spacing=6,
                    hexpand=True,
                )

                def_label = Gtk.Label(
                    label=synset["definition"],
                    wrap=True,
                    xalign=0.0,
                    selectable=True,
                    extra_menu=self._def_extra_menu_model,
                    css_classes=[
                        "definition",
                    ],
                )

                click = Gtk.GestureClick.new()
                click.connect("pressed", self._on_def_press_event)
                click.connect("stopped", self._on_def_stop_event)
                def_label.add_controller(click)

                content_box.append(def_label)

                for example in synset.get("examples", []):
                    example_label = Gtk.Label(
                        label=example,
                        wrap=True,
                        xalign=0.0,
                        selectable=True,
                        extra_menu=self._def_extra_menu_model,
                    )
                    example_label.add_css_class("example-text")

                    click = Gtk.GestureClick.new()
                    click.connect("pressed", self._on_def_press_event)
                    click.connect("stopped", self._on_def_stop_event)
                    example_label.add_controller(click)

                    content_box.append(example_label)

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

                if overall_definition_number < total_synsets:
                    spacer = Gtk.Separator(margin_top=4, margin_bottom=4)
                    pos_box.append(spacer)

                definition_number += 1
                overall_definition_number += 1

        return pos_box

    def _create_relation_widget(self, relation_type: str, words: list[str]) -> Gtk.Widget | None:
        """Creates a widget to display related words (e.g., synonyms) as clickable buttons."""
        if not words:
            return None

        wrap_box = Adw.WrapBox(
            valign=Gtk.Align.START,
            line_spacing=4,
            child_spacing=6,
        )

        type_label = Gtk.Label(
            label=f"{relation_type}:",
            xalign=0.0,
            valign=Gtk.Align.CENTER,
            css_classes=[
                "relation-type",
            ],
        )
        wrap_box.append(type_label)

        for word in words:
            button = Gtk.Button(label=word, css_classes=["lemma-button"])
            button.connect("clicked", self._on_word_button_clicked, word)
            wrap_box.append(button)

        return wrap_box

    def _on_word_button_clicked(self, _button: Gtk.Button, word: str) -> None:
        """Handles clicks on related word buttons, triggering a new search."""
        self._search_entry.set_text(word)
        self._search_entry.emit("activate")

    def _populate_definitions(self, result: dict[str, Any]) -> None:
        """Populates the definitions listbox with the search results."""
        self._clear_definitions()

        for pos, synsets in result.items():
            if synsets:
                pos_widget = self._create_definition_widget(pos, synsets)
                row = Gtk.ListBoxRow(
                    margin_top=4,
                    margin_bottom=4,
                    margin_start=4,
                    margin_end=4,
                )
                row.set_child(pos_widget)
                self._definitions_listbox.append(row)

                # NOTE Apparently `append` is what adds the `activatable` class.
                # So, now that the row has been added, we can remove the class.
                row.remove_css_class("activatable")
