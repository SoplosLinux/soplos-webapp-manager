# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/lang/en/).

## [1.0.0-3] - 2026-03-22

### 🔧 Fixed
- **UI colors**: Fixed background color inconsistency — window, list and scrolled area now consistently use the correct Soplos dark theme color (#2b2b2b).

---

## [1.0.0-2] - 2026-03-21

### ✨ Added
- **About dialog**: Press F1 or use the GNOME application menu to open the About dialog with version, author, license and website.

---

## [1.0.0-1] - 2026-03-10

### ✨ Standardized Soplos UI
- **Official Soplos Footer**: Implemented an official status bar following the Soplos ecosystem standard.
- **Environment Detection**: Added automatic identification of Desktop Environment (GNOME, Plasma, XFCE) and Protocol (Wayland, X11).
- **Incognito Mode**: New support for private browsing sessions with fully isolated profiles.
- **Extended Parameters Help**: Added a comprehensive guide for advanced browser flags and parameters.
- **UI Alignment**: Consistent use of `dim-label` styling and standard margins (15, 15, 8, 8) for seamless transition between Soplos apps.

## [1.0.0] - 2026-03-04

### 🎉 Initial Release
- **Full WebApp Editing**: Users can now edit Name, URL, Icon, Browser, and Navigation Bar settings for existing WebApps.
- **Extra Browser Parameters**: Support for custom browser flags (e.g., `--start-maximized`, `--kiosk`) both at creation and editing.
- **Improved Wayland Compatibility**: Enhanced icon mapping and window association for KDE Plasma 6 and other modern environments.
- **Independent Firefox Instances**: Optimized Firefox SSB behavior with truly isolated processes and dedicated icons.
- **Smart Favicons**: Fallback mechanism to natively download high-quality website icons via Google Favicons API.
- **Full Internationalization (i18n)**: Translation ready for the 8 default languages in Soplos Linux.

---

## Types of Changes

- **Added** for new features
- **Improved** for changes in existing functionality
- **Deprecated** for soon-to-be removed features
- **Removed** for removed features
- **Fixed** for bug fixes
- **Security** for vulnerabilities

## Author

Developed and maintained by Sergi Perich  
Website: https://soplos.org  
Contact: info@soploslinux.com

## Contributing

To report bugs or request features:
- **Issues**: https://github.com/SoplosLinux/soplos-webapp-manager/issues
- **Email**: info@soploslinux.com

## Support

- **Documentation**: https://soplos.org
- **Community**: https://soplos.org/foros/
- **Support**: info@soploslinux.com
