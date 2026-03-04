# Soplos WebApp Manager

![Soplos WebApp Manager Icon](assets/icons/128x128/soplos-webapp-manager.png)

**Soplos WebApp Manager** is an elegant, lightweight Site Specific Browser (SSB) engine tailored for Soplos Linux. It effortlessly turns any website into a standalone, desktop-integrated application utilizing isolated browser profiles for maximum privacy and separation from your primary web session.

## Screenshots

<div align="center">
  <img src="assets/screenshots/screenshot1.png" width="30%" alt="Main Window"/>
  <img src="assets/screenshots/screenshot2.png" width="30%" alt="Creation Dialog"/>
  <img src="assets/screenshots/screenshot3.png" width="30%" alt="WebApp Running"/>
</div>

## Features

- 🌐 **Multi-Engine Support**: Native or Flatpak versions of Firefox, Chrome, Chromium, Brave, Vivaldi, Edge, and Epiphany.
- 🔒 **Total Isolation**: Generates sandboxed `~/.local/share/soplos-webapps/` profiles avoiding cookie crossover.
- 🎨 **Minimalist Integration**: Built on GTK3, automatically adopting systemic Dark/Light themes under X11 or Wayland.
- 🧩 **No-UI Implementation**: Features a customized Firefox launch using `userChrome.css` to hide standard tabs bridging a native-like experience. 
- 🤖 **Smart Favicons**: Fetches 128px HD icons automatically utilizing Google Favicon API if local icon files aren't provided. 
- 🌍 **Internationalization**: Ships translated out-of-the-box for `es, en, fr, de, pt, it, ro, ru`.

## Requirements

- Python 3.10+
- GTK+ 3
- python3-gi
- At least one supported browser installed (native DEB/RPM or Flatpak).

## Installation

Usually shipped natively with Soplos Linux. To execute locally:

```bash
git clone https://github.com/SoplosLinux/soplos-webapp-manager.git
cd soplos-webapp-manager
python3 main.py
```

## Structure

```
soplos-webapp-manager/
├── assets/           # Icons and Desktop elements
├── core/             # Background logic (Profile generation, Binary detection)
├── debian/           # Deb packaging data
├── locale/           # Translation MO/PO strings
├── ui/               # GTK3 Interface
└── utils/            # Shared utilities (Favicon Fetcher)
```

## License
This project is licensed under the GPL-3.0 License - see the `debian/copyright` file for details.
