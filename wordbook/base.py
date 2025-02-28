# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2016-2024 Mufeed Ali <mufeed@kumo.foo>
# SPDX-License-Identifier: GPL-3.0-or-later

"""
base is a part of Wordbook and has code independent from the UI.
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
from typing import Callable

import wn
from wn import Form, Wordnet

from wordbook import utils

POOL = ThreadPoolExecutor()
WN_DB_VERSION = "oewn:2023"
wn.config.data_directory = os.path.join(utils.WN_DIR)
wn.config.allow_multithreading = True


def _threadpool(func):
    """
    Wraps around a function allowing it to run in a separate thread and
    return a future object.
    """

    def wrap(*args, **kwargs):
        return (POOL).submit(func, *args, **kwargs)

    return wrap


def clean_search_terms(search_term):
    """Clean up search terms."""
    text = search_term.strip().strip('<>"-?`![](){}/:;,*')
    cleaner_list = ["(", ")", "<", ">", "[", "]", "&", "\\", "\n"]
    for item in cleaner_list:
        text = text.replace(item, "")
    return text


def create_required_dirs():
    """Make required directories if they don't already exist."""
    os.makedirs(utils.CONFIG_DIR, exist_ok=True)  # create Wordbook folder
    os.makedirs(utils.CDEF_DIR, exist_ok=True)  # create Custom Definitions folder.


def fetch_definition(text, wordcol, sencol, wn_instance, cdef=True, accent="us"):
    """Check if custom definition exists."""
    if cdef and os.path.isfile(f"{utils.CDEF_DIR}/{text.lower()}"):
        return get_custom_def(text, wordcol, sencol, wn_instance, accent)
    return get_data(text, wordcol, sencol, wn_instance, accent)


