# Wordbook ~ A Simple Dictionary

[![Language grade: Python](https://img.shields.io/lgtm/grade/python/g/fushinari/wordbook.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/fushinari/wordbook/context:python)

**Wordbook** is a dictionary application using the WordNet 3.1 (or 3.0) database for definitions and the reliable eSpeak for pronunciations (both audio and phoneme).

Light Mode                                 |  Dark Mode
:-----------------------------------------:|:--------------------------------------------:
![Welcome screen](images/ss.png?raw=true)  |  ![Welcome screen](images/ss1.png?raw=true)
![Searching](images/ss2.png?raw=true)      |  ![Searching](images/ss3.png?raw=true)

## Requirements

* GTK 3.20+ [Arch: `gtk3`] or Qt 6.0+ [Arch: `qt6-base`]
* libhandy 0.84.0+ (libhandy1) [Arch AUR: `libhandy1`] (only needed for the GTK GUI)
* Python 3 [Arch: `python`]
* Standalone WordNet Python module [Arch AUR: `python-wn`]
* Python GObject [Arch: `python-gobject`] or PySide6 [Arch: `python-pyside6`]
* eSpeak-ng (For pronunciations and audio) [Arch: `espeak-ng`]

Run `wordbook` for the GTK GUI or `wordbook-qt` for the Qt GUI.

## Features

* Neat output with proper coloring and formatting
* Random Word
* Live Search
* Double click to search
* Custom Definitions feature using Pango Markup or an HTML subset for formatting
* Lightweight. 1 mb only and further reducible (It does nothing on its own, so yeah)
* Support for GNOME Dark Mode and launching app in dark mode.

## Installation

To install, first make sure of the dependencies as listed above.

```bash
python setup.py install
```

For development (i.e. to see changes live as you make them):

```bash
python setup.py develop
```

## Notes

### Qt5 Interface

* Most settings are shared between the two GUIs. Only GUI-specific settings are separated (dark mode for example).
* Should work on Windows now if espeak installed in PATH but not officially supported.
* The GTK interface is still the recommended interface and will usually be the first to receive new features.

### Why libhandy?

Because I like the new rounded corners, lol. Also, pretty settings window.

## Future

For me, this is more of an experiment than anything else. I try a lot of things, a lot of things work, a lot of things don't and I find it fun to play around with this. I also try code that I don't really understand in other projects (not risky stuff ofc), try to follow code standards and slowly try to get better at writing good code. I'm still bad at it though. Basically, a lot of this is experimentation and I don't plan to stop anytime soon, but somehow or the other, the project is generally stable and works for my daily use and I look up words a lot.
