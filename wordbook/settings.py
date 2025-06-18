# SPDX-FileCopyrightText: 2016-2025 Mufeed Ali <me@mufeed.dev>
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import json
import os
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, field_validator

from wordbook import utils


class PronunciationAccent(Enum):
    """Enumeration of supported pronunciation accents."""

    US = ("us", "American English")
    GB = ("gb", "British English")

    def __init__(self, code: str, display_name: str):
        self.code = code
        self.display_name = display_name

    @classmethod
    def from_code(cls, code: str) -> "PronunciationAccent":
        """Get accent enum from code string."""
        for accent in cls:
            if accent.code == code:
                return accent
        return cls.US  # Default fallback

    @classmethod
    def from_index(cls, index: int) -> "PronunciationAccent":
        """Get accent enum from index."""
        accents = list(cls)
        if 0 <= index < len(accents):
            return accents[index]
        return cls.US  # Default fallback

    @property
    def index(self) -> int:
        """Get the index of this accent in the enum."""
        return list(PronunciationAccent).index(self)


class BehaviorSettings(BaseModel):
    """Settings related to application behavior."""

    custom_definitions: bool = Field(default=True, description="Enable custom definitions")
    live_search: bool = Field(default=True, description="Enable live search")
    double_click: bool = Field(default=False, description="Search on double click")
    pronunciations_accent: str = Field(default="us", description="Pronunciation accent")
    auto_paste_on_launch: bool = Field(default=False, description="Auto paste from clipboard on launch")

    @field_validator("pronunciations_accent")
    @classmethod
    def validate_accent(cls, accent: str) -> str:
        """Validate pronunciation accent."""
        if accent not in [a.code for a in PronunciationAccent]:
            return PronunciationAccent.US.code  # Default fallback
        return accent


class AppearanceSettings(BaseModel):
    """Settings related to application appearance."""

    force_dark_mode: bool = Field(default=False, description="Force dark mode")


class StateSettings(BaseModel):
    """State settings."""

    history: list[str] = Field(default_factory=list, description="Search history")
    window_width: int = Field(default=400, description="Window width")
    window_height: int = Field(default=600, description="Window height")

    @field_validator("history")
    @classmethod
    def validate_history(cls, v: list[str]) -> list[str]:
        """Validate and limit history size."""
        # Keep only last 10 items
        return v[-10:] if len(v) > 10 else v


class WordbookSettings(BaseModel):
    """Main settings model for Wordbook application."""

    behavior: BehaviorSettings = Field(default_factory=BehaviorSettings)
    appearance: AppearanceSettings = Field(default_factory=AppearanceSettings)
    state: StateSettings = Field(default_factory=StateSettings)


