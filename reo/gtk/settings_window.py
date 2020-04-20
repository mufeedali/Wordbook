import os

from gi.repository import Gtk

from reo import base
from reo.settings import Settings

PATH = os.path.dirname(__file__)


@Gtk.Template(filename=f'{PATH}/ui/settings_window.ui')
class SettingsWindow(Gtk.Window):
    __gtype_name__ = 'SettingsWindow'

    cdef_switch = Gtk.Template.Child('cdef_switch')
    debug_switch = Gtk.Template.Child('debug_switch')
    live_search_switch = Gtk.Template.Child('live_search_switch')
    max_hide_switch = Gtk.Template.Child('max_hide_switch')
    dark_ui_switch = Gtk.Template.Child('dark_ui_switch')
    dark_font_switch = Gtk.Template.Child('dark_font_switch')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.cdef_switch.connect("notify::active", self.on_cdef_switch_activate)
        self.debug_switch.connect("notify::active", self.on_debug_switch_activate)
        self.live_search_switch.connect("notify::active", self.on_live_search_activate)
        self.max_hide_switch.connect("notify::active", self.on_max_hide_swtich_activate)
        self.dark_ui_switch.connect("notify::active", self.on_dark_ui_swtich_activate)
        self.dark_font_switch.connect("notify::active", self.on_dark_font_swtich_activate)

    def load_settings(self):
        self.cdef_switch.set_active(Settings.get().cdef)
        self.debug_switch.set_active(Settings.get().debug)
        self.live_search_switch.set_active(Settings.get().live_search)
        self.max_hide_switch.set_active(Settings.get().gtk_max_hide)
        self.dark_ui_switch.set_active(Settings.get().gtk_dark_ui)
        self.dark_font_switch.set_active(Settings.get().gtk_dark_font)

    def on_cdef_switch_activate(self, switch, _gparam):
        Settings.get().cdef = switch.get_active()

    def on_debug_switch_activate(self, switch, _gparam):
        Settings.get().debug = switch.get_active()
        base.log_init(Settings.get().debug)

    def on_live_search_activate(self, switch, _gparam):
        Settings.get().live_search = switch.get_active()

    def on_max_hide_swtich_activate(self, switch, _gparam):
        Settings.get().gtk_max_hide = switch.get_active()

    def on_dark_ui_swtich_activate(self, switch, _gparam):
        Settings.get().gtk_dark_ui = switch.get_active()
        Gtk.Settings.get_default().set_property("gtk-application-prefer-dark-theme", switch.get_active())

    def on_dark_font_swtich_activate(self, switch, _gparam):
        Settings.get().gtk_dark_font = switch.get_active()
