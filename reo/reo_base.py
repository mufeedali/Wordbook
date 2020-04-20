"""
reo_base contains the shared code between the Qt5 and Gtk3 frontends.

reo_base is a part of Reo. It contains a few functions that are reusable across
both the UIs.
"""

import html
import logging
import lzma
import os
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache

from reo import utils

_POOL = ThreadPoolExecutor()


def _threadpool(f):
    """Wraps around a function allowing it to run in a separate thread and return a future object."""
    def wrap(*args, **kwargs):
        return (_POOL).submit(f, *args, **kwargs)

    return wrap


def clean_html(data):
    """Convert Pango Markup subset to HTML and cleanup. Not a real converter."""
    replace_list = {
        '<span foreground="': '<font color="',
        '</span>': '</font>',
        '\n': '<br>',
        ' ': '&nbsp;',
        '<font&nbsp;': '<font ',
    }
    for to_replace, replace_with in replace_list.items():
        data = data.replace(to_replace, replace_with)
    return data


def fold_gen():
    """Make required directories if they don't already exist."""
    if not os.path.exists(utils.CONFIG_FOLD):  # check for Reo folder
        os.makedirs(utils.CONFIG_FOLD)  # create Reo folder
    if not os.path.exists(utils.CDEF_FOLD):  # check Custom Definitions folder.
        os.makedirs(utils.CDEF_FOLD)  # create Custom Definitions folder.


@lru_cache(maxsize=None)
def format_close_words(clp, text):
    """Format the similar words list obtained."""
    sub_dict = {
        r'\s+      \s+': r'  ',
        f'  ["]*{text.lower()}["]*$': r'',
        f"(.)  {text.lower()}  (.)": r"\1  \2",
        f'wn: ["]*{text.lower()}["]*  (.)': r"\1",
        f'(.)  "{text.lower()}"  (.)': r"\1  \2",
        r'\s*\n\s*': r'  ',
        r"\s\s+": r", ",
        f'["]+{text.lower()}["]+': r"",
        'wn:[,]*': r''
    }
    for to_replace, replace_with in sub_dict.items():
        sub_re = re.compile(to_replace)
        clp = sub_re.sub(replace_with, clp).strip()
    clp = clp.rstrip()
    return clp