class Settings:
    """Manages all the settings of the application using Pydantic models."""

    _autosave_disabled: bool = False
    _instance: Settings | None = None
    _settings: WordbookSettings

    def __init__(self):
        """Initialize settings."""
        self._autosave_disabled = True
        self._config_file: Path = Path(utils.CONFIG_DIR) / "wordbook.json"

        # Ensure config directory exists
        os.makedirs(utils.CONFIG_DIR, exist_ok=True)

        self._load_settings()
        self._autosave_disabled = False

    def __setattr__(self, name: str, value: Any) -> None:
        """Override setattr to automatically save settings when properties are changed."""
        super().__setattr__(name, value)
        # Auto-save after setting any property
        # Avoid during initialization or for private attributes
        if not self._autosave_disabled and not name.startswith("_"):
            self._save_settings()

    @classmethod
    def get(cls) -> Settings:
        """Get singleton instance of Settings."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _load_settings(self) -> None:
        """Load settings from file."""
        if self._config_file.exists():
            self._load_from_json()
        else:
            # Create default settings
            self._settings = WordbookSettings()
            self._save_settings()

    def _load_from_json(self) -> None:
        """Load settings from JSON file."""
        try:
            with open(self._config_file, "r") as f:
                data = json.load(f)

            self._settings = WordbookSettings.model_validate(data)
            utils.log_info("Loaded settings from JSON configuration")

        except Exception as e:
            utils.log_error(f"Failed to load JSON settings: {e}")
            utils.log_info("Creating default settings")
            self._settings = WordbookSettings()
            self._save_settings()

    def _save_settings(self) -> None:
        """Save settings to JSON file."""
        try:
            with open(self._config_file, "w") as f:
                json.dump(self._settings.model_dump(), f, indent=4)
            utils.log_debug("Settings saved successfully")
        except Exception as e:
            utils.log_error(f"Failed to save settings: {e}")

    # Behavior settings properties
    @property
    def cdef(self) -> bool:
        """Get custom definition status."""
        return self._settings.behavior.custom_definitions

    @cdef.setter
    def cdef(self, value: bool) -> None:
        """Set custom definition status."""
        self._settings.behavior.custom_definitions = value

    @property
    def live_search(self) -> bool:
        """Get live search status."""
        return self._settings.behavior.live_search

    @live_search.setter
    def live_search(self, value: bool) -> None:
        """Set live search status."""
        self._settings.behavior.live_search = value

    @property
    def double_click(self) -> bool:
        """Get double click search status."""
        return self._settings.behavior.double_click

    @double_click.setter
    def double_click(self, value: bool) -> None:
        """Set double click search status."""
        self._settings.behavior.double_click = value

    @property
    def auto_paste_on_launch(self) -> bool:
        """Get auto paste on launch status."""
        return self._settings.behavior.auto_paste_on_launch

    @auto_paste_on_launch.setter
    def auto_paste_on_launch(self, value: bool) -> None:
        """Set auto paste on launch status."""
        self._settings.behavior.auto_paste_on_launch = value

    @property
    def pronunciations_accent(self) -> PronunciationAccent:
        """Get pronunciations accent as enum."""
        return PronunciationAccent.from_code(self._settings.behavior.pronunciations_accent)

    @pronunciations_accent.setter
    def pronunciations_accent(self, value: PronunciationAccent) -> None:
        """Set pronunciations accent by enum value."""
        self._settings.behavior.pronunciations_accent = value.code

    @property
    def pronunciations_accent_enum(self) -> PronunciationAccent:
        """Get pronunciations accent as enum."""
        return PronunciationAccent.from_code(self._settings.behavior.pronunciations_accent)

    # Appearance settings properties
    @property
    def gtk_dark_ui(self) -> bool:
        """Get GTK dark theme setting."""
        return self._settings.appearance.force_dark_mode

    @gtk_dark_ui.setter
    def gtk_dark_ui(self, value: bool) -> None:
        """Set GTK dark theme setting."""
        self._settings.appearance.force_dark_mode = value

    # State settings properties
    @property
    def history(self) -> list[str]:
        """Get search history."""
        return self._settings.state.history.copy()

    @history.setter
    def history(self, value: list[str]) -> None:
        """Set search history."""
        # Validate and limit history
        self._settings.state.history = value[-10:] if len(value) > 10 else value

    def clear_history(self) -> None:
        """Clear search history."""
        self._settings.state.history = []

    @property
    def window_width(self) -> int:
        """Get window width."""
        return self._settings.state.window_width

    @window_width.setter
    def window_width(self, value: int) -> None:
        """Set window width."""
        self._settings.state.window_width = value

    @property
    def window_height(self) -> int:
        """Get window height."""
        return self._settings.state.window_height

    @window_height.setter
    def window_height(self, value: int) -> None:
        """Set window height."""
        self._settings.state.window_height = value

    def batch_update(self, settings_dict: dict[str, Any]) -> None:
        """Update multiple settings at once and save only once."""
        self._autosave_disabled = True
        try:
            for key, value in settings_dict.items():
                if hasattr(self, key):
                    setattr(self, key, value)
                else:
                    utils.log_warning(f"Attempted to set unknown setting: {key}")
        finally:
            self._autosave_disabled = False
        self._save_settings()

    # Utility methods
    def reset_to_defaults(self) -> None:
        """Reset all settings to defaults."""
        utils.log_info("Resetting settings to defaults")
        self._settings = WordbookSettings()
        self._save_settings()
