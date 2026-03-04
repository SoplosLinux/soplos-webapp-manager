import os
import urllib.request
import urllib.error
from urllib.parse import urlparse
from pathlib import Path

def download_favicon(url: str, output_dir: str) -> str:
    """
    Downloads the favicon for a given URL using smart fallback mechanisms.
    Returns the absolute path to the downloaded icon, or empty string if failed.
    """
    try:
        parsed_url = urlparse(url)
        if not parsed_url.scheme:
            url = "http://" + url
            parsed_url = urlparse(url)
            
        domain = parsed_url.netloc
        if not domain:
            return ""
            
        # Try finding root domain (last two parts) for duckduckgo fallback
        parts = domain.split('.')
        root_domain = ".".join(parts[-2:]) if len(parts) >= 2 else domain
        
        icon_urls = [
            f"https://icons.duckduckgo.com/ip3/{domain}.ico",
            f"https://icons.duckduckgo.com/ip3/{root_domain}.ico",
            f"https://www.google.com/s2/favicons?domain={domain}&sz=128"
        ]
        
        output_path = os.path.join(output_dir, f"favicon_{domain}.png")
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        for icon_url in icon_urls:
            try:
                req = urllib.request.Request(icon_url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
                with urllib.request.urlopen(req) as response:
                    with open(output_path, 'wb') as out_file:
                        out_file.write(response.read())
                return output_path
            except urllib.error.HTTPError as e:
                print(f"Fallback check: failed to fetch from {icon_url}: {e}")
                continue
                
        return ""
    except Exception as e:
        print(f"Error downloading favicon for {url}: {e}")
        return ""
