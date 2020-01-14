"""
reo_base contains the shared code between the Qt5 and Gtk3 frontends.

reo_base is a part of Reo. It contains a few functions that are reusable across
both the UIs.
"""

# The MIT License (MIT)

# Copyright (c) 2019-2020 Mufeed Ali
# This file is part of Reo

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# Author: Mufeed Ali

import re
import html
import os
import subprocess
from os.path import expanduser

reo_version = "master"
reo_fold = expanduser('~') + "/.config/reo"
# ^ This is where stuff like settings, Custom Definitions, etc will go.
cdef_fold = reo_fold + "/cdef"
# ^ The Folder within reo_fold where Custom Definitions are to be kept.
reo_config = reo_fold + "/reo.conf"


def foldGen():
    """Make required directories if they don't already exist."""
    if not os.path.exists(reo_fold):  # check for Reo folder
        os.makedirs(reo_fold)  # create Reo folder
    if not os.path.exists(cdef_fold):  # check for Custom Definitions folder.
        os.makedirs(cdef_fold)  # create Custom Definitions folder.


def defProcessor(defi, term, senCol, wordCol, markup='html', debug=False):
    """Format the definition obtained from 'dict'."""
    defi = defi.replace('1 definition found\n\nFrom WordNet (r)' +
                        ' 3.0 (2006) [wn]:\n', '')
    defi = defi.replace('1 definition found\n\nFrom WordNet (r)' +
                        ' 3.1 (2011) [wn]:\n', '')
    defi = html.escape(defi, False)
    try:
        termInWn = re.search("  " + term, defi,
                             flags=re.IGNORECASE).group(0)
    except Exception as ex:
        termInWn = ''
        print("Regex search failed" + str(ex))
    defi = defi.replace(termInWn + '\n', '')
    if debug is True:
        print("Searching " + termInWn.strip())
    relist = {r'[ \t\r\f\v]+n\s+': '<b>' + termInWn +
              '</b> ~ <i>noun</i>:\n      ',
              r'[ \t\r\f\v]+adv\s+': '<b>' + termInWn +
              '</b> ~ <i>adverb</i>:\n      ',
              r'[ \t\r\f\v]+adj\s+': '<b>' + termInWn +
              '</b> ~ <i>adjective</i>:\n      ',
              r'[ \t\r\f\v]+v\s+': '<b>' + termInWn +
              '</b> ~ <i>verb</i>:\n      ',
              r'([-]+)\s+      \s+': r'\1',
              r'\s+      \s+': r' ',
              r'"$': r'</font>',
              r'\s+(\d+):\D': r'\n  <b>\1:  </b>',
              r'";\s*"': '</font><b>;</b> <font color="' + senCol + '">',
              r'[;:]\s*"': r'\n        <font color="' + senCol + '">',
              r'"\s+\[': r'</font>[',
              r'\[syn:': r'\n        <i>Synonyms: ',
              r'\[ant:': r'\n        <i>Antonyms: ',
              r'}\]': r'}</i>',
              r"\{([^{]*)\}": r'<font color="' + wordCol + r'">\1</font>',
              r'";[ \t\r\f\v]*$': r'</font>',
              r'";[ \t\r\f\v]+(.+)$': r'</font> \1',
              r'"[; \t\r\f\v]+(\(.+\))$': r'</font> \1',
              r'"\s*\-+\s*(.+)\s*([<]*)': r"</font> - \1; \2",
              r';\s*$': r''}
    for x, y in relist.items():
        reclean = re.compile(x, re.MULTILINE)
        defi = reclean.sub(y, defi)
    if markup == "pango":
        defi = defi.replace('<font color="', '<span foreground="')
        defi = defi.replace('</font>', '</span>')
    if not defi.find("`") == -1:
        defi = defi.replace("`", "'")
    if not defi.find("thunder started the sleeping") == -1:
        defi = defi.replace("thunder started the sleeping",
                            "thunder started, the sleeping")
    if markup == "html":
        cleanDefi = defi.strip().replace('\n', '<br>')
    else:
        cleanDefi = defi.strip()
    return cleanDefi


def clsfmt(clp, text):
    """Format the similar words list obtained."""
    subDict = {r'\s+      \s+': r'  ',
               '  ["]*' + text.lower() + '["]*$': r'',
               "(.)  " + text.lower() + "  (.)": r"\1  \2",
               'wn: ["]*' + text.lower() + '["]*  (.)': r"\1",
               '(.)  "' + text.lower() + '"  (.)': r"\1  \2",
               r'\s*\n\s*': r'  ',
               r"\s\s+": r", ",
               '["]+' + text.lower() + '["]+': r"",
               'wn:[,]*': r''}
    for x, y in subDict.items():
        subr = re.compile(x)
        clp = subr.sub(y, clp).strip()
    clp = clp.rstrip()
    return clp


def fortune():
    """Present fortune easter egg."""
    try:
        fortune = subprocess.Popen(["fortune", "-a"], stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT)
        fortune.wait()
        ft = fortune.stdout.read().decode()
        ft = html.escape(ft, False)
        return "<tt>" + ft + "</tt>"
    except Exception as ex:
        ft = "Easter Egg Fail!!! Install 'fortune' or 'fortunemod'."
        print(ft + "\n" + str(ex))
        return "<tt>" + ft + "</tt>"


