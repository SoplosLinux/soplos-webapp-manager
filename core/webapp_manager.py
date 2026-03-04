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
from typing import List, Dict, Optional

from .browser_manager import BrowserManager, Browser

class WebApp:
    """Represents an installed WebApp."""
    def __init__(self, id_name: str, name: str, url: str, browser_id: str, icon_path: str, desktop_file: str, profile_path: str):
        self.id_name = id_name
        self.name = name
        self.url = url
        self.browser_id = browser_id
        self.icon_path = icon_path
        self.desktop_file = desktop_file
        self.profile_path = profile_path

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
            try:
                # configparser needs a single section to read cleanly, .desktop files have [Desktop Entry]
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
                    
                    # Basic heuristic to extract URL: look for http
                    for part in exec_cmd.split():
                        if part.startswith("http://") or part.startswith("https://"):
                            url = part
                            break
                    
                    # Find which browser corresponds
                    for brw in self.browser_manager.get_browsers_list():
                        if brw.executable in exec_cmd or (brw.is_flatpak and brw.flatpak_id in exec_cmd):
                            browser_id = brw.id_name
                            break
                    
                    webapps.append(WebApp(id_name, name, url, browser_id, icon, str(file), profile_path))
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
            if profile_dir.exists():
                shutil.rmtree(profile_dir)
        except:
            success = False
            
        return success

    def create_webapp(self, name: str, url: str, icon_path: str, category: str, browser_id: str, show_navbar: bool = False) -> Optional[WebApp]:
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
            
        class_name = f"WebApp-{id_name}"
        exec_cmd = browser.get_launch_command(url, str(profile_path), class_name, show_navbar)
        
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
"""
        
        with open(desktop_file, 'w') as f:
            f.write(desktop_content)
            
        # Make the desktop file executable
        os.chmod(desktop_file, 0o755)
        
        return WebApp(id_name, name, url, browser_id, icon_path, str(desktop_file), str(profile_path))

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
