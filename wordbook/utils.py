# SPDX-FileCopyrightText: 2016-2025 Mufeed Ali <me@mufeed.dev>
# SPDX-License-Identifier: GPL-3.0-or-later

"""
This module provides project-wide utilities, including:
- Global constants for important file paths (CONFIG_DIR, DATA_DIR, etc.).
- A centralized logging setup with helper functions.
"""

from __future__ import annotations

import logging
import os
import traceback
from typing import TYPE_CHECKING

from gi.repository import GLib

if TYPE_CHECKING:
    from logging import Logger

RES_PATH = "/dev/mufeed/Wordbook"

CONFIG_DIR: str = os.path.join(GLib.get_user_config_dir(), "wordbook")
CONFIG_FILE: str = os.path.join(CONFIG_DIR, "wordbook.conf")
DATA_DIR: str = os.path.join(GLib.get_user_data_dir(), "wordbook")
WN_DIR: str = os.path.join(DATA_DIR, "wn")

logging.basicConfig(format="%(asctime)s - [%(levelname)s] [%(threadName)s] (%(module)s:%(lineno)d) %(message)s")
LOGGER: Logger = logging.getLogger()


def log_init(debug: bool) -> None:
    """Initialize logging level based on debug flag."""
    if debug:
        level = logging.DEBUG
    else:
        level = logging.WARNING
    LOGGER.setLevel(level)


def log_critical(message: str) -> None:
    """Log a critical error. If called inside an except block, logs the traceback."""
    LOGGER.critical(message)
    trace = traceback.format_exc()
    if "NoneType: None" not in trace:
        LOGGER.critical(trace)


def log_debug(message: str) -> None:
    """Log a debug message. If called inside an except block, logs the traceback."""
    LOGGER.debug(message)
    trace = traceback.format_exc()
    if "NoneType: None" not in trace:
        LOGGER.debug(trace)


def log_error(message: str) -> None:
    """Log an error. If called inside an except block, logs the traceback."""
    LOGGER.error(message)
    trace = traceback.format_exc()
    if "NoneType: None" not in trace:
        LOGGER.error(trace)


def log_info(message: str) -> None:
    """Log an info message. If called inside an except block, logs the traceback."""
    LOGGER.info(message)
    trace = traceback.format_exc()
    if "NoneType: None" not in trace:
        LOGGER.info(trace)


def log_warning(message: str) -> None:
    """Log a warning. If called inside an except block, logs the traceback."""
    LOGGER.warning(message)
    trace = traceback.format_exc()
    if "NoneType: None" not in trace:
        LOGGER.warning(trace)
