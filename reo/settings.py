# -*- coding: utf-8 -*-
# Copyright (C) 2016-2020 Mufeed Ali
# SPDX-License-Identifier: GPL-3.0-only or GPL-3.0-or-later
# Author: Mufeed Ali <fushinari@protonmail.com>

import configparser
import os

from reo import utils


class Settings:
    """Manages all the settings of the application including both the GUIs."""
    config = configparser.ConfigParser()
    instance = None

    def __init__(self):
        """Initialize configuration."""
        if not os.path.exists(utils.CONFIG_FILE):
            self.config['General'] = {
                'CustomDefinitions': 'yes',
                'Debug': 'no',
                'LiveSearch': 'no',
                'ConfigVersion': '1',
            }
            self.config['UI-gtk'] = {
                'DarkUI': 'yes',
                'DarkFont': 'yes',
                'HideWindowButtonsMaximized': 'no',
            }
            self.config['UI-qt'] = {
                'DarkFont': 'no',
            }
        else:
            self.load_settings()

    @property
    def cdef(self):
        """Get custom definition status."""
        return self.config.getboolean('General', 'CustomDefinitions')

    @cdef.setter
    def cdef(self, value):
        """Set custom definition status."""
        self.set_boolean_key('General', 'CustomDefinitions', value)

    @property
    def debug(self):
        """Get whether to launch in debug mode."""
        return self.config.getboolean('General', 'Debug')

    @debug.setter
    def debug(self, value):
        """Set whether to launch in debug mode."""
        self.set_boolean_key('General', 'Debug', value)

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
    def gtk_dark_ui(self, value):
        """Set GTK theme setting."""
        self.set_boolean_key('UI-gtk', 'DarkUI', value)

    @property
    def gtk_dark_font(self):
        """Get GTK theme setting."""
        return self.config.getboolean('UI-gtk', 'DarkFont')

    @gtk_dark_font.setter
    def gtk_dark_font(self, value):
        """Set GTK theme setting."""
        self.set_boolean_key('UI-gtk', 'DarkFont', value)

    @property
    def gtk_max_hide(self):
        """Get whether window buttons should be hidden in maximized state in GTK."""
        return self.config.getboolean('UI-gtk', 'HideWindowButtonsMaximized')

    @gtk_max_hide.setter
    def gtk_max_hide(self, value):
        """Set whether window buttons should be hidden in maximized state in GTK."""
        self.set_boolean_key('UI-gtk', 'HideWindowButtonsMaximized', value)

    @property
    def live_search(self):
        """Get whether to enable Live Search."""
        return self.config.getboolean('General', 'LiveSearch')

    @live_search.setter
    def live_search(self, value):
        """Set whether to enable Live Search."""
        self.set_boolean_key('General', 'LiveSearch', value)

    def load_settings(self):
        """Load settings from file."""
        with open(utils.CONFIG_FILE, 'r') as file:
            self.config.read_file(file)
        print("Version Code: " + self.config.get('General', 'ConfigVersion'))

    @property
    def qt_dark_font(self):
        """Get Qt theme setting."""
        return self.config.getboolean('UI-qt', 'DarkFont')

    @qt_dark_font.setter
    def qt_dark_font(self, value):
        """Set Qt theme setting."""
        self.set_boolean_key('UI-qt', 'DarkFont', value)

    def save_settings(self):
        """Save settings."""
        with open(utils.CONFIG_FILE, 'w') as file:
            self.config.write(file)

    def set_boolean_key(self, section, key, value):
        self.config[section][key] = utils.boot_to_str(value)
        self.save_settings()
