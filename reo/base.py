# -*- coding: utf-8 -*-
# Copyright (C) 2016-2020 Mufeed Ali
# SPDX-License-Identifier: GPL-3.0-only or GPL-3.0-or-later
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
import sys
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache

from reo import utils

_POOL = ThreadPoolExecutor()


def _threadpool(func):
    """Wraps around a function allowing it to run in a separate thread and return a future object."""
    def wrap(*args, **kwargs):
        return (_POOL).submit(func, *args, **kwargs)

    return wrap


def cleaner(search_term):
    """Clean up search terms."""
    text = search_term.strip().strip('<>"-?`![](){}/:;,*')
    cleaner_list = ['(', ')', '<', '>', '[', ']', '&', '\\']
    for item in cleaner_list:
        text = text.replace(item, '')
    return text


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
def format_close_words(clp, text, skip_clean=False):
    """Format the similar words list obtained."""
    if not skip_clean:
        # Clean up
        sub_dict = {
            r'\s+      \s+': r'  ',  # clear extra space
            f'  ["]*{text.lower()}["]*$': r'',  # remove ocurrence of same term at the end
            f'(.)  {text.lower()}  (.)': r'\1  \2',  # remove ocurrence of same term in the middle with no quotations
            f'wn: ["]*{text.lower()}["]*  (.)': r'\1',  # remove ocurrence of same term at the beginning
            f'(.)  "{text.lower()}"  (.)': r'\1  \2',  # remove ocurrence of same term in the middle with quotations
            r'\s*\n\s*': r'  ',  # clear extra whitespace for replacement with comma
            r'\s\s+': r', ',  # replace with commas for separation
            f'["]+{text.lower()}["]+': r'',  # replace single ocurrences of the same term
            'wn:[,]*': r'',  # remove 'wn:' from the start
        }
        for to_replace, replace_with in sub_dict.items():
            sub_re = re.compile(to_replace)
            clp = sub_re.sub(replace_with, clp).strip()
    # Make them all hyperlinks.
    new_list = []
    for item in clp.split(', '):
        item = item.strip('"')
        if item:
            new_list.append(f'<a href="search:{item}">{item}</a>'.strip())
    new_string = ', '.join(new_list)
    return new_string


def generate_definition(text, wordcol, sencol, cdef=True):
    """Check if custom definition exists."""
    if cdef and os.path.isfile(utils.CDEF_FOLD + '/' + text.lower()):
        return get_custom_def(text, wordcol, sencol)
    return get_data(text, wordcol, sencol)