def get_cowfortune():
    """Present cowsay version of fortune easter egg."""
    try:
        cowsay = subprocess.Popen(["cowsay", get_fortune()], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        cowsay.wait()
        if cowsay:
            cst = cowsay.stdout.read().decode()
            return f"<tt>{cst}</tt>"
        return "<tt>Cowsay fail... Too bad...</tt>"
    except OSError as ex:
        fortune_out = "Easter Egg Fail!!! Install 'fortune' or 'fortunemod' and also 'cowsay'."
        print(f"{fortune_out}\n{str(ex)}")
        return f"<tt>{fortune_out}</tt>"


def get_custom_def(text, wordcol, sencol, markup="html"):
    """Present custom definition when available."""
    with open(utils.CDEF_FOLD + '/' + text, 'r') as def_file:
        custom_def_read = def_file.read()
        re_list = {
            "<i>($WORDCOL)</i>": wordcol,
            "<i>($SENCOL)</i>": sencol,
            "($WORDCOL)": wordcol,
            "($SENCOL)": sencol,
            "$WORDCOL": wordcol,
            "$SENCOL": sencol,
        }
        for i, j in re_list.items():
            custom_def_read = custom_def_read.replace(i, j)
    if "\n[warninghide]" in custom_def_read:
        custom_def_read = custom_def_read.replace("\n[warninghide]", "")
        if markup == "pango":
            return clean_pango(custom_def_read)
        return clean_html(custom_def_read)
    if markup == "pango":
        return(clean_pango(custom_def_read) + '\n<span foreground="#e6292f">NOTE: This is a Custom definition. No one '
               'is to be held responsible for errors in this.</span>')
    return(clean_html(custom_def_read) + '\n<font color="#e6292f">NOTE: This is a Custom definition. No one is to be '
           'held responsible for errors in this.</font>')


def get_data(term, word_col, sen_col, markup='html'):
    """Obtain the data to be processed and presented."""
    output = run_processes(term)
    if not output:
        return "Lookup failed. Check logs."
    definition = output[0]
    if not definition == '':
        clean_def = process_definition(definition, term, sen_col, word_col)
        no_def = 0
    else:
        clean_def = f"Couldn't find definition for '{term}'."
        no_def = 1
    pron = output[1]
    clean_pron = " /{0}/".format(pron.strip().replace('\n ', ' '))
    close = output[2]
    clean_close = format_close_words(close, term)
    fail = False
    if term.lower() == 'recursion':
        clean_close = 'recursion'
    if clean_close.strip() == '':
        fail = True
    if clean_pron == '' or clean_pron.isspace():
        final_pron = "Obtaining pronunciation failed."
    else:
        final_pron = f"<b>Pronunciation</b>: <b>{clean_pron}</b>"
    if not fail:
        if no_def == 1:
            final_close = f'<b>Did you mean</b>:<br><i><font color="{word_col}">  {clean_close}</font></i>'
        else:
            final_close = f'<b>Similar Words</b>:<br><i><font color="{word_col}">  {clean_close}</font></i>'
    else:
        final_close = ''
    if markup == "pango":
        final_data = clean_pango(f'{final_pron.strip()}\n{clean_def}\n{final_close.strip()}').replace('&', '&amp;')
    else:
        final_data = clean_html(f"<p>{final_pron.strip()}</p><p>{clean_def}</p><p>{final_close.strip()}</p>")
    return final_data


def get_fortune():
    """Present fortune easter egg."""
    try:
        fortune_process = subprocess.Popen(["fortune", "-a"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        fortune_process.wait()
        fortune_out = fortune_process.stdout.read().decode()
        fortune_out = html.escape(fortune_out, False)
        return f"<tt>{fortune_out}</tt>"
    except OSError as ex:
        fortune_out = "Easter Egg Fail!!! Install 'fortune' or 'fortunemod'."
        print(f"{fortune_out}\n{str(ex)}")
        return f"<tt>{fortune_out}</tt>"


def get_version_info():
    """Present clear version info."""
    print('Reo - ' + utils.VERSION)
    print('Copyright 2016-2020 Mufeed Ali')
    print()
    wn_ver = get_wn_version()
    if wn_ver == '3.1':
        print("WordNet Version 3.1 (2011) (Installed)")
    elif wn_ver == '3.0':
        print("WordNet Version 3.0 (2006) (Installed)")
    print()
    try:
        dict_process = subprocess.Popen(["dict", "-V"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        dict_out = dict_process.stdout.read().decode()
        print(dict_out.strip())
    except OSError as ex:
        print("Looks like missing components. (dict)\n" + str(ex))
    print()
    try:
        espeak_process = subprocess.Popen(["espeak-ng", "--version"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        espeak_process.wait()
        espeak_out = espeak_process.stdout.read().decode()
        print(espeak_out.strip())
    except OSError as ex:
        print("You're missing a few components. (espeak-ng)\n" + str(ex))


@_threadpool
def get_wn_file():
    """Get the WordNet wordlist according to WordNet version."""
    wn_version = get_wn_version()
    wn = str(lzma.open(utils.get_word_list(wn_version), 'r').read()).split('\\n')
    return (wn_version, wn)


@lru_cache(maxsize=None)
def get_wn_version():
    """Check version of WordNet."""
    try:
        check_process = subprocess.Popen(["dict", "-d", "wn", "test"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        check_out = check_process.stdout.read().decode()
    except OSError as ex:
        print("Error with dict. Error")
        print(ex)
        return '3.1'
    if not check_out.find('1 definition found\n\nFrom WordNet (r) 3.0 (2006) [wn]:\n') == -1:
        return '3.0'
    return '3.1'


def log_init(debug):
    """Initialize logging."""
    if debug is True:
        level = logging.DEBUG
    else:
        level = logging.WARNING
    logging.basicConfig(level=level,
                        format="%(asctime)s - [%(levelname)s] [%(threadName)s] (%(module)s:%(lineno)d) %(message)s")


def process_definition(definition, term, sen_col, word_col):
    """Format the definition obtained from 'dict'."""
    definition = definition.replace('1 definition found\n\nFrom WordNet (r) 3.0 (2006) [wn]:\n', '')
    definition = definition.replace('1 definition found\n\nFrom WordNet (r) 3.1 (2011) [wn]:\n', '')
    definition = html.escape(definition, False)
    term_in_wn = re.search("  " + term, definition, flags=re.IGNORECASE).group(0) or term
    definition = definition.replace(term_in_wn + '\n', '')
    logging.info("Searching %s", term_in_wn.strip())
    re_list = {
        r'[ \t\r\f\v]+n\s+': f'<b>{term_in_wn}</b> ~ <i>noun</i>:\n      ',
        r'[ \t\r\f\v]+adv\s+': f'<b>{term_in_wn}</b> ~ <i>adverb</i>:\n      ',
        r'[ \t\r\f\v]+adj\s+': f'<b>{term_in_wn}</b> ~ <i>adjective</i>:\n      ',
        r'[ \t\r\f\v]+v\s+': f'<b>{term_in_wn}</b> ~ <i>verb</i>:\n      ',
        r'([-]+)\s+      \s+': r'\1',
        r'\s+      \s+': r' ',
        r'"$': r'</font>',
        r'\s+(\d+):\D': r'\n  <b>\1:  </b>',
        r'";\s*"': f'</font><b>;</b> <font color="{sen_col}">',
        r'[;:]\s*"': fr'\n        <font color="{sen_col}">',
        r'"\s+\[': r'</font>[',
        r'\[syn:': r'\n        <i>Synonyms: ',
        r'\[ant:': r'\n        <i>Antonyms: ',
        r'}\]': r'}</i>',
        r"\{([^{]*)\}": fr'<font color="{word_col}">\1</font>',
        r'";[ \t\r\f\v]*$': r'</font>',
        r'";[ \t\r\f\v]+(.+)$': r'</font> \1',
        r'"[; \t\r\f\v]+(\(.+\))$': r'</font> \1',
        r'"\s*\-+\s*(.+)(\s*)([<]*)': r"</font> - \1\2\3",
        r';\s*$': r'',
        "`": "'",
    }
    for to_replace, replace_with in re_list.items():
        re_clean = re.compile(to_replace, re.MULTILINE)
        definition = re_clean.sub(replace_with, definition)
    return definition.strip()


@lru_cache(maxsize=None)
def run_processes(term):
    """Run the processes for obtaining defintion data."""
    strategy = "lev"
    try:
        process_def = subprocess.Popen(["dict", "-d", "wn", term], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        process_pron = subprocess.Popen(["espeak-ng", "-ven-uk-rp", "--ipa", "-q", term], stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE)
        process_close = subprocess.Popen(["dict", "-m", "-d", "wn", "-s", strategy, term], stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE)
    except OSError as ex:
        print("Didn't Work! ERROR INFO: " + str(ex))
        return None
    process_def.wait()
    output = ['', '', '']
    output[0] = process_def.stdout.read().decode()
    process_pron.wait()
    output[1] = process_pron.stdout.read().decode()
    process_close.wait()
    output[2] = process_close.stdout.read().decode()
    return output


def clean_pango(data):
    """Convert HTML subset to Pango markup. Not a real converter."""
    replace_list = {
        '<font color="': '<span foreground="',
        '</font>': '</span>',
        '<br>': '\n',
    }
    for to_replace, replace_with in replace_list.items():
        data = data.replace(to_replace, replace_with)
    return data


def generate_definition(text, wordcol, sencol, markup="html"):
    """Check if custom definition exists."""
    if os.path.exists(utils.CDEF_FOLD + '/' + text.lower()):
        return get_custom_def(text, wordcol, sencol, markup)
    return get_data(text, wordcol, sencol, markup)


def read_term(text, speed):
    """Say text loudly."""
    with open(os.devnull, 'w') as null_maker:
        subprocess.Popen(["espeak-ng", "-s", speed, "-ven-uk-rp", text], stdout=null_maker, stderr=subprocess.STDOUT)
