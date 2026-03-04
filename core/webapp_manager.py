"""
Web Application integration logic.
Manages the creation, listing, and deletion of custom .desktop files
and isolated browser profiles.
"""

import os
import shutil
import uuid
import configparser
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urlparse

from .browser_manager import BrowserManager, Browser

class WebApp:
    """Represents an installed WebApp."""
    def __init__(self, id_name: str, name: str, url: str, browser_id: str, icon_path: str, desktop_file: str, profile_path: str, show_navbar: bool = False, extra_params: str = ""):
        self.id_name = id_name
        self.name = name
        self.url = url
        self.browser_id = browser_id
        self.icon_path = icon_path
        self.desktop_file = desktop_file
        self.profile_path = profile_path
        self.show_navbar = show_navbar
        self.extra_params = extra_params

class WebAppManager:
    def __init__(self, browser_manager: BrowserManager):
        self.browser_manager = browser_manager
        self.desktop_dir = Path.home() / ".local" / "share" / "applications"
        self.profiles_dir = Path.home() / ".local" / "share" / "soplos-webapps"
        
        self.desktop_dir.mkdir(parents=True, exist_ok=True)
        self.profiles_dir.mkdir(parents=True, exist_ok=True)

    def list_webapps(self) -> List[WebApp]:
        """List all installed soplos webapps."""
        webapps = []
        for file in self.desktop_dir.glob("soplos-webapp-*.desktop"):
            config = configparser.ConfigParser(interpolation=None)
            config.optionxform = str # Preserve case for reading correctly
            try:
                config.read(file)
                if "Desktop Entry" in config:
                    entry = config["Desktop Entry"]
                    
                    id_name = file.stem.replace("soplos-webapp-", "")
                    name = entry.get("Name", id_name)
                    icon = entry.get("Icon", "")
                    exec_cmd = entry.get("Exec", "")
                    
                    # Try to reconstruct the URL and browser from the Exec command
                    url = ""
                    browser_id = "unknown"
                    profile_path = str(self.profiles_dir / id_name)
                    
                    # Basic heuristic to extract URL
                    for part in exec_cmd.split():
                        if part.startswith("http://") or part.startswith("https://"):
                            url = part
                            break
                        elif part.startswith("--app="):
                            url = part.replace("--app=", "")
                            break
                    
                    # Find which browser corresponds
                    for brw in self.browser_manager.get_browsers_list():
                        if brw.executable in exec_cmd or (brw.is_flatpak and brw.flatpak_id in exec_cmd):
                            browser_id = brw.id_name
                            break
                    
                    # Read navbar state from custom field
                    show_navbar_val = entry.get("X-Soplos-Navbar", "false")
                    show_navbar = show_navbar_val.lower() == "true"
                    
                    # Read extra params from custom field
                    extra_params = entry.get("X-Soplos-ExtraParams", "")
                    
                    webapps.append(WebApp(id_name, name, url, browser_id, icon, str(file), profile_path, show_navbar, extra_params))
            except Exception as e:
                print(f"Error reading {file}: {e}")
                
        return webapps

    def delete_webapp(self, id_name: str) -> bool:
        """Removes a webapp from the system."""
        desktop_file = self.desktop_dir / f"soplos-webapp-{id_name}.desktop"
        profile_dir = self.profiles_dir / id_name
        
        success = True
        try:
            if desktop_file.exists():
                desktop_file.unlink()
        except:
            success = False
            
        try:
            # Also cleanup any compatibility symlinks
            for sym in self.desktop_dir.glob("chrome-*.desktop"):
                if sym.is_symlink() and str(sym.readlink()).endswith(f"soplos-webapp-{id_name}.desktop"):
                    sym.unlink()
                    
            if profile_dir.exists():
                shutil.rmtree(profile_dir)
        except:
            success = False
            
        return success

    def _manage_chrome_compat_links(self, id_name: str, url: str, browser_id: str):
        """
        KDE Plasma 6 (Wayland) often ignores --wayland-app-id and looks for a .desktop
        matching an internal ID like 'chrome-host.com__-Default'.
        We create a symlink with that name pointing to our soplos-webapp-*.desktop.
        """
        # Only for Chrome-based browsers
        if browser_id not in ["chrome", "chromium", "brave", "vivaldi", "edge"]:
            return
            
        try:
            parsed = urlparse(url)
            host = parsed.netloc
            if not host:
                return
                
            # Remove any existing symlinks for this specific webapp first
            for sym in self.desktop_dir.glob("chrome-*.desktop"):
                if sym.is_symlink() and str(sym.readlink()).endswith(f"soplos-webapp-{id_name}.desktop"):
                    sym.unlink()
                    
            # Create the link KWin expects: chrome-{host}__-Default.desktop
            # Based on user's dbus-send: "chrome-web.whatsapp.com__-Default"
            compat_name = f"chrome-{host}__-Default.desktop"
            target_name = f"soplos-webapp-{id_name}.desktop"
            compat_path = self.desktop_dir / compat_name
            target_path = self.desktop_dir / target_name
            
            if target_path.exists() and not compat_path.exists():
                os.symlink(target_path.name, compat_path)
        except Exception as e:
            print(f"Error creating compatibility symlink: {e}")

    def update_webapp(self, id_name: str, new_name: str = None, new_icon: str = None, new_category: str = None, 
                      new_url: str = None, new_browser_id: str = None, new_show_navbar: bool = None, new_extra_params: str = None) -> bool:
        """Updates an existing webapp's .desktop file."""
        desktop_file = self.desktop_dir / f"soplos-webapp-{id_name}.desktop"
        if not desktop_file.exists():
            return False
        
        config = configparser.ConfigParser(interpolation=None)
        config.optionxform = str  # IMPORTANT: Preserve case (Exec instead of exec)
        config.read(desktop_file)
        
        if "Desktop Entry" not in config:
            return False
        
        entry = config["Desktop Entry"]
        
        # Cleanup any lowercase keys from previous buggy version to avoid DuplicateOptionError later
        standard_keys = ["Name", "Exec", "Icon", "Categories", "StartupWMClass", "Terminal", "Type", "Version", "Comment", "StartupNotify"]
        for key in list(entry.keys()):
            if key != "X-Soplos-Navbar" and key.lower() in [k.lower() for k in standard_keys]:
                if key not in standard_keys: # If it's not the exact standard casing, remove it
                    del entry[key]

        # Always align StartupWMClass with the desktop filename for Wayland compatibility
        class_name = f"soplos-webapp-{id_name}"
        entry["StartupWMClass"] = class_name
        
        if new_name:
            entry["Name"] = new_name
            entry["Comment"] = f"Soplos WebApp for {new_name}"
        if new_icon:
            entry["Icon"] = new_icon
        if new_category:
            entry["Categories"] = f"{new_category};"
            
        # Extract current data if not provided
        exec_cmd = entry.get("Exec", "")
        # ... fallback for lowercase if it was already corrupted
        if not exec_cmd:
            exec_cmd = entry.get("exec", "")
            
        current_url = ""
        current_browser_id = "unknown"
        
        for part in exec_cmd.split():
            if part.startswith("http://") or part.startswith("https://"):
                current_url = part
                break
            elif part.startswith("--app="):
                current_url = part.replace("--app=", "")
                break
        
        for brw in self.browser_manager.get_browsers_list():
            if brw.executable in exec_cmd or (brw.is_flatpak and brw.flatpak_id in exec_cmd):
                current_browser_id = brw.id_name
                break
        
        url = new_url if new_url is not None else current_url
        browser_id = new_browser_id if new_browser_id is not None else current_browser_id
        
        # Extra parameters
        if new_extra_params is not None:
            extra_params = new_extra_params
        else:
            extra_params = entry.get("X-Soplos-ExtraParams", "")
            
        # Save extra params state in custom field
        entry["X-Soplos-ExtraParams"] = extra_params
        
        # Determine show_navbar
        if new_show_navbar is not None:
            show_navbar = new_show_navbar
        else:
            # Try to read from X-Soplos-Navbar first, fallback to heuristic
            show_navbar_val = entry.get("X-Soplos-Navbar", "")
            if show_navbar_val:
                show_navbar = show_navbar_val.lower() == "true"
            else:
                show_navbar = "--nav" in exec_cmd or "userChrome.css" not in exec_cmd
        
        # Save navbar state in custom field
        entry["X-Soplos-Navbar"] = "true" if show_navbar else "false"
            
        if url and browser_id != "unknown":
            browser = self.browser_manager.get_browser(browser_id)
            if browser:
                profile_path = self.profiles_dir / id_name
                if browser.id_name in ["firefox", "librewolf"]:
                    self._setup_firefox_profile(str(profile_path), show_navbar)
                entry["Exec"] = browser.get_launch_command(url, str(profile_path), class_name, show_navbar, extra_params)
        
        with open(desktop_file, 'w') as f:
            # IMPORTANT: space_around_delimiters=False for .desktop compliance
            config.write(f, space_around_delimiters=False)
        
        os.chmod(desktop_file, 0o755)
        
        # Add Chrome compatibility symlink for KDE Plasma 6 Wayland
        self._manage_chrome_compat_links(id_name, url, browser_id)
        
        os.system("update-desktop-database ~/.local/share/applications 2>/dev/null")
        return True


    def create_webapp(self, name: str, url: str, icon_path: str, category: str, browser_id: str, show_navbar: bool = False, extra_params: str = "") -> Optional[WebApp]:
        """Creates a new webapp."""
        browser = self.browser_manager.get_browser(browser_id)
        if not browser:
            print(f"Browser {browser_id} not found.")
            return None
            
        # Generate a safe unique ID
        safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_name = safe_name.replace(" ", "-").lower()
        id_name = f"{safe_name}-{str(uuid.uuid4())[:6]}"
        
        profile_path = self.profiles_dir / id_name
        profile_path.mkdir(parents=True, exist_ok=True)
        
        # Specific browser profile setup (Firefox needs userChrome.css to act like an SSB)
        if browser.id_name in ["firefox", "librewolf", "firefox-flatpak"]:
            self._setup_firefox_profile(str(profile_path), show_navbar)
            
        class_name = f"soplos-webapp-{id_name}"
        exec_cmd = browser.get_launch_command(url, str(profile_path), class_name, show_navbar, extra_params)
        
        desktop_file = self.desktop_dir / f"soplos-webapp-{id_name}.desktop"
        
        desktop_content = f"""[Desktop Entry]
Version=1.0
Name={name}
Comment=Soplos WebApp for {name}
Exec={exec_cmd}
Terminal=false
X-MultipleArgs=false
Type=Application
Icon={icon_path}
Categories={category};
StartupWMClass={class_name}
StartupNotify=true
X-Soplos-Navbar={"true" if show_navbar else "false"}
X-Soplos-ExtraParams={extra_params}
"""

        
        with open(desktop_file, 'w') as f:
            f.write(desktop_content)
            
        # Make the desktop file executable
        os.chmod(desktop_file, 0o755)
        
        # Add Chrome compatibility symlink for KDE Plasma 6 Wayland
        self._manage_chrome_compat_links(id_name, url, browser_id)
        
        os.system("update-desktop-database ~/.local/share/applications 2>/dev/null")
        
        return WebApp(id_name, name, url, browser_id, icon_path, str(desktop_file), str(profile_path), show_navbar, extra_params)

    def _setup_firefox_profile(self, profile_path: str, show_navbar: bool):
        """Creates user.js and userChrome.css to strip UI from Firefox."""
        chrome_dir = os.path.join(profile_path, "chrome")
        os.makedirs(chrome_dir, exist_ok=True)
        
        user_js_path = os.path.join(profile_path, "user.js")
        user_chrome_path = os.path.join(chrome_dir, "userChrome.css")
        
        # user.js to disable telemetry and enable custom chrome
        user_js = """
// Enable custom CSS
user_pref("toolkit.legacyUserProfileCustomizations.stylesheets", true);
// Disable default browser checks
user_pref("browser.shell.checkDefaultBrowser", false);
user_pref("browser.tabs.warnOnClose", false);
// Session restore and privacy
user_pref("browser.startup.page", 3);
// Block telemetry
user_pref("datareporting.healthreport.uploadEnabled", false);
user_pref("datareporting.policy.dataSubmissionEnabled", false);
// Force system titlebar to show window controls (since tabs are hidden)
user_pref("browser.tabs.drawInTitlebar", false);
user_pref("browser.tabs.inTitlebar", 0);
"""
        with open(user_js_path, "w") as f:
            f.write(user_js)
            
        # CSS to hide Firefox UI elements
        user_chrome = """
@namespace url("http://www.mozilla.org/keymaster/gatekeeper/there.is.only.xul");
/* Hide tabs bar */
#TabsToolbar { visibility: collapse !important; }
/* Hide sidebar header */
#sidebar-header { visibility: collapse !important; }
"""
        if not show_navbar:
            user_chrome += """
/* Hide Navigation bar */
#nav-bar { visibility: collapse !important; }
/* Hide Bookmarks bar */
#PersonalToolbar { visibility: collapse !important; }
"""
        with open(user_chrome_path, "w") as f:
            f.write(user_chrome)