def get_cowfortune():
    """Present cowsay version of fortune easter egg."""
    try:
        cowsaid: str = (
            subprocess.Popen(
                ["cowsay", get_fortune(mono=False)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
            .communicate()[0]
            .decode()
        )
        if cowsaid:
            return f"<tt>{html.escape(cowsaid)}</tt>"
        return "<tt>Cowsay fail… Too bad…</tt>"
    except OSError as ex:
        fortune_out = "Easter Egg Fail!!! Install 'fortune' or 'fortunemod' and also 'cowsay'."
        print(f"{fortune_out}\n{str(ex)}")
        return f"<tt>{fortune_out}</tt>"


def get_custom_def(text: str, wordcol: str, sencol: str, wn_instance, accent="us"):
    """Present custom definition when available."""
    with open(f"{utils.CDEF_DIR}/{text}", "r") as def_file:
        custom_def_dict: dict = json.load(def_file)
    if "linkto" in custom_def_dict:
        return get_data(custom_def_dict.get("linkto", text), wordcol, sencol, wn_instance, accent)
    definition = custom_def_dict.get(
        "out_string",
        get_definition(text, wordcol, sencol, wn_instance)[0]["out_string"],
    )
    definition = definition.format(WORDCOL=wordcol, SENCOL=sencol)
    term = custom_def_dict.get("term", text)
    pronunciation = custom_def_dict.get("pronunciation", get_pronunciation(term, accent)) or "Is espeak-ng installed?"
    final_data = {
        "term": term,
        "pronunciation": pronunciation,
        "out_string": definition,
    }
    return final_data


def get_data(term, word_col, sen_col, wn_instance, accent="us"):
    """Obtain the data to be processed and presented."""

    # Obtain definition from given parameters
    definition = get_definition(term, word_col, sen_col, wn_instance)
    clean_def = definition[0]

    # Get pronunciation of the term or default to the original term if no pronunciation available.
    pron = get_pronunciation(clean_def["term"] or term, accent)
    final_pron = pron if pron and not pron.isspace() else "Is espeak-ng installed?"

    # Create the dictionary to be returned.
    final_data = {
        "term": clean_def["term"],
        "pronunciation": final_pron,
        "result": clean_def["result"],
        "out_string": clean_def["out_string"],
    }

    return final_data


def get_definition(term: str, word_col: str, sen_col: str, wn_instance):
    """Get the definition from python-wn and process it."""
    first_match = None
    result_dict = None
    synsets = wn_instance.synsets(term)  # Get relevant synsets.

    if synsets:
        # Synsets have 'parts of speech'. We need their real names.
        # We also need to track their values across synsets to an extent.
        pos = None
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

        result_dict = {
            "adjective": [],
            "noun": [],
            "verb": [],
            "adverb": [],
            "phrase": [],
            "conjunction": [],
            "adposition": [],
            "other": [],
            "unknown": [],
            "word_col": word_col,
            "sen_col": sen_col,
        }
        for synset in synsets:
            # Try to organize based on parts of speech.
            pos = actual_pos[synset.pos]  # If this fails, nothing beyond it is useful.

            # We need the term as is found in the WordNet database.
            lemma_names = synset.lemmas()
            diff_match = difflib.get_close_matches(term, lemma_names)
            synset_name = diff_match[0].strip() if diff_match else lemma_names[0]

            # If suitable term isn't found, return the term entered.
            if first_match is None or first_match == "":
                first_match = synset_name

            syn = []  # Synonyms
            ant = []  # Antonyms
            for lemma in synset.lemmas():
                syn_name = lemma.replace("_", " ").strip()
                if not syn_name == first_match:
                    syn.append(syn_name)
            for sense in synset.senses():
                for ant_sense in sense.get_related("antonym"):
                    ant_name = ant_sense.word().lemma()
                    ant.append(ant_name)

            sims = []  # WordNet's "Similar to"
            for sim_synset in synset.get_related("similar"):
                sims.extend(sim_synset.lemmas())

            also_sees = []  # WorNet's "Also See"
            for also_synset in synset.get_related("also"):
                also_sees.extend(also_synset.lemmas())

            synset_dict = {
                "name": synset_name,
                "definition": synset.definition(),
                "examples": synset.examples(),
                "syn": syn,
                "ant": ant,
                "sim": sims,
                "also_sees": also_sees,
            }

            # Get the definition for each synset.
            result_dict[pos].append(synset_dict)

    if result_dict is None:
        clean_def = {
            "term": term,
            "result": None,
            "out_string": None,
        }
        return (clean_def, True)

    clean_def = {
        "term": first_match,
        "result": result_dict,
        "out_string": None,
    }
    return (clean_def, False)


def get_fortune(mono=True):
    """Present fortune easter egg."""
    try:
        fortune_output = (
            subprocess.Popen(["fortune", "-a"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            .communicate()[0]
            .decode()
        )
        if fortune_output:
            fortune_output = html.escape(fortune_output, False)
    except OSError as ex:
        fortune_output = "Easter egg fail! Install 'fortune' or 'fortune-mod'."
        utils.log_error(f"{fortune_output}\n{str(ex)}")

    if mono:
        return f"<tt>{fortune_output}</tt>"
    return fortune_output


@lru_cache(maxsize=128)
def get_pronunciation(term, accent="us"):
    """Get the pronunciation from espeak and process it."""
    pron_output = (
        subprocess.Popen(
            ["espeak-ng", "-v", f"en-{accent}", "--ipa", "-q", term],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        .communicate()[0]
        .decode()
    )
    clean_output = " /{0}/".format(pron_output.strip().replace("\n ", " "))
    return clean_output


def get_version_info(version):
    """Present clear version info."""
    print(f"Wordbook - {version}")
    print("Copyright 2016-2024 Mufeed Ali")
    print()
    try:
        espeak_out = (
            subprocess.Popen(["espeak-ng", "--version"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            .communicate()[0]
            .decode()
        )
        print(espeak_out.strip())
    except OSError as ex:
        print(f"You're missing a few dependencies. (espeak-ng)\n{str(ex)}")


@_threadpool
def get_wn_file(reloader: Callable) -> dict[str, Wordnet | list[Form]]:
    """Get the WordNet wordlist according to WordNet version."""
    utils.log_info("Initializing WordNet.")
    try:
        wn_instance: Wordnet = Wordnet(lexicon=WN_DB_VERSION)
    except (wn.Error, wn.DatabaseError):
        utils.log_info("The WordNet database is either corrupted or is of an older version.")
        return reloader()
    utils.log_info("Fetching WordNet, wordlist.")
    wn_file = [w.lemma() for w in wn_instance.words()]
    utils.log_info("WordNet is ready.")
    return {"instance": wn_instance, "list": wn_file}


def format_output(text, dark_font, wn_instance, cdef, accent="us"):
    """Return appropriate definitions."""
    if dark_font:
        sencol = "cyan"  # Color of sentences in Dark mode
        wordcol = "lightgreen"  # Color of: Similar words, Synonyms and Antonyms.
    else:
        sencol = "blue"  # Color of sentences in regular
        wordcol = "green"  # Color of: Similar words, Synonyms, Antonyms.

    if text == "fortune -a":
        return {
            "term": "<tt>Some random adage</tt>",
            "pronunciation": "<tt>Courtesy of fortune</tt>",
            "out_string": get_fortune(),
        }
    if text == "cowfortune":
        return {
            "term": "<tt>Some random adage from a cow</tt>",
            "pronunciation": "<tt>Courtesy of fortune and cowsay</tt>",
            "out_string": get_cowfortune(),
        }
    if text in ("crash now", "close now"):
        return sys.exit()
    if text and not text.isspace():
        return fetch_definition(text, wordcol, sencol, wn_instance, cdef=cdef, accent=accent)
    return None


def read_term(text, speed=120, accent="us"):
    """Say text loudly."""
    with open(os.devnull, "w") as null_maker:
        subprocess.Popen(
            ["espeak-ng", "-s", str(speed), "-v", f"en-{accent}", text],
            stdout=null_maker,
            stderr=subprocess.STDOUT,
        )


class WordnetDownloader:
    @staticmethod
    def check_status() -> bool:
        """
        Check if the Wordnet database has already been downloaded.
        """
        return os.path.isfile(os.path.join(utils.WN_DIR, "wn.db"))

    @staticmethod
    def download(progress_handler=None):
        """Download the Wordnet database."""
        if os.path.isdir(os.path.join(utils.WN_DIR, "downloads")):
            rmtree(os.path.join(utils.WN_DIR, "downloads"))
        wn.download(WN_DB_VERSION, progress_handler=progress_handler)

    @staticmethod
    def delete_db():
        """Delete the Wordnet database."""
        os.remove(os.path.join(utils.WN_DIR, "wn.db"))
