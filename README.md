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
* libadwaita 1.1.0+ [Arch: `libadwaita`]
* Python 3 [Arch: `python`]
* Standalone WordNet Python module [Arch AUR: `python-wn`]
* Python GObject [Arch: `python-gobject`]
* eSpeak-ng (For pronunciations and audio) [Arch: `espeak-ng`]

## Installation

### Using Flatpak

<a href='https://flathub.org/apps/details/dev.mufeed.Wordbook'><img width='240' alt='Download on Flathub' src='https://flathub.org/assets/badges/flathub-badge-en.png'/></a>

### Using Nix

[![](https://raw.githubusercontent.com/dch82/Nixpkgs-Badges/main/nixpkgs-badge-light.svg)](https://search.nixos.org/packages?size=1&show=wordbook)

This method can be used anywhere the Nix package manager is installed.

### Using distro-specific packages

Right now, Wordbook is only packaged for Arch through the AUR as [`wordbook`](https://aur.archlinux.org/packages/wordbook).

On NixOS, Wordbook can be installed using the Nix package manager as shown above. Additionally, the following code can be added to your NixOS configuration file, usually located in `/etc/nixos/configuration.nix`.

```
  environment.systemPackages = [
    pkgs.wordbook
  ];
```

### From Source

To install, first make sure of the dependencies as listed above. You can use `just` to make the process easy.

```bash
just setup
just install
```

Without `just`:
```bash
mkdir -p _build
meson setup . _build
ninja -C _build install
```

For a local build with debugging enabled:

```bash
just run
# OR
just setup
just develop-configure
just local-run
```

## Code of Conduct

This project adheres to the [GNOME Code of Conduct](https://conduct.gnome.org/). By participating through any means, including PRs, Issues or Discussions, you are expected to uphold this code.
