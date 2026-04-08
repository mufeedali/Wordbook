from __future__ import annotations

from collections.abc import Callable

from gi.repository import Gdk, GLib, Gtk, Pango


class SearchCompletion:
    _ENTRY_CLASS = "completion-entry"
    _ENTRY_ACTIVE_CLASS = "completion-active"
    _MAX_ITEMS = 10

    def __init__(
        self,
        parent: Gtk.Widget,
        entry: Gtk.Entry,
        item_provider: Callable[[str, int], list[str]],
        activate: Callable[[str], None],
    ) -> None:
        self._parent = parent
        self._entry = entry
        self._entry.add_css_class(self._ENTRY_CLASS)
        self._item_provider = item_provider
        self._activate = activate
        self._enabled = False
        self._items: list[str] = []
        self._listbox = Gtk.ListBox(selection_mode=Gtk.SelectionMode.SINGLE)
        self._listbox.set_activate_on_single_click(True)
        self._listbox.set_focusable(False)
        self._listbox.connect("row-activated", self._on_row_activated)
        self._scroller = Gtk.ScrolledWindow(
            hscrollbar_policy=Gtk.PolicyType.NEVER,
            propagate_natural_height=True,
        )
        self._scroller.set_focusable(False)
        self._scroller.set_has_frame(False)
        self._scroller.set_child(self._listbox)
        self._popover = Gtk.Popover()
        self._popover.set_autohide(False)
        self._popover.set_has_arrow(False)
        self._popover.set_position(Gtk.PositionType.BOTTOM)
        self._popover.set_focusable(False)
        self._popover.add_css_class("completion-popover")
        self._popover.connect("closed", self._on_popover_closed)
        self._popover.set_child(self._scroller)
        self._popover.set_parent(parent)
        key_controller = Gtk.EventControllerKey.new()
        key_controller.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
        key_controller.connect("key-pressed", self._on_key_pressed)
        self._entry.add_controller(key_controller)

        focus_controller = Gtk.EventControllerFocus.new()
        focus_controller.connect("enter", self._on_entry_focus_enter)
        focus_controller.connect("leave", self._on_entry_focus_leave)
        self._entry.add_controller(focus_controller)

        click_controller = Gtk.GestureClick.new()
        click_controller.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
        click_controller.connect("pressed", self._on_parent_pressed)
        self._parent.add_controller(click_controller)

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = enabled
        if enabled:
            self.update(self._entry.get_text())
        else:
            self.clear()

    def update(self, text: str) -> None:
        if not self._enabled or not text.strip() or not self.entry_has_focus():
            self.hide()
            return

        self._items = self._item_provider(text, self._MAX_ITEMS)
        self._listbox.remove_all()
        if not self._items:
            self.hide()
            return

        for item in self._items:
            self._listbox.append(self._create_row(item))

        if not self._sync_geometry():
            self.hide()
            return

        self._set_entry_active(True)
        self._popover.popup()
        self._popover.present()
        self._entry.grab_focus_without_selecting()

    def clear(self) -> None:
        self._items = []
        self._listbox.remove_all()
        self.hide()

    def hide(self) -> None:
        self._listbox.unselect_all()
        self._set_entry_active(False)
        if self._popover.get_visible():
            self._popover.popdown()

    def handle_key_pressed(self, keyval: int) -> bool:
        if not self._popover.get_visible():
            return False
        if keyval in (Gdk.KEY_Down, Gdk.KEY_Up):
            return self._move_selection(1 if keyval == Gdk.KEY_Down else -1)
        if keyval == Gdk.KEY_Tab:
            index = self._selected_index(fallback_to_first=True)
            if index is None:
                return False
            self._apply_entry_text(self._items[index])
            self.hide()
            return True
        if keyval in (Gdk.KEY_Return, Gdk.KEY_KP_Enter):
            return self._activate_index(self._selected_index())
        if keyval == Gdk.KEY_Escape:
            self.hide()
            return True
        return False

    def _sync_geometry(self) -> bool:
        success, bounds = self._entry.compute_bounds(self._parent)
        if not success:
            return False
        entry_width = max(round(bounds.get_width()), self._entry.get_width(), 1)
        rect = Gdk.Rectangle()
        rect.x = round(bounds.get_x())
        rect.y = round(bounds.get_y() + bounds.get_height()) - 1
        rect.width = entry_width
        rect.height = 1
        self._popover.set_offset(0, 0)
        self._popover.set_pointing_to(rect)
        self._scroller.set_size_request(entry_width, -1)
        return True

    def _move_selection(self, step: int) -> bool:
        if not self._items:
            return False

        index = self._selected_index()
        if index is None:
            index = 0 if step > 0 else len(self._items) - 1
        else:
            index = max(0, min(index + step, len(self._items) - 1))

        row = self._listbox.get_row_at_index(index)
        if row is None:
            return False
        self._listbox.select_row(row)
        return True

    def _apply_entry_text(self, completion_text: str) -> None:
        current_text = self._entry.get_text()
        leading_whitespace = current_text[: len(current_text) - len(current_text.lstrip())]
        updated_text = leading_whitespace + completion_text
        self._entry.set_text(updated_text)
        self._entry.set_position(len(updated_text))

    def _on_row_activated(self, _listbox: Gtk.ListBox, row: Gtk.ListBoxRow) -> None:
        self._activate_index(row.get_index())

    def _on_key_pressed(self, _controller, keyval, _keycode, _state):
        if self.handle_key_pressed(keyval):
            return Gdk.EVENT_STOP
        return Gdk.EVENT_PROPAGATE

    def _on_entry_focus_enter(self, _controller) -> None:
        self.update(self._entry.get_text())

    def _on_entry_focus_leave(self, _controller) -> None:
        GLib.idle_add(self._hide_if_focus_lost)

    def _on_parent_pressed(self, _gesture, _n_press: int, x: float, y: float) -> None:
        clicked_widget = self._parent.pick(x, y, Gtk.PickFlags.DEFAULT)
        if clicked_widget is None:
            self.hide()
            return

        clicked_entry = self._contains_widget(self._entry, clicked_widget)
        if not self._popover.get_visible():
            if clicked_entry:
                GLib.idle_add(self._show_if_possible)
            return

        if clicked_entry or self._contains_widget(self._popover, clicked_widget):
            return

        self.hide()

    def _on_popover_closed(self, _popover: Gtk.Popover) -> None:
        self._set_entry_active(False)

    def _hide_if_focus_lost(self) -> bool:
        if not self.entry_has_focus():
            self.hide()
        return False

    def _show_if_possible(self) -> bool:
        self.update(self._entry.get_text())
        return False

    def entry_has_focus(self) -> bool:
        root = self._entry.get_root()
        focus_widget = None if root is None else root.get_focus()
        return self._contains_widget(self._entry, focus_widget)

    def _set_entry_active(self, active: bool) -> None:
        if active:
            self._entry.add_css_class(self._ENTRY_ACTIVE_CLASS)
            return
        self._entry.remove_css_class(self._ENTRY_ACTIVE_CLASS)

    def _activate_index(self, index: int | None) -> bool:
        if index is None or index < 0 or index >= len(self._items):
            return False
        item = self._items[index]
        self.clear()
        self._activate(item)
        return True

    def _selected_index(self, fallback_to_first: bool = False) -> int | None:
        row = self._listbox.get_selected_row()
        if row is not None:
            index = row.get_index()
            if 0 <= index < len(self._items):
                return index
        if fallback_to_first and self._items:
            return 0
        return None

    @staticmethod
    def _contains_widget(ancestor: Gtk.Widget, widget: Gtk.Widget | None) -> bool:
        return widget == ancestor or (widget is not None and widget.is_ancestor(ancestor))

    @staticmethod
    def _create_row(item: str) -> Gtk.ListBoxRow:
        row = Gtk.ListBoxRow(activatable=True, selectable=True)
        row.set_focusable(False)
        label = Gtk.Label(
            label=item,
            xalign=0,
            ellipsize=Pango.EllipsizeMode.END,
            margin_top=3,
            margin_bottom=3,
            margin_start=10,
            margin_end=10,
        )
        row.set_child(label)
        return row
