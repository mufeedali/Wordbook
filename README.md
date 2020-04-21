# Reo ~ The Simple Dictionary

**Reo** is a dictionary application using the WordNet 3.1 (or 3.0) database for definitions and the reliable eSpeak for pronunciations (both audio and phoneme).

Light Mode                             |  Dark Mode
:-------------------------------------:|:-------------------------------------:
![Light Mode](images/ss.png?raw=true)  |  ![Dark Mode](images/ss1.png?raw=true)

## Requirements

* DICT official client and server (dictd and dict) [Arch: `dictd`]
* WordNet 3.1 or 3.0 database for dictd (dict-wn) [Arch AUR: `dict-wn`]
* Python 3 [Arch: `python`]
* Python GObject [Arch: `python-gobject`] or PyQt5 [Arch: `python-pyqt5`]
* GTK 3.20+ [Arch: `gtk3`] or Qt 5.8+ [Arch: `qt5-base`]
* eSpeak-ng (For pronunciations and audio) [Arch: `espeak-ng`]

Run `reo-gtk` for the GTK GUI or `reo-qt` for the Qt GUI.

## Features

* Neat output with proper coloring and formatting
* Random Word
* Live Search
* Custom Definitions feature using Pango Markup or an HTML subset for formatting
* Lightweight. 1 mb only and further reducible (It does nothing on its own, so yeah)
* Support for GNOME Dark Mode and launching app in dark mode. Also supports gtk3-nocsd.

## Installation

To install, first make sure of the dependencies as listed above.

```bash
python setup.py install
```

For development (i.e. to see changes live as you make them):

```bash
python setup.py develop
```

## Troubleshooting

### Slow output

If the output is slow, it's possibly because the definition is obtained from dict.org rather than localhost. So, run

```bash
sudo systemctl enable --now dictd.service
```

### Qt5 Interface

The Qt GUI is now pretty stable and seems to work well enough but the GTK GUI is still the recommended version, for now and probably forever. But Qt5 is fun to work with, so I'll be working on it anyway.

Right now, the Qt5 GUI already has almost all features of the GTK 3 GUI. Features that are not here yet are:

* Dark mode: It's currently suited for dark mode usage and not light mode, but that said, there's no switch yet.
* Live Search: It's there but only through a commandline option.

Another important thing to note is that the use of Qt5 won't make it cross-platform. It's still Linux-only and probably will remain so.

## Credits

* Restructured using the excellent [`cookiecutter-pypackage`](https://github.com/audreyr/cookiecutter-pypackage/) template with [`cookiecutter`](https://github.com/cookiecutter/cookiecutter).
* Some of the restructuring was inspired by [`trackma`](https://github.com/z411/trackma).

## Future

For me, this is more of an experiment than anything else. I try a lot of things, a lot of things work, a lot of things don't and I find it fun to play around with this. I also try code that I don't really understand in other projects (not risky stuff ofc), try to follow code standards and slowly try to get better at writing good code. I'm still bad at it though. Basically, a lot of this is experimentation and I don't plan to stop anytime soon, but somehow or the other, the project is generally stable and works for my daily use and I look up words a lot.

Basically it's just a GUI for some CLI tools. It doesn't even directly interact with dictd. And even the UI is badly done with Glade for GTK and Qt Designer for Qt5. So yeah, I'm lazy.
