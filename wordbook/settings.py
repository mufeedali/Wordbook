# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2016-2022 Mufeed Ali <fushinari@protonmail.com>
# SPDX-License-Identifier: GPL-3.0-or-later

import configparser
import json
import os

from wordbook import utils


class Settings:
    """Manages all the settings of the application."""

    config = configparser.ConfigParser()
    instance = None

    def __init__(self):
        """Initialize configuration."""
        if not os.path.exists(utils.CONFIG_FILE):
            self.config["Behavior"] = {
                "CustomDefinitions": "yes",
                "LiveSearch": "yes",
                "DoubleClick": "no",
                "PronunciationsAccent": "us",
            }
            self.config["Appearance"] = {
                "ForceDarkMode": "yes",
            }
            self.config["Misc"] = {
                "ConfigVersion": "6",
                "History": "[]",
            }
        else:
            self.load_settings()

    @property
    def cdef(self):
        """Get custom definition status."""
        return self.config.getboolean("Behavior", "CustomDefinitions")

    @cdef.setter
    def cdef(self, value):
        """Set custom definition status."""
        self.set_boolean_key("Behavior", "CustomDefinitions", value)

    @property
    def double_click(self):
        """Get whether to search on double click."""
        return self.config.getboolean("Behavior", "DoubleClick")

    @double_click.setter
    def double_click(self, value):
        """Set whether to search on double click."""
        self.set_boolean_key("Behavior", "DoubleClick", value)

    @staticmethod
    def get():
        """Return an instance of Settings"""
        if Settings.instance is None:
            Settings.instance = Settings()
        return Settings.instance

    @property
    def gtk_dark_ui(self):
        """Get GTK theme setting."""
        return self.config.getboolean("Appearance", "ForceDarkMode")

    @gtk_dark_ui.setter
    def gtk_dark_ui(self, value):
        """Set GTK theme setting."""
        self.set_boolean_key("Appearance", "ForceDarkMode", value)

    @property
    def history(self):
        """Get search history."""
        return json.loads(self.config.get("Misc", "History"))

    @history.setter
    def history(self, value):
        """Set search history."""
        self.config.set("Misc", "History", json.dumps(value))
        self.save_settings()  # Manually save because set_boolean_key is not called.

    @property
    def live_search(self):
        """Get whether to enable Live Search."""
        return self.config.getboolean("Behavior", "LiveSearch")

    @live_search.setter
    def live_search(self, value):
        """Set whether to enable Live Search."""
        self.set_boolean_key("Behavior", "LiveSearch", value)

    def load_settings(self):
        """Load settings from file."""

        def rename_section(
            config,  # the config to modify
            old_name,  # the old section name
            new_name,  # the new section name
        ):
            """Rename a section in the config."""
            items = config.items(old_name)
            config.add_section(new_name)
            for item in items:
                config.set(new_name, item[0], item[1])
            config.remove_section(old_name)

        def mv_option(
            config,  # the config to modify
            option_name,  # the option to move
            section,  # the section to move from
            new_section=None,  # the section to move to
            new_option_name=None,  # the new option name
            new_value=None,  # the new value
        ):
            """Move an option from one section to another."""
            if new_section is None:
                new_section = section
            if new_option_name is None:
                new_option_name = option_name
            if new_value is None:
                new_value = config.get(section, option_name)
            config.set(new_section, new_option_name, new_value)
            config.remove_option(section, option_name)

        with open(utils.CONFIG_FILE, "r") as file:
            self.config.read_file(file)

        config_version = int(
            self.config.get(
                "Misc",
                "ConfigVersion",
                fallback=self.config.get("General", "ConfigVersion", fallback="6")
            )
        )

        utils.log_info(f"Version Code: {config_version}")
        # Migrating older config files.
        if config_version != 6:
            if config_version == 1:
                # Add new option.
                self.set_boolean_key("General", "DoubleClick", False)
                self.config.set("General", "ConfigVersion", "2")

            if config_version == 2:
                # Remove old options.
                self.config.remove_section("UI-qt")  # Qt UI removed.
                self.config.remove_option("General", "Debug")  # replaced.

                # Rename existing options.
                rename_section(self.config, "UI-gtk", "UI")

                # Add new options.
                self.config.set("General", "PronunciationsAccent", "us")

                self.config.set("General", "ConfigVersion", "3")  # Set version.

            # Remove ability to hide window buttons when maximized.
            if config_version == 3:
                utils.log_info("Updating to ConfigVersion 4")
                self.config.remove_option("UI", "HideWindowButtonsMaximized")
                self.config.set("General", "ConfigVersion", "4")

            if config_version == 4:
                utils.log_info("Updating to ConfigVersion 5")
                self.config.add_section("Misc")
                self.config.set("Misc", "History", "[]")
                self.config.set("General", "ConfigVersion", "5")

            if config_version == 5:
                utils.log_info("Updating to ConfigVersion 6")

                mv_option(self.config, "DarkUI", "UI", new_option_name="ForceDarkMode")
                self.config.remove_option("UI", "DarkFont")

                # Rename existing options.
                rename_section(self.config, "General", "Behavior")
                rename_section(self.config, "UI", "Appearance")

                mv_option(
                    self.config, "ConfigVersion", "Behavior", "Misc", new_value="6"
                )

            self.save_settings()  # Save before proceeding.

    @property
    def pronunciations_accent(self):
        """Get pronunciations accent."""
        return self.config.get("Behavior", "PronunciationsAccent")

    @pronunciations_accent.setter
    def pronunciations_accent(self, value):
        """Set pronunciations accent."""
        self.config.set("Behavior", "PronunciationsAccent", value)
        self.save_settings()  # Manually save because set_boolean_key is not called.

    @property
    def pronunciations_accent_value(self):
        """Get pronunciations accent index."""
        if self.pronunciations_accent == "us":
            return 0

        if self.pronunciations_accent == "gb":
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
