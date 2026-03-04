#!/usr/bin/env python3
import sys
import os
import signal
import gettext
from pathlib import Path

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, Gdk, GdkPixbuf

# Basic configuration
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))
LOCALE_DIR = PROJECT_ROOT / "locale"
ASSETS_DIR = PROJECT_ROOT / "assets"

# Desktop integration (same values as wrapper, ensures consistency when run directly)
GLib.set_prgname('org.soplos.webappmanager')
GLib.set_application_name('soplos-webapp-manager')
Gtk.Window.set_default_icon_name('org.soplos.webappmanager')
if hasattr(Gdk, 'set_program_class'):
    Gdk.set_program_class('org.soplos.webappmanager')

# Set window icon from file (works even without hicolor installation)
_icon_file = ASSETS_DIR / 'icons' / 'org.soplos.webappmanager.png'
if _icon_file.exists():
    try:
        Gtk.Window.set_default_icon(GdkPixbuf.Pixbuf.new_from_file(str(_icon_file)))
    except Exception:
        pass

# Fast native internationalization
gettext.bindtextdomain('soplos-webapp-manager', str(LOCALE_DIR))
gettext.textdomain('soplos-webapp-manager')
try:
    _ = gettext.translation('soplos-webapp-manager', str(LOCALE_DIR)).gettext
except FileNotFoundError:
    _ = gettext.gettext

from core.browser_manager import BrowserManager
from core.webapp_manager import WebAppManager

def _cleanup_garbage():
    """Remove __pycache__ and other temporary files."""
    try:
        import shutil
        for root, dirs, files in os.walk(PROJECT_ROOT):
            if '__pycache__' in dirs:
                pycache_path = os.path.join(root, '__pycache__')
                try:
                    shutil.rmtree(pycache_path, ignore_errors=True)
                except Exception:
                    pass
    except Exception as e:
        print(f"Cleanup warning: {e}")

def main():
    print(_("Starting Soplos WebApp Manager..."))
    
    # Init managers
    browser_manager = BrowserManager()
    webapp_manager = WebAppManager(browser_manager)
    
    from ui.main_window import MainWindow
    
    app_window = MainWindow(browser_manager, webapp_manager, _, ASSETS_DIR)
    app_window.connect("destroy", Gtk.main_quit)
    app_window.show_all()
    
    try:
        Gtk.main()
    except KeyboardInterrupt:
        pass
    finally:
        _cleanup_garbage()
        
    return 0

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    sys.exit(main())
