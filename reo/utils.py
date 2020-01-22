"""utils contains a few global variables and essential functions."""
from os.path import expanduser, dirname

CONFIG_FOLD = expanduser('~') + "/.config/reo"
# ^ This is where stuff like settings, Custom Definitions, etc will go.
CDEF_FOLD = CONFIG_FOLD + "/cdef"
# ^ The Folder within reo_fold where Custom Definitions are to be kept.
CONFIG_FILE = CONFIG_FOLD + "/reo.conf"
VERSION = '0.1.0'


def get_wordlist(wn_version):
    """Get the wordlist filename depending on the WordNet version."""
    WORLDLIST = dirname(__file__) + '/data/wn' + wn_version + '.lzma'
    return WORLDLIST


def bool_str(bool):
    """Convert boolean to string for configparser."""
    if bool is True:
        return "yes"
    else:
        return "no"


def save_settings(config):
    """Save settings."""
    with open(CONFIG_FILE, 'w') as file:
        config.write(file)
