# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2016-2020 Mufeed Ali <fushinari@protonmail.com>
# SPDX-License-Identifier: GPL-3.0-or-later

"""
base contains the shared code between the GTK+ 3 UI and other possible frontends.

base is a part of Wordbook. It contains a few functions that are reusable across
both the UIs.
"""

import difflib
import html
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from shutil import rmtree

import wn
from wn import Wordnet

from wordbook import utils

_POOL = ThreadPoolExecutor()
wn.config.data_directory = os.path.join(utils.WN_DIR)


def _threadpool(func):
    """
    Wraps around a function allowing it to run in a separate thread and
    return a future object.
    """

    def wrap(*args, **kwargs):
        return (_POOL).submit(func, *args, **kwargs)

    return wrap


def cleaner(search_term):
    """Clean up search terms."""
    text = search_term.strip().strip('<>"-?`![](){}/:;,*')
    cleaner_list = ["(", ")", "<", ">", "[", "]", "&", "\\", "\n"]
    for item in cleaner_list:
        text = text.replace(item, "")
    return text


def clean_html(data):
    """
    Convert Pango Markup subset used in Wordbook to HTML and cleanup.
    Not a real converter.
    """
    replace_list = {
        '<span foreground="': '<font color="',
        "</span>": "</font>",
        "\n": "<br>",
        "  ": "&nbsp;&nbsp;",
    }
    for to_replace, replace_with in replace_list.items():
        data = data.replace(to_replace, replace_with)
    return data


def clean_pango(data):
    """Convert HTML subset used in Wordbook to Pango markup. Not a real converter."""
    replace_list = {
        '<font color="': '<span foreground="',
        "</font>": "</span>",
        "<br>": "\n",
    }
    for to_replace, replace_with in replace_list.items():
        data = data.replace(to_replace, replace_with)
    return data


def fold_gen():
    """Make required directories if they don't already exist."""
    if not os.path.exists(utils.CONFIG_DIR):  # check for Wordbook folder
        os.makedirs(utils.CONFIG_DIR)  # create Wordbook folder
    if not os.path.exists(utils.CDEF_DIR):  # check Custom Definitions folder.
        os.makedirs(utils.CDEF_DIR)  # create Custom Definitions folder.


def generate_definition(text, wordcol, sencol, wn_instance, cdef=True, accent="us"):
    """Check if custom definition exists."""
    if cdef and os.path.isfile(utils.CDEF_DIR + "/" + text.lower()):
        return get_custom_def(text, wordcol, sencol, wn_instance, accent)
    return get_data(text, wordcol, sencol, wn_instance, accent)


