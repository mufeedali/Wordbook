"""utils contains a few global variables and essential functions."""
from os.path import expanduser, dirname

CONFIG_FOLD = expanduser('~') + "/.config/reo"
# ^ This is where stuff like settings, Custom Definitions, etc will go.
CDEF_FOLD = CONFIG_FOLD + "/cdef"
# ^ The Folder within reo_fold where Custom Definitions are to be kept.
CONFIG_FILE = CONFIG_FOLD + "/reo.conf"
VERSION = '0.1.0'


def get_word_list(wn_version):
    """Get the word list filename depending on the WordNet version."""
    word_list = f"{dirname(__file__)}/data/wn{wn_version}.lzma"
    return word_list


def boot_to_str(boolean):
    """Convert boolean to string for configuration parser."""
    if boolean is True:
        return "yes"
    return "no"


def save_settings(config):
    """Save settings."""
    with open(CONFIG_FILE, 'w') as file:
        config.write(file)
