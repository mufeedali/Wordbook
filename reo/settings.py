import configparser
import os

from reo import utils


class Settings:
    config = configparser.ConfigParser()
    instance = None

    def __init__(self):
        """Initialize configuration."""
        if not os.path.exists(utils.CONFIG_FILE):
            self.config['General'] = {
                'CustomDefinitions': 'yes',
                'Debug': 'no',
                'LiveSearch': 'no',
            }
            self.config['UI-gtk'] = {
                'DarkUI': 'no',
                'DarkFont': 'no',
                'HideWindowButtonsMaximized': 'no',
            }
            self.config['UI-qt'] = {
                'DarkFont': 'no',
            }
        else:
            self.load_settings()

    def load_settings(self):
        """Load settings."""
        with open(utils.CONFIG_FILE, 'r') as file:
            self.config.read_file(file)

    @property
    def cdef(self):
        """Get custom definition status."""
        return self.config.getboolean('General', 'CustomDefinitions')

    @cdef.setter
    def cdef(self, val):
        """Set custom definition status."""
        self.config['General']['CustomDefinitions'] = utils.boot_to_str(val)
        self.save_settings()

    @property
    def debug(self):
        """Get whether to launch in debug mode."""
        return self.config.getboolean('General', 'Debug')

    @debug.setter
    def debug(self, val):
        """Set whether to launch in debug mode."""
        self.config['General']['Debug'] = utils.boot_to_str(val)
        self.save_settings()

    @staticmethod
    def get():
        """Return an instance of Settings"""
        if Settings.instance is None:
            Settings.instance = Settings()
        return Settings.instance

    @property
    def gtk_dark_ui(self):
        """Get GTK theme setting."""
        return self.config.getboolean('UI-gtk', 'DarkUI')

    @gtk_dark_ui.setter
    def gtk_dark_ui(self, val):
        """Set GTK theme setting."""
        self.config['UI-gtk']['DarkUI'] = utils.boot_to_str(val)
        self.save_settings()

    @property
    def gtk_dark_font(self):
        """Get GTK theme setting."""
        return self.config.getboolean('UI-gtk', 'DarkFont')

    @gtk_dark_font.setter
    def gtk_dark_font(self, val):
        """Set GTK theme setting."""
        self.config['UI-gtk']['DarkFont'] = utils.boot_to_str(val)
        self.save_settings()

    @property
    def gtk_max_hide(self):
        """Get whether window buttons should be hidden in maximized state in GTK."""
        return self.config.getboolean('UI-gtk', 'HideWindowButtonsMaximized')

    @gtk_max_hide.setter
    def gtk_max_hide(self, val):
        """Set whether window buttons should be hidden in maximized state in GTK."""
        self.config['UI-gtk']['HideWindowButtonsMaximized'] = utils.boot_to_str(val)
        self.save_settings()

    @property
    def live_search(self):
        """Get whether to enable Live Search."""
        return self.config.getboolean('General', 'LiveSearch')

    @live_search.setter
    def live_search(self, val):
        """Set whether to enable Live Search."""
        self.config['General']['LiveSearch'] = utils.boot_to_str(val)
        self.save_settings()

    @property
    def qt_dark_font(self):
        """Get Qt theme setting."""
        return self.config.getboolean('UI-qt', 'DarkFont')

    @qt_dark_font.setter
    def qt_dark_font(self, val):
        """Set Qt theme setting."""
        self.config['UI-qt']['DarkFont'] = utils.boot_to_str(val)
        self.save_settings()

    def save_settings(self):
        """Save settings."""
        with open(utils.CONFIG_FILE, 'w') as file:
            self.config.write(file)
