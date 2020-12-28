# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2016-2020 Mufeed Ali <fushinari@protonmail.com>
# SPDX-License-Identifier: GPL-3.0-or-later

import configparser
import os

from wordbook import utils


class Settings:
    """Manages all the settings of the application."""

    config = configparser.ConfigParser()
    instance = None

    def __init__(self):
        """Initialize configuration."""
        if not os.path.exists(utils.CONFIG_FILE):
            self.config["General"] = {
                "CustomDefinitions": "yes",
                "LiveSearch": "no",
                "DoubleClick": "no",
                "ConfigVersion": "3",
                "PronunciationsAccent": "us",
            }
            self.config["UI"] = {
                "DarkUI": "yes",
                "DarkFont": "yes",
                "HideWindowButtonsMaximized": "no",
            }
        else:
            self.load_settings()

    @property
    def cdef(self):
        """Get custom definition status."""
        return self.config.getboolean("General", "CustomDefinitions")

    @cdef.setter
    def cdef(self, value):
        """Set custom definition status."""
        self.set_boolean_key("General", "CustomDefinitions", value)

    @property
    def double_click(self):
        """Get whether to search on double click."""
        return self.config.getboolean("General", "DoubleClick")

    @double_click.setter
    def double_click(self, value):
        """Set whether to search on double click."""
        self.set_boolean_key("General", "DoubleClick", value)

    @staticmethod
    def get():
        """Return an instance of Settings"""
        if Settings.instance is None:
            Settings.instance = Settings()
        return Settings.instance

    @property
    def gtk_dark_ui(self):
        """Get GTK theme setting."""
        return self.config.getboolean("UI", "DarkUI")

    @gtk_dark_ui.setter
    def gtk_dark_ui(self, value):
        """Set GTK theme setting."""
        self.set_boolean_key("UI", "DarkUI", value)

    @property
    def gtk_dark_font(self):
        """Get GTK theme setting."""
        return self.config.getboolean("UI", "DarkFont")

    @gtk_dark_font.setter
    def gtk_dark_font(self, value):
        """Set GTK theme setting."""
        self.set_boolean_key("UI", "DarkFont", value)

    @property
    def gtk_max_hide(self):
        """Get whether window buttons should be hidden in maximized state in GTK."""
        return self.config.getboolean("UI", "HideWindowButtonsMaximized")

    @gtk_max_hide.setter
    def gtk_max_hide(self, value):
        """Set whether window buttons should be hidden in maximized state in GTK."""
        self.set_boolean_key("UI", "HideWindowButtonsMaximized", value)

    @property
    def live_search(self):
        """Get whether to enable Live Search."""
        return self.config.getboolean("General", "LiveSearch")

    @live_search.setter
    def live_search(self, value):
        """Set whether to enable Live Search."""
        self.set_boolean_key("General", "LiveSearch", value)

    def load_settings(self):
        """Load settings from file."""

        def rename_section(config, old_name, new_name):
            items = config.items(old_name)
            config.add_section(new_name)
            for item in items:
                config.set(new_name, item[0], item[1])
            config.remove_section(old_name)

        with open(utils.CONFIG_FILE, "r") as file:
            self.config.read_file(file)
        utils.log_info("Version Code: " + self.config.get("General", "ConfigVersion"))

        if self.config.getint("General", "ConfigVersion") < 3:
            utils.log_info("Updating to ConfigVersion 3")

            # Remove old options.
            self.config.remove_section("UI-qt")  # Qt UI removed.
            self.config.remove_option("General", "Debug")  # replaced.

            # Rename existing options.
            rename_section(self.config, "UI-gtk", "UI")

            # Add new options.
            self.config.set("General", "PronunciationsAccent", "us")

            if self.config.getint("General", "ConfigVersion") < 2:
                # Add new option.
                self.set_boolean_key("General", "DoubleClick", False)

            self.config.set("General", "ConfigVersion", "3")  # Set version.
            self.save_settings()  # Save before proceeding.

    @property
    def pronunciations_accent(self):
        """Get pronunciations accent."""
        return self.config.get("General", "PronunciationsAccent")

    @pronunciations_accent.setter
    def pronunciations_accent(self, value):
        """Set pronunciations accent."""
        self.config.set("General", "PronunciationsAccent", value)
        self.save_settings()  # Manually save because set_boolean_key is not called.

    @property
    def pronunciations_accent_value(self):
        """Get pronunciations accent index."""
        if self.pronunciations_accent == "us":
            return 0
        elif self.pronunciations_accent == "gb":
            return 1
        return 0

    @pronunciations_accent_value.setter
    def pronunciations_accent_value(self, value):
        """Set pronunciations accent index."""
        if value == 0:
            self.pronunciations_accent = "us"
        elif value == 1:
            self.pronunciations_accent = "gb"

    def save_settings(self):
        """Save settings."""
        with open(utils.CONFIG_FILE, "w") as file:
            self.config.write(file)

    def set_boolean_key(self, section, key, value):
        """Set a boolean value in the configuration file."""
        self.config[section][key] = utils.boot_to_str(value)
        self.save_settings()
