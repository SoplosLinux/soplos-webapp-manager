# Soplos WebApp Manager

![Soplos WebApp Manager Icon](assets/icons/128x128/org.soplos.webappmanager.png)

**Soplos WebApp Manager** is an elegant, lightweight Site Specific Browser (SSB) engine tailored for Soplos Linux. It effortlessly turns any website into a standalone, desktop-integrated application utilizing isolated browser profiles for maximum privacy and separation from your primary web session.

## Screenshots

<div align="center">
  <img src="assets/screenshots/screenshot1.png" width="30%" alt="Main Window"/>
  <img src="assets/screenshots/screenshot2.png" width="30%" alt="Creation Dialog"/>
  <img src="assets/screenshots/screenshot3.png" width="30%" alt="WebApp Running"/>
</div>

## Features

- 🌐 **Multi-Engine Support**: Native or Flatpak versions of Firefox, Chrome, Chromium, Brave, Vivaldi, Edge, and Epiphany.
- ✏️ **Full WebApp Editing**: Reconfigure Name, URL, Icon, and Browser settings at any time without recreating the profile.
- ⚙️ **Extra Browser Parameters**: Add custom flags like `--start-maximized` or `--kiosk` with a new built-in help guide.
- 🔒 **Total Isolation & Incognito**: Generates sandboxed profiles and supports Incognito mode sessions.
- 🎨 **Soplos UI Integration**: Official status bar with automatic detection of DE (GNOME/Plasma/XFCE) and protocol (Wayland/X11).
- 🧩 **No-UI Implementation**: Customized Firefox launch using `userChrome.css` and dynamic StartupWMClass mapping.
- 🤖 **Smart Favicons**: HD icons automatically downloaded via Google Favicon API. 
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

## 🆕 New in version 1.0.0-2 (March 21, 2026)

- **About dialog**: Press F1 or use the GNOME application menu to open the About dialog.

## License
This project is licensed under the GPL-3.0 License - see the `debian/copyright` file for details.
