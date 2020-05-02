"""utils contains a few global variables and essential functions."""
import logging
import os
import traceback

VERSION = '0.1.0'

HOME = os.path.expanduser('~')
LOCAL_FOLD = os.path.join(os.environ.get("XDG_DATA_HOME", os.path.join(HOME, ".local", "share")), "reo")
CDEF_FOLD = os.path.join(LOCAL_FOLD, "cdef")
CONFIG_FOLD = os.path.join(os.environ.get("XDG_CONFIG_HOME", os.path.join(HOME, ".config")), "reo")
CONFIG_FILE = os.path.join(CONFIG_FOLD, "reo.conf")

logging.basicConfig(format="%(asctime)s - [%(levelname)s] [%(threadName)s] (%(module)s:%(lineno)d) %(message)s")
LOGGER = logging.getLogger()


def boot_to_str(boolean):
    """Convert boolean to string for configuration parser."""
    if boolean is True:
        return "yes"
    return "no"


def get_word_list(wn_version):
    """Get the word list filename depending on the WordNet version."""
    word_list = f"{os.path.dirname(__file__)}/data/wn{wn_version}.lzma"
    return word_list


def log_init(debug):
    """Initialize logging."""
    if debug is True:
        level = logging.DEBUG
    else:
        level = logging.WARNING
    LOGGER.setLevel(level)


def log_critical(message):
    """Log a critical error and if possible, its traceback."""
    LOGGER.critical(message)
    trace = traceback.format_exc()
    if trace.strip() != 'NoneType: None':
        LOGGER.critical(traceback.format_exc())


def log_debug(message):
    """Log a debug message and if possible, its traceback."""
    LOGGER.debug(message)
    trace = traceback.format_exc()
    if trace.strip() != 'NoneType: None':
        LOGGER.debug(traceback.format_exc())


def log_error(message):
    """Log an error and if possible, its traceback."""
    LOGGER.error(message)
    trace = traceback.format_exc()
    if trace.strip() != 'NoneType: None':
        LOGGER.error(traceback.format_exc())


def log_info(message):
    """Log a message and if possible, its traceback."""
    LOGGER.info(message)
    trace = traceback.format_exc()
    if trace.strip() != 'NoneType: None':
        LOGGER.info(trace)


def log_warning(message):
    """Log a warning and if possible, its traceback."""
    LOGGER.warning(message)
    trace = traceback.format_exc()
    if trace.strip() != 'NoneType: None':
        LOGGER.warning(traceback.format_exc())
