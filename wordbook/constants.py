# SPDX-FileCopyrightText: 2016-2026 Mufeed Ali <me@mufeed.dev>
# SPDX-License-Identifier: GPL-3.0-or-later

"""Constants module for Wordbook."""

def _define(val: str, default: str) -> str:
    return default if val.startswith("@") else val

RES_PATH = "/dev/mufeed/Wordbook"

WN_DB_VERSION = "oewn:2025+"
WN_FILE_VERSION = _define("@WN_FILE_VERSION@", "dev")

POS_MAP = {
    "s": "adjective",
    "n": "noun",
    "v": "verb",
    "r": "adverb",
    "a": "adjective",
    "t": "phrase",
    "c": "conjunction",
    "p": "adposition",
    "x": "other",
    "u": "unknown",
}

DARK_MODE_SENTENCE_COLOR = "cyan"
LIGHT_MODE_SENTENCE_COLOR = "blue"

SEARCH_TERM_CLEANUP_CHARS = '<>"-?`![](){}/:;,'
SEARCH_TERM_REPLACE_CHARS = ["(", ")", "<", ">", "[", "]", "&", "\\", "\n"]
