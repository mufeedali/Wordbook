<h1 align="center">
<img height="128" src="data/icons/dev.mufeed.Wordbook.svg" alt="Wordbook"/><br>
Wordbook
</h1>

<p align="center">Look up definitions for words</p>

<p align="center">
    <img title="Wordbook" src="screenshots/dark.png?raw=true">
</p>

<p align="center">
<b>Wordbook</b> is an offline English-English dictionary application built for GNOME using the <a href="https://github.com/globalwordnet/english-wordnet">Open English WordNet</a> database for definitions and the reliable eSpeak for pronunciations (both audio and phoneme).
</p>

## Features

* Fully offline after initial data download
* Random Word
* Live Search
* Double click to search
* Support for GNOME Dark Mode and launching app in dark mode.

## Requirements

* GTK 4.6+ [Arch: `gtk4`]
* libadwaita 1.7.0+ [Arch: `libadwaita`]
* Python 3.12+ [Arch: `python`]
* Python modules:
    * RapidFuzz [Arch: `python-rapidfuzz`]
    * Pydantic [Arch: `python-pydantic`]
    * Python GObject [Arch: `python-gobject`]
    * ONLY if using Python versions older than 3.14, backports.zstd [Arch: `python-backports-zstd`]
* eSpeak-ng (For pronunciations and audio) [Arch: `espeak-ng`]

## Installation

### Using Flatpak

<a href='https://flathub.org/apps/details/dev.mufeed.Wordbook'><img width='240' alt='Download on Flathub' src='https://flathub.org/assets/badges/flathub-badge-en.png'/></a>

### Using Nix

[![](https://raw.githubusercontent.com/dch82/Nixpkgs-Badges/main/nixpkgs-badge-light.svg)](https://search.nixos.org/packages?size=1&show=wordbook)

This method can be used anywhere the Nix package manager is installed.

### Using distro-specific packages

Wordbook is packaged for Arch through the AUR as [`wordbook`](https://aur.archlinux.org/packages/wordbook).

On NixOS, Wordbook can be installed using the Nix package manager as shown above. Additionally, the following code can be added to your NixOS configuration file, usually located in `/etc/nixos/configuration.nix`.

```
  environment.systemPackages = [
    pkgs.wordbook
  ];
```

## Building from Source

To build Wordbook from source, use Meson:

```bash
meson setup builddir
meson compile -C builddir
meson install -C builddir
```

## Contributing

Contributions are welcome. There are many ways to contribute:

1. Open GitHub issues to report bugs or for feature requests.
2. Develop a feature or a bug fix. It would be best to open an issue or discussion first before developing a feature.
3. Add new translations or improve existing translations.

### Development

The best way to work with Wordbook is to either use [GNOME Builder](https://apps.gnome.org/Builder/) or to use [flatplay](https://github.com/mufeedali/flatplay) with your editor of choice.

### Translations

The easiest way to contribute to translations right now is to do one of the following:

1. Approve the LLM-generated translations by removing the line that says `# llm-generated`.
2. Replacing the LLM-generated translations.
3. Improving the human-translated strings.

The LLM-generated translations are to try and ease the burden on translators. The idea is to have temporary translations until a human can review them. All strings translated by LLMs are tagged as `llm-generated`.

## Code of Conduct

This project adheres to the [GNOME Code of Conduct](https://conduct.gnome.org/). By participating through any means, including PRs, Issues or Discussions, you are expected to uphold this code.