def get_cowfortune():
    """Present cowsay version of fortune easter egg."""
    try:
        cowsay = subprocess.Popen(
            ["cowsay", get_fortune(mono=False)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        cowsay.wait()
        if cowsay:
            cst = cowsay.stdout.read().decode()
            return f"<tt>{html.escape(cst)}</tt>"
        return "<tt>Cowsay fail... Too bad...</tt>"
    except OSError as ex:
        fortune_out = (
            "Easter Egg Fail!!! Install 'fortune' or 'fortunemod' and also 'cowsay'."
        )
        print(f"{fortune_out}\n{str(ex)}")
        return f"<tt>{fortune_out}</tt>"


def get_custom_def(text, wordcol, sencol, wn_instance, accent="us"):
    """Present custom definition when available."""
    with open(utils.CDEF_DIR + "/" + text, "r") as def_file:
        custom_def_dict = json.load(def_file)
    if "linkto" in custom_def_dict:
        return get_data(
            custom_def_dict.get("linkto", text), wordcol, sencol, wn_instance, accent
        )
    definition = custom_def_dict.get(
        "definition",
        get_definition(text, wordcol, sencol, wn_instance)[0]["definition"],
    )
    re_list = {
        "<i>($WORDCOL)</i>": wordcol,
        "<i>($SENCOL)</i>": sencol,
        "($WORDCOL)": wordcol,
        "($SENCOL)": sencol,
        "$WORDCOL": wordcol,
        "$SENCOL": sencol,
    }
    if definition is not None:
        for i, j in re_list.items():
            definition = definition.replace(i, j)
    term = custom_def_dict.get("term", text)
    pronunciation = (
        custom_def_dict.get("pronunciation", get_pronunciation(term, accent))
        or "Is espeak-ng installed?"
    )
    final_data = {
        "term": term,
        "pronunciation": pronunciation,
        "definition": definition,
    }
    return final_data


def get_data(term, word_col, sen_col, wn_instance, accent="us"):
    """Obtain the data to be processed and presented."""
    definition = get_definition(term, word_col, sen_col, wn_instance)
    clean_def = definition[0]
    pron = get_pronunciation(clean_def["term"] or term, accent)
    if not pron or pron == "" or pron.isspace():
        final_pron = "Is espeak-ng installed?"
    else:
        final_pron = pron
    final_data = {
        "term": clean_def["term"],
        "pronunciation": final_pron,
        "definition": clean_def["definition"],
    }
    return final_data


def get_definition(term, word_col, sen_col, wn_instance):
    """Get the definition from python-wn and process it."""
    synsets = wn_instance.synsets(term)  # Get relevant synsets.

    # Synsets have 'parts of speech' symbolized by letters. We need their actual names.
    # We also need to track their values across synsets to an extent.
    pos = None
    orig_synset = None
    actual_pos = {
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

    i = 0  # Initiate a counter.
    def_string = ""  # Initiate a string for the definition to go into.
    first_match = None
    for synset in synsets:
        # Try to organize based on parts of speech.
        orig_pos = pos
        pos = actual_pos[synset.pos]  # If this fails, nothing beyond it is useful.

        # We need the term as is found in the WordNet database.
        lemma_names = synset.lemmas()
        diff_match = difflib.get_close_matches(term, lemma_names)
        synset_name = diff_match[0].strip() if diff_match else lemma_names[0]

        # If suitable term isn't found, return the term entered.
        if first_match is None or first_match == "":
            first_match = synset_name

        # Identify and set the number of definitions for the same part of speech.
        if orig_pos is None:
            def_string += f"{synset_name} ~ <b>{pos}</b>\n"
            orig_synset = synset_name
            i += 1
        elif orig_pos == pos:
            i += 1
        else:
            def_string += f"{synset_name} ~ <b>{pos}</b>\n"
            orig_synset = synset_name
            i = 1

        # Get the definition for each synset.
        def_string += f"  <b>{i}</b>: {synset.definition()}\n"

        # Get examples if available.
        if synset.examples():
            for example in synset.examples():
                def_string += f'        <font color="{sen_col}">{example}</font>\n'

        syn = []  # Synonyms
        ant = []  # Antonyms
        for lemma in synset.lemmas():
            syn_name = lemma.replace("_", " ").strip()
            if not syn_name == orig_synset:
                syn.append(
                    f'<font color="{word_col}"><a href="search:{syn_name}">{syn_name}</a></font>'.strip()
                )
        for ant_synset in synset.get_related("antonym"):
            ant_names = ant_synset.lemmas()
            for ant_name in ant_names:
                ant.append(
                    f'<font color="{word_col}"><a href="search:{ant_name}">{ant_name}</a></font>'.strip()
                )
        if syn:
            syn = ", ".join(syn)
            def_string += f"        Synonyms: <i>{syn}</i>\n"
        if ant:
            ant = ", ".join(ant)
            def_string += f"        Antonyms: <i>{ant}</i>\n"

        sims = []  # WordNet's "Similar to"
        for sim_synset in synset.get_related("similar"):
            sim_names = sim_synset.lemmas()
            for sim_name in sim_names:
                sims.append(
                    f'<font color="{word_col}"><a href="search:{sim_name}">{sim_name}</a></font>'.strip()
                )
        if sims:
            sims = ", ".join(sims)
            def_string += f"        Similar to: <i>{sims}</i>\n"

        also_sees = []  # WorNet's "Also See"
        for also_synset in synset.get_related("also"):
            see_names = also_synset.lemmas()
            for see_name in see_names:
                also_sees.append(
                    f'<font color="{word_col}"><a href="search:{see_name}">{see_name}</a></font>'.strip()
                )
        if also_sees:
            also_sees = ", ".join(also_sees)
            def_string += f"        Also see: <i>{also_sees}</i>\n"

    if def_string == "":
        clean_def = {
            "term": term,
            "definition": None,
        }
        return (clean_def, True)
    clean_def = {
        "term": first_match,
        "definition": def_string.strip(),
    }
    return (clean_def, False)


def get_fortune(mono=True):
    """Present fortune easter egg."""
    try:
        fortune_process = subprocess.Popen(
            ["fortune", "-a"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT
        )
        fortune_process.wait()
        fortune_out = fortune_process.stdout.read().decode()
        fortune_out = html.escape(fortune_out, False)
    except OSError as ex:
        fortune_out = "Easter Egg Fail! Install 'fortune' or 'fortune-mod'."
        utils.log_error(f"{fortune_out}\n{str(ex)}")
    if mono:
        return f"<tt>{fortune_out}</tt>"
    return fortune_out


@lru_cache(maxsize=None)
def get_pronunciation(term, accent="us"):
    """Get the pronunciation from espeak and process it."""
    try:
        process_pron = subprocess.Popen(
            ["espeak-ng", "-v", f"en-{accent}", "--ipa", "-q", term],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except OSError as ex:
        utils.log_warning("Didn't Work! ERROR INFO: " + str(ex))
        return None
    process_pron.wait()
    output = process_pron.stdout.read().decode()
    clean_output = " /{0}/".format(output.strip().replace("\n ", " "))
    return clean_output


def get_version_info():
    """Present clear version info."""
    print("Wordbook - " + utils.VERSION)
    print("Copyright 2016-2020 Mufeed Ali")
    print()
    try:
        espeak_process = subprocess.Popen(
            ["espeak-ng", "--version"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT
        )
        espeak_process.wait()
        espeak_out = espeak_process.stdout.read().decode()
        print(espeak_out.strip())
    except OSError as ex:
        print("You're missing a few dependencies. (espeak-ng)\n" + str(ex))


@_threadpool
def get_wn_file():
    """Get the WordNet wordlist according to WordNet version."""
    utils.log_info("Initalizing WordNet.")
    wn_instance = Wordnet(lexicon="ewn")
    utils.log_info("Fetching WordNet, wordlist.")
    wn_file = [w.lemma() for w in wn_instance.words()]
    utils.log_info("WordNet is ready.")
    return {"instance": wn_instance, "list": wn_file}


def reactor(text, dark_font, wn_instance, cdef, accent="us"):
    """Return appropriate definitions."""
    if dark_font:
        sencol = "cyan"  # Color of sentences in Dark mode
        wordcol = "lightgreen"  # Color of: Similar words,
    #                                     Synonyms and Antonyms.
    else:
        sencol = "blue"  # Color of sentences in regular
        wordcol = "green"  # Color of: Similar words, Synonyms, Antonyms.
    wn_list = (
        "00-database-allchars",
        "00-database-info",
        "00-database-short",
        "00-database-url",
    )
    if text in wn_list:
        return {
            "term": "<tt>Wordbook</tt>",
            "pronunciation": "<tt>Powered by WordNet and espeak-ng.</tt>",
            "definition": '<tt>URL: <a href="https://wordnet.princeton.edu/">WordNet</a></tt>',
        }
    if text == "fortune -a":
        return {
            "term": "<tt>Some random adage</tt>",
            "pronunciation": "<tt>Courtesy of fortune</tt>",
            "definition": get_fortune(),
        }
    if text == "cowfortune":
        return {
            "term": "<tt>Some random adage from a cow</tt>",
            "pronunciation": "<tt>Courtesy of fortune and cowsay</tt>",
            "definition": get_cowfortune(),
        }
    if text in ("crash now", "close now"):
        return sys.exit()
    if text and not text.isspace():
        return generate_definition(
            text, wordcol, sencol, wn_instance, cdef=cdef, accent=accent
        )
    return None


def read_term(text, speed=120, accent="us"):
    """Say text loudly."""
    with open(os.devnull, "w") as null_maker:
        subprocess.Popen(
            ["espeak-ng", "-s", speed, "-v", f"en-{accent}", text],
            stdout=null_maker,
            stderr=subprocess.STDOUT,
        )


class WordnetDownloader:
    @staticmethod
    def check_status():
        """
        Check if the Wordnet database has already been downloaded.
        """
        return os.path.isfile(os.path.join(utils.WN_DIR, "wn.db"))

    @staticmethod
    def download(progress_handler=None):
        if os.path.isdir(os.path.join(utils.WN_DIR, "downloads")):
            rmtree(os.path.join(utils.WN_DIR, "downloads"))
        wn.download("ewn", progress_handler=progress_handler)