def cowfortune():
    """Present cowsay version of fortune easter egg."""
    try:
        cowsay = subprocess.Popen(["cowsay", fortune()],
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT)
        cowsay.wait()
        if cowsay:
            cst = cowsay.stdout.read().decode()
        return "<tt>" + cst + "</tt>"
    except Exception as ex:
        ft = ("Easter Egg Fail!!! Install 'fortune' or 'fortunemod'" +
              " and also 'cowsay'.")
        print(ft + "\n" + str(ex))
        return "<tt>" + ft + "</tt>"


def dataObtain(term, wordCol, senCol, markup='html', debug=False):
    """
    Obtain the data to be processed and presented.

    Too complex according to McCabe complexity check. Needs work.
    """
    strat = "lev"
    try:
        procDefi = subprocess.Popen(["dict", "-d", "wn", term],
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
        procPron = subprocess.Popen(["espeak-ng", "-ven-uk-rp",
                                     "--ipa", "-q", term],
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
        procClos = subprocess.Popen(["dict", "-m", "-d", "wn",
                                     "-s", strat, term],
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
    except Exception as ex:
        print("Didnt Work! ERROR INFO: " + str(ex))
    procDefi.wait()
    defi = procDefi.stdout.read().decode()
    if not defi == '':
        cleanDefi = defProcessor(defi, term, senCol, wordCol, markup, debug)
        NoDef = 0
    else:
        cleanDefi = "Coundn't find definition for '" + term + "'."
        NoDef = 1
    procPron.wait()
    pron = procPron.stdout.read().decode()
    cleanPron = " /" + pron.strip().replace('\n ', ' ') + "/"
    procClos.wait()
    clos = procClos.stdout.read().decode()
    cleanClos = clsfmt(clos, term)
    fail = False
    if term.lower() == 'recursion':
        clos = 'recursion'
    if cleanClos.strip() == '':
        fail = True
    if procPron and not NoDef == 1:
        finalPron = "<b>Pronunciation</b>: <b>" + cleanPron + '</b>'
    elif procPron and NoDef == 1:
        finalPron = ("<b>Probable Pronunciation</b>: <b>" + cleanPron +
                     '</b>')
    if not fail:
        if NoDef == 1:
            finalClos = ('<b>Did you mean</b>:<br><i><font color="' +
                         wordCol + '">  ' + cleanClos + '</font></i>')
        else:
            finalClos = ('<b>Similar Words</b>:<br>' +
                         '<i><font color="' + wordCol + '">  ' +
                         cleanClos + '</font></i>')
    else:
        finalClos = ''
    if markup == "pango":
        data = finalPron.strip() + '\n' + cleanDefi + '\n' + finalClos.strip()
        data = data.replace('<font color="', '<span foreground="')
        data = data.replace('</font>', '</span>')
        data = data.replace('<br>', '\n')
        finalData = data.replace('&', '&amp;')
    else:
        data = ("<p>" + finalPron + '</p><p>' + cleanDefi + '</p><p>' +
                finalClos.strip() + "</p>")
        finalData = data.replace('&', '&amp;').replace('  ', '&nbsp;&nbsp;')
    return finalData


def wnvercheck():
    """Check version of WordNet."""
    try:
        checkProc = subprocess.Popen(["dict", "-d", "wn", "test"],
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT)
        checkOut = checkProc.stdout.read().decode()
    except Exception as ex:
        print("Error with dict. Error")
        print(ex)
    if not checkOut.find('1 definition found\n\nFrom WordNet (r)' +
                         ' 3.1 (2011) [wn]:\n') == -1:
        return '3.1'
    elif not checkOut.find('1 definition found\n\nFrom WordNet (r)' +
                           ' 3.0 (2006) [wn]:\n') == -1:
        return '3.0'


def verinfo():
    """Present clear version info."""
    print('Reo - ' + reo_version)
    print('Copyright 2016-2020 Mufeed Ali')
    print()
    wnver = wnvercheck()
    if wnver == '3.1':
        print("WordNet Version 3.1 (2011) (Installed)")
    elif wnver == '3.0':
        print("WordNet Version 3.0 (2006) (Installed)")
    print()
    try:
        dictProc = subprocess.Popen(["dict", "-V"],
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT)
        dictOut = dictProc.stdout.read().decode()
        print(dictOut.strip())
    except Exception as ex:
        print("Looks like missing components. (dict)\n" + str(ex))
    print()
    try:
        esProc = subprocess.Popen(["espeak-ng", "--version"],
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT)
        esOut = esProc.stdout.read().decode()
        print(esOut.strip())
    except Exception as ex:
        print("You're missing a few components. (espeak-ng)\n" + str(ex))


def htmltopango(data):
    """Convert HTML data to Pango markup data."""
    data = data.replace('<font color="', '<span foreground="')
    data = data.replace('</font>', '</span>')
    data = data.replace('<br>', '\n')
    return data


def readTerm(text, speed):
    """Say text loudly."""
    with open(os.devnull, 'w') as NULLMAKER:
        subprocess.Popen(["espeak-ng", "-ven-uk-rp", "-s", speed, text],
                         stdout=NULLMAKER, stderr=subprocess.STDOUT)
