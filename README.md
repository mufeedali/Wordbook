# Reo ~ The Simple Dictionary
**Reo** is a dictionary application using the WordNet 3.1 (or 3.0) database for definitions and the reliable eSpeak for pronunciations (both audio and phoneme).

### Requirements
 * DICT official client and server (dictd and dict)
 * WordNet 3.1 or 3.0 database for dictd (dict-wn)
 * Python 3 (2 is not supported)
 * Python GObject
 * Gtk+ 3.20+ (3.16+ should work but not ideally)
 * eSpeak (For pronunciations and audio)

### Features
 * Neat output with proper coloring and formatting
 * Random Word feature for learning new things
 * Beautiful HeaderBar-based UI that is truly Unique to Reo and Rerun
 * Optimized Code with further optimizations coming each day
 * Custom Definitions feature using Pango Markup Syntax for formatting
 * Lightweight. 3.7 mb only and further reducible (Tips at End)
 * Support for GNOME Dark Mode and launching app in dark mode.
 * Easter eggs ;)

#### Why no Python 2 support?
Python 2 lacks a lot of things used by Reo like proper Unicode support, which from shutil and more. But I would like proper Python 2 support because, as noted in a commit to Rerun, I've noticed better performance in Python 2 than Python 3 though by very small margins.

#### Gtk versions before Gtk+ 3.20?
Gtk+ 3.14 and below are IMPOSSIBLE. Gtk+ 3.16 and 3.18 should also work. However, it is not recommended as the UI might not appear as intended, though usable.

**Tips**

 * Determine your WordNet version and then, delete the index file (wn3.1 or wn3.0) for the version that you do not require. This will save you about 2 MBs of space.

 * After you have confirmed that everything is working fine for you, open 'reo' in a text editor and remove all the print statements put in for logging. This should improve performance though not noticeably. This is only in master for now and once Git Flow is used this will not be the case and you won't have to do this manually.  
 **UPDATE**: This is not applicable anymore since pretty much all print statements are removed before pushing to master.

 * Also, if you can, clean up the code on-the-whole according to how your system is set up. It shouldn't be all that hard. Just remove bits you won't need (like Random Word for some), remove version detections and remove the corresponding imports. This can improve performance greatly. Reo was built to be tweakable, so this should be easy.  
 More recent versions to the code should be easier to comprehend and thus easier to modify to your will.  

 * Custom definitions (to be placed in "~/.reo/cdef") are given higher priority over definitions obtained from dictd. Furthermore, the warning displayed for custom definitions can be hidden by adding "[warninghide]" as the last line in the custom definition. This can be advantageously used to replace erroneous definitions or add missing definitions on your own. It would be great if you could put said custom definition as an issue in Github.

#### Future
I might not get to work on this project anymore. Fork it if you wish so.
