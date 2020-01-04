# Reo ~ The Simple Dictionary
**Reo** is a dictionary application using the WordNet 3.1 (or 3.0) database for definitions and the reliable eSpeak for pronunciations (both audio and phoneme).

Light Mode                       |  Dark Mode
:-------------------------------:|:--------------------------------:
![Light Mode](/ss.png?raw=true)  |  ![Dark Mode](/ss1.png?raw=true)

### Requirements
 * DICT official client and server (dictd and dict)
 * WordNet 3.1 or 3.0 database for dictd (dict-wn)
 * Python 3
 * Python GObject
 * Gtk+ 3.20+
 * eSpeak-ng (For pronunciations and audio)

You can confirm all the requirements by running Reo with the arguments `--check` (`-c`) or `--adversion` (`-d`).

#### Slow?
If the output is slow, it's possibly because the definition is obtained from dict.org rather than localhost. So, run  
`sudo systemctl enable dictd.service && sudo systemctl start dictd.service`

### Features
 * Neat output with proper coloring and formatting
 * Random Word
 * Custom Definitions feature using Pango Markup Syntax for formatting
 * Lightweight. 1 mb only and further reducible (It does nothing on its own, so yeah)
 * Support for GNOME Dark Mode and launching app in dark mode. Also supports gtk3-nocsd.

#### Files

 * `reo.py`: The Gtk3 application. Executable. It's the main code for now.
 * `reo.ui`: The Glade file from which the UI is loaded. Not executable.
 * `reo_base.py`: Code that was originally in `reo.py` made a separate module for reusing the code in the Qt5 interface. Not executable.
 * `reo_qt.py`: The Qt5 interface. A WIP, just barely works. Executable.
 * `ui_build.py`: Minor script to compile the Qt5 UI file and pass it to `autopep8`.

#### Qt5 Interface

Unlike the Gtk3 version, which works quite well already, the Qt5 interface is more of an experiment. I just wanted to see how easy it would be to port Reo over to Qt5. While I do plan to add all the features from the Gtk3 version over to the Qt5 version, the Gtk version is the recommended version, for now and probably forever, especially since Gtk3 applications will look native on Plasma (on X11. It already looked good on Plasma Wayland.) starting from KDE 5.18 LTS. But Qt5 is fun to work with, so I'll be working on it anyway.

`reo_qt.py` imports `qtpy`, which allows it to make use of whatever Qt5 bindings are available on the system. qtpy is available on the repositories of most major distributions (`python-qtpy` on most of them).

Another important thing to note is that the use of Qt5 won't make it cross-platform. It's still Linux-only and probably will remain so.

#### Future
Honestly, I feel like just deleting this and forgetting it ever existed. But well, it works and has no bugs I know. So, guess I'll keep it and since I do use it, I might improve a lot of the little things. But overall, I'm pretty satisfied with this.  

Basically it's just a GUI for some CLI tools. It doesn't even directly interact with dictd. And even the UI is badly done with Glade. So yeah, I'm lazy.