def get_cowfortune():
    """Present cowsay version of fortune easter egg."""
    try:
        cowsay = subprocess.Popen(['cowsay', get_fortune(mono=False)], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        cowsay.wait()
        if cowsay:
            cst = cowsay.stdout.read().decode()
            return f'<tt>{html.escape(cst)}</tt>'
        return '<tt>Cowsay fail... Too bad...</tt>'
    except OSError as ex:
        fortune_out = 'Easter Egg Fail!!! Install \'fortune\' or \'fortunemod\' and also \'cowsay\'.'
        print(f'{fortune_out}\n{str(ex)}')
        return f'<tt>{fortune_out}</tt>'


def get_custom_def(text, wordcol, sencol):
    """Present custom definition when available."""
    with open(utils.CDEF_FOLD + '/' + text, 'r') as def_file:
        custom_def_dict = json.load(def_file)
    if 'linkto' in custom_def_dict:
        return get_data(custom_def_dict.get('linkto', text), wordcol, sencol)
    definition = custom_def_dict.get('definition', get_definition(text, wordcol, sencol)[0]['definition'])
    close = custom_def_dict.get('close', get_close_words(text))
    if close is None or close.strip() == '':
        final_close = ''
    else:
        final_close = f'<b>Similar Words</b>:<br>  <i><font color="{wordcol}">{close}</font></i>'
    re_list = {
        '<i>($WORDCOL)</i>': wordcol,
        '<i>($SENCOL)</i>': sencol,
        '($WORDCOL)': wordcol,
        '($SENCOL)': sencol,
        '$WORDCOL': wordcol,
        '$SENCOL': sencol,
    }
    for i, j in re_list.items():
        definition = definition.replace(i, j)
        final_close = final_close.replace(i, j)
    term = custom_def_dict.get('term', text)
    pronunciation = custom_def_dict.get('pronunciation', get_pronunciation(term)) or 'Is espeak-ng installed?'
    final_data = {
        'term': term,
        'pronunciation': pronunciation,
        'definition': definition,
        'close': final_close,
    }
    return final_data


def get_close_words(term):
    """Run the processes for obtaining definition data."""
    strategy = 'lev'
    try:
        process_close = subprocess.Popen(['dict', '-m', '-d', 'wn', '-s', strategy, term], stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE)
    except OSError as ex:
        print('Didn\'t Work! ERROR INFO: ' + str(ex))
        return None
    process_close.wait()
    output = process_close.stdout.read().decode()
    clean_output = format_close_words(output, term)
    return clean_output


def get_data(term, word_col, sen_col):
    """Obtain the data to be processed and presented."""
    definition = get_definition(term, word_col, sen_col)
    clean_def = definition[0]
    no_def = definition[1]
    pron = get_pronunciation(term)
    clean_close = get_close_words(term)
    if not clean_close or clean_close.strip() == '':
        fail_flag = True
        clean_close = ''
    else:
        fail_flag = False
    if term.lower() == 'recursion':
        clean_close = 'recursion'
    if not pron or pron == '' or pron.isspace():
        final_pron = 'Is espeak-ng installed?'
    else:
        final_pron = pron
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


def get_definition(term, word_col, sen_col):
    """Get the definition from dictd and process it."""
    try:
        process_def = subprocess.Popen(['dict', '-d', 'wn', term], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except OSError as ex:
        print('Didn\'t Work! ERROR INFO: ' + str(ex))
        return (
            {
                'term': term,
                'definition': 'Lookup failed. Are dict and dictd installed?',
            },
            True
        )
    process_def.wait()
    definition = process_def.stdout.read().decode()
    if definition is not None:
        if definition == '':
            clean_def = {
                'term': term,
                'definition': f'Couldn\'t find definition for \'{term}\'.',
            }
            return (clean_def, True)
        clean_def = process_definition(definition, term, sen_col, word_col)
        return (clean_def, False)


def get_fortune(mono=True):
    """Present fortune easter egg."""
    try:
        fortune_process = subprocess.Popen(['fortune', '-a'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        fortune_process.wait()
        fortune_out = fortune_process.stdout.read().decode()
        fortune_out = html.escape(fortune_out, False)
    except OSError as ex:
        fortune_out = 'Easter Egg Fail! Install \'fortune\' or \'fortune-mod\'.'
        utils.log_error(f'{fortune_out}\n{str(ex)}')
    if mono:
        return f'<tt>{fortune_out}</tt>'
    return fortune_out


@lru_cache(maxsize=None)
def get_pronunciation(term):
    """Get the pronunciation from espeak and process it."""
    try:
        process_pron = subprocess.Popen(['espeak-ng', '-ven-uk-rp', '--ipa', '-q', term], stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE)
    except OSError as ex:
        print('Didn\'t Work! ERROR INFO: ' + str(ex))
        return None
    process_pron.wait()
    output = process_pron.stdout.read().decode()
    clean_output = ' /{0}/'.format(output.strip().replace('\n ', ' '))
    return clean_output


def get_version_info():
    """Present clear version info."""
    print('Reo - ' + utils.VERSION)
    print('Copyright 2016-2020 Mufeed Ali')
    print()
    wn_ver = get_wn_version()
    if wn_ver == '3.1':
        print('WordNet Version 3.1 (2011) (Installed)')
    elif wn_ver == '3.0':
        print('WordNet Version 3.0 (2006) (Installed)')
    print()
    try:
        dict_process = subprocess.Popen(['dict', '-V'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        dict_out = dict_process.stdout.read().decode()
        print(dict_out.strip())
    except OSError as ex:
        print('Looks like missing dependencies. (dict)\n' + str(ex))
    print()
    try:
        espeak_process = subprocess.Popen(['espeak-ng', '--version'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        espeak_process.wait()
        espeak_out = espeak_process.stdout.read().decode()
        print(espeak_out.strip())
    except OSError as ex:
        print('You\'re missing a few dependencies. (espeak-ng)\n' + str(ex))


@_threadpool
def get_wn_file():
    """Get the WordNet wordlist according to WordNet version."""
    wn_version = get_wn_version()
    wn_file = str(lzma.open(utils.get_word_list(wn_version), 'r').read()).split('\\n')
    return (wn_version, wn_file)


@lru_cache(maxsize=None)
def get_wn_version():
    """Check version of WordNet."""
    try:
        check_process = subprocess.Popen(['dict', '-d', 'wn', 'test'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        check_out = check_process.stdout.read().decode()
    except OSError as ex:
        print('Error with dict. Error')
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
    term_in_wn = re.search('  ' + term, definition, flags=re.IGNORECASE).group(0) or term
    definition = definition.replace(term_in_wn + '\n', '')
    utils.log_info(f'Searching {term_in_wn.strip()}')
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
        r'[;:]\s*\(': r'\n        (',  # non-example after example (o.k.)
        r'\[syn:': r'\n        <i>Synonyms: ',  # synonyms header
        r'\[ant:': r'\n        <i>Antonyms: ',  # antonyms header
        r'}\]': r'}</i>',  # syn and ant end markers
        r'\{([^{]*)\([a-zA-Z]\)\}': fr'<a href="search:\1"><font color="{word_col}">\1</font></a>',  # words with (a)
        r'\{([^{]*)\}': fr'<a href="search:\1"><font color="{word_col}">\1</font></a>',  # syn and ant words
        r';\s*$': r'',  # fixes wrong line endings (eg: "change")
        '`': '\'',  # correct wrong character usage
    }
    for to_replace, replace_with in re_list.items():
        re_clean = re.compile(to_replace, re.MULTILINE)
        definition = re_clean.sub(replace_with, definition)
    return {
        'term': term_in_wn,
        'definition': '  ' + definition.strip(),
    }


def reactor(text, dark_font, wn_ver, cdef):
    """Return appropriate definitions."""
    if dark_font:
        sencol = 'cyan'  # Color of sentences in Dark mode
        wordcol = 'lightgreen'  # Color of: Similar Words,
#                                     Synonyms and Antonyms.
    else:
        sencol = 'blue'  # Color of sentences in regular
        wordcol = 'green'  # Color of: Similar Words, Synonyms, Antonyms.
    wn_list = (
        '00-database-allchars',
        '00-database-info',
        '00-database-short',
        '00-database-url'
    )
    if text in wn_list:
        return {
            'term': '<tt>Reo</tt>',
            'pronunciation': f'<tt>Powered by dictd and WordNet {wn_ver}</tt>',
            'definition': '<tt>URL: <a href="https://wordnet.princeton.edu/">WordNet</a></tt>',
            'close': ''
        }
    if text == 'fortune -a':
        return {
            'term': '<tt>Some random adage</tt>',
            'pronunciation': '<tt>Courtesy of fortune</tt>',
            'definition': get_fortune(),
            'close': ''
        }
    if text == 'cowfortune':
        return {
            'term': '<tt>Some random adage from a cow</tt>',
            'pronunciation': '<tt>Courtesy of fortune and cowsay</tt>',
            'definition': get_cowfortune(),
            'close': ''
        }
    if text.lower() == 'reo':
        return {
            'term': '<tt>Reo</tt>',
            'pronunciation': '<tt>/ɹˈiːəʊ/</tt>',
            'definition': '<tt><i>Japanese Word</i>\n'
                          '  <b>1:</b> Name of this application, chosen kind of at random.\n'
                          '  <b>2:</b> Japanese word meaning \'Wise Center\'</tt>',
            'close': ('<tt> <b>Similar Words:</b>\n' +
                      f'  <i><span foreground=\"{wordcol}\">' +
                      format_close_words(
                          'ro, re, roe, redo, reno, oreo, ceo, leo, neo, ' +
                          'rho, rio, reb, red, ref, rem, rep, res, ret, rev, rex',
                          'Reo', True
                      ) +
                      '</span></i></tt>')
        }
    if text in ('crash now', 'close now'):
        sys.exit()
        return None
    if text and not text.isspace():
        return generate_definition(text, wordcol, sencol, cdef=cdef)
    return None


def read_term(text, speed):
    """Say text loudly."""
    with open(os.devnull, 'w') as null_maker:
        subprocess.Popen(['espeak-ng', '-s', speed, '-ven-uk-rp', text], stdout=null_maker, stderr=subprocess.STDOUT)
