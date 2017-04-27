# Reo ~ The Simple Dictionary
**Reo** is a dictionary application using the WordNet 3.1 (or 3.0) database for definitions and the reliable eSpeak for pronunciations (both audio and phoneme).
### Requirements
 * DICT official client and server (dictd and dict)
 * WordNet 3.1 or 3.0 database for dictd (dict-wn)
 * Python 3 (2 is not supported)
 * Python GObject
 * Gtk+ 3.20+ (3.16+ should work but not ideally)

### Features
 * Neat output with proper coloring and formatting
 * Random Word feature for learning new things
 * Beautiful HeaderBar-based UI that is truly Unique to Reo and Rerun
 * Optimized Code with further optimizations coming each day
 * Custom Definitions feature using Pango Markup Syntax for formatting
 * Lightweight. 3.7 mb only and further reducible (Self-optimization Tips at End)
 * Support for GNOME Dark Mode and launching app in dark mode.
 * Easter eggs ;)

#### Why no Python 2 support?
Python 2 lacks a lot of things used by Reo like proper Unicode support, which from shutil and more. But I would like proper Python 2 support because, as noted in a commit to Rerun, I've noticed better performance in Python 2 than Python 3 though by very small margins.

#### Gtk versions before Gtk+3.20?
Gtk+3.14 and below are IMPOSSIBLE. Gtk+ 3.16 and 3.18 should also work. BUT the UI might seem horribly broken. If so, try reverting the UI changes in commit d543d27f1c520147ad8059d0ede1f3a07dc65368. This MIGHT fix it.
Still, the recommended versions remain Gtk+ 3.20 and above.

**Tips**  
Determine your WordNet version and then, delete the index file (wn3.1 or wn3.0) for the version that you do not require. This will save you about 2 MBs of space.  
After you have confirmed that everything is working fine for you, open 'reo' in a text editor and remove all the print statements put in for logging. This should improve performance though not noticeably. This is only in master for now and once Git Flow is used this will not be the case and you won't have to do this manually.  
Also, if you can, clean up the code on-the-whole according to how your system is set up. It shouldn't be all that hard. Just remove bits you won't need (like Random Word for some), remove version detections and remove the corresponding imports. This can improve performance greatly. Reo was built to be tweakable.

#### Future
The future is clear. Stabilize Reo first. Then, I will drop the first 2 requirements in a different project called *Jisho*. Eventually the third too.
