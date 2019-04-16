# Reo ~ The Simple Dictionary
**Reo** is a dictionary application using the WordNet 3.1 (or 3.0) database for definitions and the reliable eSpeak for pronunciations (both audio and phoneme).

![In Light Mode](/ss.png?raw=true)

![In Dark Mode](/ss1.png?raw=true)

### Pretty much abandoned. But also pretty stable.  
I don't think it needs any improvements for now. It works on older and newer distributions.

### Requirements
 * DICT official client and server (dictd and dict)
 * WordNet 3.1 or 3.0 database for dictd (dict-wn)
 * Python 3 (2 is not supported)
 * Python GObject
 * Gtk+ 3.20+
 * eSpeak (For pronunciations and audio)

### Features
 * Neat output with proper coloring and formatting
 * Random Word
 * Custom Definitions feature using Pango Markup Syntax for formatting
 * Lightweight. 3.7 mb only and further reducible
 * Support for GNOME Dark Mode and launching app in dark mode.
 * Easter eggs ;)

#### Why no Python 2 support?
Python 2 lacks a lot of things used by Reo like proper Unicode support, which from shutil and more.

#### Future
Honestly, I feel like just deleting this and forgetting it ever existed. But well, it works and has no bugs I know. So, guess I'll keep it.
