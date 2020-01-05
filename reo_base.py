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


def defProcessor(defi, term, senCol, wordCol, markup='qt', debug=False):
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
    if markup == "qt":
        cleanDefi = defi.strip().replace('\n', '<br>').replace('  ',
                                                               '&nbsp;&nbsp;')
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


def readTerm(text, speed):
    """Say text loudly."""
    with open(os.devnull, 'w') as NULLMAKER:
        subprocess.Popen(["espeak-ng", "-ven-uk-rp", "-s", speed, text],
                         stdout=NULLMAKER, stderr=subprocess.STDOUT)
