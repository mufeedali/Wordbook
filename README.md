<img height="128" src="data/icons/com.github.fushinari.Wordbook.svg" align="left"/>

# Wordbook

A dictionary application for GNOME.

Light Mode                                 |  Dark Mode
:-----------------------------------------:|:--------------------------------------------:
![Welcome screen](images/ss.png?raw=true)  |  ![Welcome screen](images/ss1.png?raw=true)
![Searching](images/ss2.png?raw=true)      |  ![Searching](images/ss3.png?raw=true)

**Wordbook** is a dictionary application using the [Open English WordNet](https://github.com/globalwordnet/english-wordnet) database for definitions and the reliable eSpeak for pronunciations (both audio and phoneme).

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
make develop
make run
```
