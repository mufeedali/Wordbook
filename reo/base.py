# -*- coding: utf-8 -*-
# Copyright (C) 2016-2020 Mufeed Ali
# SPDX-License-Identifier: MIT
# Author: Mufeed Ali <fushinari@protonmail.com>

"""
base contains the shared code between the Qt5 and GTK 3 frontends.

base is a part of Reo. It contains a few functions that are reusable across
both the UIs.
"""

import html
import json
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
    """Convert Pango Markup subset used in Reo to HTML and cleanup. Not a real converter."""
    replace_list = {
        '<span foreground="': '<font color="',
        '</span>': '</font>',
        '\n': '<br>',
        '  ': '&nbsp;&nbsp;',
    }
    for to_replace, replace_with in replace_list.items():
        data = data.replace(to_replace, replace_with)
    return data


def clean_pango(data):
    """Convert HTML subset used in Reo to Pango markup. Not a real converter."""
    replace_list = {
        '<font color="': '<span foreground="',
        '</font>': '</span>',
        '<br>': '\n',
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
    # Clean up
    sub_dict = {
        r'\s+      \s+': r'  ',  # clear extra space
        f'  ["]*{text.lower()}["]*$': r'',  # remove ocurrence of same term at the end
        f"(.)  {text.lower()}  (.)": r"\1  \2",  # remove ocurrence of same term in the middle with no quotations
        f'wn: ["]*{text.lower()}["]*  (.)': r"\1",  # remove ocurrence of same term at the beginning
        f'(.)  "{text.lower()}"  (.)': r"\1  \2",  # remove ocurrence of same term in the middle with quotations
        r'\s*\n\s*': r'  ',  # clear extra whitespace for replacement with comma
        r"\s\s+": r", ",  # replace with commas for separation
        f'["]+{text.lower()}["]+': r"",  # replace single ocurrences of the same term
        'wn:[,]*': r'',  # remove 'wn:' from the start
    }
    for to_replace, replace_with in sub_dict.items():
        sub_re = re.compile(to_replace)
        clp = sub_re.sub(replace_with, clp).strip()
    # Make them all hyperlinks.
    new_list = []
    for item in clp.split(', '):
        item = item.strip("\"")
        if item:
            new_list.append(f'<a href="search:{item}">{item}</a>'.strip())
    return new_list


def generate_definition(text, wordcol, sencol, cdef=True):
    """Check if custom definition exists."""
    if cdef and os.path.exists(utils.CDEF_FOLD + '/' + text.lower()):
        return get_custom_def(text, wordcol, sencol)
    return get_data(text, wordcol, sencol)


def get_cowfortune():
    """Present cowsay version of fortune easter egg."""
    try:
        cowsay = subprocess.Popen(["cowsay", get_fortune(mono=False)], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        cowsay.wait()
        if cowsay:
            cst = cowsay.stdout.read().decode()
            return f"<tt>{html.escape(cst)}</tt>"
        return "<tt>Cowsay fail... Too bad...</tt>"
    except OSError as ex:
        fortune_out = "Easter Egg Fail!!! Install 'fortune' or 'fortunemod' and also 'cowsay'."
        print(f"{fortune_out}\n{str(ex)}")
        return f"<tt>{fortune_out}</tt>"


def get_custom_def(text, wordcol, sencol):
    """Present custom definition when available."""
    with open(utils.CDEF_FOLD + '/' + text, 'r') as def_file:
        custom_def_dict = json.load(def_file)
    definition = custom_def_dict['definition']
    close = custom_def_dict['close']
    re_list = {
        "<i>($WORDCOL)</i>": wordcol,
        "<i>($SENCOL)</i>": sencol,
        "($WORDCOL)": wordcol,
        "($SENCOL)": sencol,
        "$WORDCOL": wordcol,
        "$SENCOL": sencol,
    }
    for i, j in re_list.items():
        definition = definition.replace(i, j)
        close = close.replace(i, j)
    final_data = {
        'term': custom_def_dict['term'],
        'pronunciation': custom_def_dict['pronunciation'],
        'definition': definition,
        'close': close,
    }
    return final_data


def get_data(term, word_col, sen_col):
    """Obtain the data to be processed and presented."""
    output = run_processes(term)
    if not output:
        return "Lookup failed. Check logs."
    definition = output[0]
    if not definition == '':
        clean_def = process_definition(definition, term, sen_col, word_col)
        no_def = 0
    else:
        clean_def = {
            "term": term,
            "definition": f"Couldn't find definition for '{term}'.",
        }
        no_def = 1
    pron = output[1]
    clean_pron = " /{0}/".format(pron.strip().replace('\n ', ' '))
    close = output[2]
    clean_close = ", ".join(format_close_words(close, term))
    fail_flag = False
    if term.lower() == 'recursion':
        clean_close = 'recursion'
    if clean_close.strip() == '':
        fail_flag = True
    if clean_pron == '' or clean_pron.isspace():
        final_pron = "Obtaining pronunciation failed."
    else:
        final_pron = clean_pron
    if not fail_flag:
        if no_def == 1:
            final_close = f'<b>Did you mean</b>:<br>  <i><font color="{word_col}">{clean_close}</font></i>'
        else:
            final_close = f'<b>Similar Words</b>:<br>  <i><font color="{word_col}">{clean_close}</font></i>'
    else:
        final_close = ''
    final_data = {
        'term': clean_def['term'],
        'pronunciation': final_pron,
        'definition': clean_def['definition'],
        'close': final_close,
    }
    return final_data


def get_fortune(mono=True):
    """Present fortune easter egg."""
    try:
        fortune_process = subprocess.Popen(["fortune", "-a"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        fortune_process.wait()
        fortune_out = fortune_process.stdout.read().decode()
        fortune_out = html.escape(fortune_out, False)
    except OSError as ex:
        fortune_out = "Easter Egg Fail!!! Install 'fortune' or 'fortunemod'."
        utils.log_error(f"{fortune_out}\n{str(ex)}")
    if mono:
        return f"<tt>{fortune_out}</tt>"
    return fortune_out


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


def process_definition(definition, term, sen_col, word_col):
    """Format the definition obtained from 'dict'."""
    definition = definition.replace('1 definition found\n\nFrom WordNet (r) 3.0 (2006) [wn]:\n', '')
    definition = definition.replace('1 definition found\n\nFrom WordNet (r) 3.1 (2011) [wn]:\n', '')
    definition = html.escape(definition, False)
    term_in_wn = re.search("  " + term, definition, flags=re.IGNORECASE).group(0) or term
    definition = definition.replace(term_in_wn + '\n', '')
    utils.log_info(f"Searching {term_in_wn.strip()}")
    re_list = {
        r'[ \t\r\f\v]+n\s+': '  <i>noun</i>\n      ',  # definition header of noun
        r'[ \t\r\f\v]+adv\s+': '  <i>adverb</i>\n      ',  # definition header of adverb
        r'[ \t\r\f\v]+adj\s+': '  <i>adjective</i>\n      ',  # definition header of adjective
        r'[ \t\r\f\v]+v\s+': '  <i>verb</i>\n      ',  # definition header of verb
        r'\s+(\d+):\D': r'\n  <b>\1:  </b>',  # numbering
        r'([-]+)\s+      \s+': r'\1',  # clear whitespaces after hyphen
        r'\s+      \s+': r' ',  # clear whitespaces (usually the ones after a linebreak)
        r'" "': '"; "',  # correction for some weird cases where sentences are only separated by a single space
        r'[;:]\s*"([^;:]*)"\s*-': fr'\n        <font color="{sen_col}">\1</font> - ',  # sentences that are quotes
        r'[;:]\s*"([^;:]*)"\s*\[': fr'\n        <font color="{sen_col}">\1</font>[',  # sentence followed by syn or ant
        r'[;:]\s*"([^;:]*)"\s*\;': fr';\n        <font color="{sen_col}">\1</font>;',  # sentence followed by another
        r'[;:]*\s*"([^;:]*)"\s*\;': fr'\n        <font color="{sen_col}">\1</font>;',  # clean up leftovers from last
        r'[;:]\s*"([^;:]*)"\s*$': fr'\n        <font color="{sen_col}">\1</font>',  # sentences at EOL
        r'[;:]\s*"(.*)"\s*-': fr'\n        <font color="{sen_col}">\1</font> - ',  # leftover quotes
        r'\[syn:': r'\n        <i>Synonyms: ',  # synonyms header
        r'\[ant:': r'\n        <i>Antonyms: ',  # antonyms header
        r'}\]': r'}</i>',  # syn and ant end markers
        r"\{([^{]*)\([a-zA-Z]\)\}": fr'<a href="search:\1"><font color="{word_col}">\1</font></a>',  # words with (a)
        r"\{([^{]*)\}": fr'<a href="search:\1"><font color="{word_col}">\1</font></a>',  # syn and ant words
        r';\s*$': r'',  # fixes wrong line endings (eg: "change")
        "`": "'",  # correct wrong character usage
    }
    for to_replace, replace_with in re_list.items():
        re_clean = re.compile(to_replace, re.MULTILINE)
        definition = re_clean.sub(replace_with, definition)
    return {
        'term': term_in_wn,
        'definition': "  " + definition.strip(),
    }


def read_term(text, speed):
    """Say text loudly."""
    with open(os.devnull, 'w') as null_maker:
        subprocess.Popen(["espeak-ng", "-s", speed, "-ven-uk-rp", text], stdout=null_maker, stderr=subprocess.STDOUT)


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
