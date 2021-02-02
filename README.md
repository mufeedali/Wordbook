<img height="128" src="data/icons/com.github.fushinari.Wordbook.svg" align="left"/>

# Wordbook

A dictionary application for GNOME.

[![Language grade: Python](https://img.shields.io/lgtm/grade/python/g/fushinari/wordbook.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/fushinari/wordbook/context:python)

**Wordbook** is a dictionary application using the [Open English WordNet](https://github.com/globalwordnet/english-wordnet) database for definitions and the reliable eSpeak for pronunciations (both audio and phoneme).

Light Mode                                 |  Dark Mode
:-----------------------------------------:|:--------------------------------------------:
![Welcome screen](images/ss.png?raw=true)  |  ![Welcome screen](images/ss1.png?raw=true)
![Searching](images/ss2.png?raw=true)      |  ![Searching](images/ss3.png?raw=true)

## Requirements

* GTK 3.20+ [Arch: `gtk3`]
* libhandy 1.0.0+ (libhandy1) [Arch: `libhandy`]
* Python 3 [Arch: `python`]
* Standalone WordNet Python module [Arch AUR: `python-wn`]
* Python GObject [Arch: `python-gobject`]
* eSpeak-ng (For pronunciations and audio) [Arch: `espeak-ng`]

## Features

* Neat output with proper coloring and formatting
* Random Word
* Live Search
* Double click to search
* Custom Definitions feature using Pango Markup or an HTML subset for formatting
* Support for GNOME Dark Mode and launching app in dark mode.

## Installation

To install, first make sure of the dependencies as listed above.

```bash
make setup
make install
```

For a local build with debugging enabled:

```bash
make setup
make local
make run
```

## Future

For me, this is more of an experiment than anything else. I try a lot of things, a lot of things work, a lot of things don't and I find it fun to play around with this. I also try code that I don't really understand in other projects (not risky stuff ofc), try to follow code standards and slowly try to get better at writing good code. I'm still bad at it though. Basically, a lot of this is experimentation and I don't plan to stop anytime soon, but somehow or the other, the project is generally stable and works for my daily use and I look up words a lot.
