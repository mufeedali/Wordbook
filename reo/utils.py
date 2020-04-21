"""utils contains a few global variables and essential functions."""
import logging
import traceback
from os.path import dirname, expanduser

CONFIG_FOLD = expanduser('~') + "/.config/reo"
# ^ This is where stuff like settings, Custom Definitions, etc will go.
CDEF_FOLD = CONFIG_FOLD + "/cdef"
# ^ The Folder within reo_fold where Custom Definitions are to be kept.
CONFIG_FILE = CONFIG_FOLD + "/reo.conf"
VERSION = '0.1.0'

logging.basicConfig(format="%(asctime)s - [%(levelname)s] [%(threadName)s] (%(module)s:%(lineno)d) %(message)s")
LOGGER = logging.getLogger()


def boot_to_str(boolean):
    """Convert boolean to string for configuration parser."""
    if boolean is True:
        return "yes"
    return "no"


def get_word_list(wn_version):
    """Get the word list filename depending on the WordNet version."""
    word_list = f"{dirname(__file__)}/data/wn{wn_version}.lzma"
    return word_list


def log_init(debug):
    """Initialize logging."""
    if debug is True:
        level = logging.DEBUG
    else:
        level = logging.WARNING
    LOGGER.setLevel(level)


def log_critical(message):
    LOGGER.critical(message)
    trace = traceback.format_exc()
    if trace.strip() != 'NoneType: None':
        LOGGER.critical(traceback.format_exc())


def log_debug(message):
    LOGGER.debug(message)
    trace = traceback.format_exc()
    if trace.strip() != 'NoneType: None':
        LOGGER.debug(traceback.format_exc())


def log_error(message):
    LOGGER.error(message)
    trace = traceback.format_exc()
    if trace.strip() != 'NoneType: None':
        LOGGER.error(traceback.format_exc())


def log_info(message):
    LOGGER.info(message)
    trace = traceback.format_exc()
    if trace.strip() != 'NoneType: None':
        LOGGER.info(trace)


def log_warning(message):
    LOGGER.warning(message)
    trace = traceback.format_exc()
    if trace.strip() != 'NoneType: None':
        LOGGER.warning(traceback.format_exc())
