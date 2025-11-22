# SPDX-FileCopyrightText: 2016-2025 Mufeed Ali <me@mufeed.dev>
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Constants module for Wordbook.
Contains all pure constant values used throughout the application.
"""

# Resource path for UI files
RES_PATH = "/dev/mufeed/Wordbook"

# WordNet database version information
WN_DB_VERSION: str = "oewn:2024"
WN_FILE_VERSION: str = "oewn-2024"

# Part of speech mapping from WordNet codes to human-readable names
POS_MAP: dict[str, str] = {
    "s": "adjective",
    "n": "noun",
    "v": "verb",
    "r": "adverb",
    "a": "adjective",  # Note: 'a' and 's' both map to adjective
    "t": "phrase",
    "c": "conjunction",
    "p": "adposition",
    "x": "other",
    "u": "unknown",
}

# Color settings for sentence highlighting
DARK_MODE_SENTENCE_COLOR = "cyan"
LIGHT_MODE_SENTENCE_COLOR = "blue"

# Search term cleanup configuration
SEARCH_TERM_CLEANUP_CHARS = '<>"-?`![](){}/:;,'
SEARCH_TERM_REPLACE_CHARS = ["(", ")", "<", ">", "[", "]", "&", "\\", "\n"]
