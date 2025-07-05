# SPDX-FileCopyrightText: 2016-2025 Mufeed Ali <me@mufeed.dev>
# SPDX-License-Identifier: GPL-3.0-or-later

"""utils contains a few global variables and essential functions."""

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
    """Initialize logging."""
    if debug is True:
        level = logging.DEBUG
    else:
        level = logging.WARNING
    LOGGER.setLevel(level)


def log_critical(message: str) -> None:
    """Log a critical error and if possible, its traceback."""
    LOGGER.critical(message)
    trace = traceback.format_exc()
    if trace.strip() != "NoneType: None":
        LOGGER.critical(traceback.format_exc())


def log_debug(message: str) -> None:
    """Log a debug message and if possible, its traceback."""
    LOGGER.debug(message)
    trace = traceback.format_exc()
    if trace.strip() != "NoneType: None":
        LOGGER.debug(traceback.format_exc())


def log_error(message: str) -> None:
    """Log an error and if possible, its traceback."""
    LOGGER.error(message)
    trace = traceback.format_exc()
    if trace.strip() != "NoneType: None":
        LOGGER.error(traceback.format_exc())


def log_info(message: str) -> None:
    """Log a message and if possible, its traceback."""
    LOGGER.info(message)
    trace = traceback.format_exc()
    if trace.strip() != "NoneType: None":
        LOGGER.info(trace)


def log_warning(message: str) -> None:
    """Log a warning and if possible, its traceback."""
    LOGGER.warning(message)
    trace = traceback.format_exc()
    if trace.strip() != "NoneType: None":
        LOGGER.warning(traceback.format_exc())
