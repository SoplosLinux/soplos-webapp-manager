"""
Browser manager module.
Handles detection of installed browsers and their specific command line arguments
for launching in Site Specific Browser (SSB) mode.
"""

import os
import shutil
from typing import Dict, List, Optional


class Browser:
    def __init__(self, id_name: str, display_name: str, executable: str, is_flatpak: bool = False, flatpak_id: str = ""):
        self.id_name = id_name
        self.display_name = display_name
        self.executable = executable
        self.is_flatpak = is_flatpak
        self.flatpak_id = flatpak_id

    def get_launch_command(self, url: str, profile_path: str, class_name: str, show_navbar: bool = False, extra_params: str = "") -> str:
        """
        Generate the Exec command for the .desktop file.
        """
        cmd = []
        
        if self.is_flatpak:
            cmd.extend(["flatpak", "run", self.flatpak_id])
        else:
            cmd.append(self.executable)

        # Chrome / Chromium based
        if self.id_name in ["chromium", "chrome", "brave", "vivaldi", "edge"]:
            # Set environment variable for desktop integration (used by KDE/GNOME to map windows)
            cmd.insert(0, f"env CHROME_DESKTOP={class_name}.desktop")
            
            # Identity and platform flags FIRST: if they come after --app they might be ignored
            # Force native Wayland mode more aggressively
            cmd.append("--enable-features=UseOzonePlatform")
            cmd.append("--ozone-platform=wayland")
            
            cmd.append(f"--wayland-app-id={class_name}")
            cmd.append(f"--app-name={class_name}")
            cmd.append(f"--class={class_name}")
            cmd.append(f"--name={class_name}")
            cmd.append(f"--wm-class={class_name}")
            cmd.append(f"--user-data-dir={profile_path}")
            cmd.append(f"--app={url}")
            
        # Firefox based
        elif self.id_name in ["firefox", "librewolf"]:
            # Set environment variable for Wayland/modern DEs app-id matching
            cmd.insert(0, f"env MOZ_APP_REMOTINGNAME={class_name}")
            cmd.append("-no-remote")
            cmd.append("-new-instance")
            cmd.append("-profile")
            cmd.append(f'"{profile_path}"')
            # These work on X11
            cmd.append("-class")
            cmd.append(class_name)
            cmd.append("-name")
            cmd.append(class_name)
            cmd.append(url)
            
        # WebKit based (Epiphany)
        elif self.id_name == "epiphany":
            cmd.append("--application-mode")
            cmd.append(f"--profile={profile_path}")
            cmd.append(url)

        # Append extra parameters if any
        if extra_params:
            cmd.append(extra_params)
            
        return " ".join(cmd)



class BrowserManager:
    """Detects available browsers on the system."""
    
    SUPPORTED_BROWSERS = [
        {"id": "firefox", "name": "Mozilla Firefox", "bins": ["firefox", "firefox-esr"]},
        {"id": "chromium", "name": "Chromium", "bins": ["chromium", "chromium-browser"]},
        {"id": "chrome", "name": "Google Chrome", "bins": ["google-chrome", "google-chrome-stable"]},
        {"id": "brave", "name": "Brave", "bins": ["brave", "brave-browser"]},
        {"id": "vivaldi", "name": "Vivaldi", "bins": ["vivaldi", "vivaldi-stable"]},
        {"id": "edge", "name": "Microsoft Edge", "bins": ["microsoft-edge", "microsoft-edge-stable"]},
        {"id": "epiphany", "name": "GNOME Web", "bins": ["epiphany", "epiphany-browser"]}
    ]
    
    FLATPAK_BROWSERS = [
        {"id": "firefox", "name": "Firefox (Flatpak)", "flatpak_id": "org.mozilla.firefox"},
        {"id": "chromium", "name": "Chromium (Flatpak)", "flatpak_id": "org.chromium.Chromium"},
        {"id": "chrome", "name": "Google Chrome (Flatpak)", "flatpak_id": "com.google.Chrome"},
        {"id": "brave", "name": "Brave (Flatpak)", "flatpak_id": "com.brave.Browser"},
        {"id": "epiphany", "name": "GNOME Web (Flatpak)", "flatpak_id": "org.gnome.Epiphany"}
    ]

    def __init__(self):
        self.available_browsers: Dict[str, Browser] = {}
        self.detect_browsers()

    def detect_browsers(self):
        """Scans the system for supported browsers."""
        self.available_browsers.clear()
        
        # 1. Detect native binaries
        for b_info in self.SUPPORTED_BROWSERS:
            for bin_name in b_info["bins"]:
                executable = shutil.which(bin_name)
                if executable:
                    browser = Browser(
                        id_name=b_info["id"],
                        display_name=b_info["name"],
                        executable=executable
                    )
                    self.available_browsers[b_info["id"]] = browser
                    break # Found one binary for this browser type, move to next browser

        # 2. Detect flatpaks (if flatpak is installed)
        if shutil.which("flatpak"):
            try:
                import subprocess
                result = subprocess.run(["flatpak", "list", "--app", "--columns=application"], 
                                      capture_output=True, text=True)
                installed_flatpaks = result.stdout.splitlines()
                
                for fb in self.FLATPAK_BROWSERS:
                    if fb["flatpak_id"] in installed_flatpaks:
                        b_id = f"{fb['id']}-flatpak"
                        browser = Browser(
                            id_name=fb["id"],
                            display_name=fb["name"],
                            executable="flatpak",
                            is_flatpak=True,
                            flatpak_id=fb["flatpak_id"]
                        )
                        self.available_browsers[b_id] = browser
            except Exception as e:
                print(f"Error detecting Flatpak browsers: {e}")

    def get_browsers_list(self) -> List[Browser]:
        """Returns a list of available browsers."""
        return list(self.available_browsers.values())
        
    def get_browser(self, browser_id: str) -> Optional[Browser]:
        """Get a specific browser by its ID."""
        return self.available_browsers.get(browser_id)
