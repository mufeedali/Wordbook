<h1 align="center">
<img height="128" src="data/icons/com.github.fushinari.Wordbook.svg" alt="Wordbook"/><br>
Wordbook
</h1>

<p align="center">Lookup definitions of any term</p>

<p align="center">
<img src="images/ss2.png?raw=true" alt="Searching (Light mode)" width="290">
</p>

<p align="center">
<b>Wordbook</b> is a dictionary application built for GNOME using the <a href="https://github.com/globalwordnet/english-wordnet">Open English WordNet</a> database for definitions and the reliable eSpeak for pronunciations (both audio and phoneme).
</p>

## Features

* Fully offline after initial data download
* Random Word
* Live Search
* Double click to search
* Custom Definitions feature using Pango Markup or an HTML subset for formatting
* Support for GNOME Dark Mode and launching app in dark mode.

## Screenshots

<img src="images/ss.png?raw=true" alt="Welcome screen (Light mode)" width="290"> <img src="images/ss2.png?raw=true" alt="Searching (Light mode)" width="290">

<img src="images/ss1.png?raw=true" alt="Welcome screen (Dark mode)" width="290"> <img src="images/ss3.png?raw=true" alt="Searching (Dark mode)" width="290">

## Requirements

* GTK 3.20+ [Arch: `gtk3`]
* libhandy 1.0.0+ (libhandy1) [Arch: `libhandy`]
* Python 3 [Arch: `python`]
* Standalone WordNet Python module [Arch AUR: `python-wn`]
* Python GObject [Arch: `python-gobject`]
* eSpeak-ng (For pronunciations and audio) [Arch: `espeak-ng`]

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
