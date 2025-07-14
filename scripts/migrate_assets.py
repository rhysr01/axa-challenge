#!/usr/bin/env python3
"""
AXA Asset Migration Script

This script helps migrate static assets to the new axa_theme directory structure.
"""
import os
import shutil
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).parent.parent
STATIC_DIR = BASE_DIR / "axa_app_mvp" / "static"
THEME_DIR = STATIC_DIR / "axa_theme"

# Asset mappings - source: destination
ASSET_MAPPINGS = {
    # CSS
    "css/design-system.css": "css/design-system.css",
    "css/main.css": "css/main.css",
    
    # Icons and images
    "img/axa-logo.svg": "img/axa-logo.svg",
    "img/axa-logo-white.svg": "img/axa-logo-white.svg",
    "img/favicon.ico": "img/favicon.ico",
    "img/favicon-16x16.png": "img/favicon-16x16.png",
    "img/favicon-32x32.png": "img/favicon-32x32.png",
    "img/apple-touch-icon.png": "img/apple-touch-icon.png",
    "img/site.webmanifest": "img/site.webmanifest",
    
    # Fonts
    "fonts/HelveticaNeue.woff2": "fonts/HelveticaNeue.woff2",
    "fonts/HelveticaNeue.woff": "fonts/HelveticaNeue.woff",
    "fonts/HelveticaNeue-Bold.woff2": "fonts/HelveticaNeue-Bold.woff2",
    "fonts/HelveticaNeue-Bold.woff": "fonts/HelveticaNeue-Bold.woff",
}

def migrate_assets():
    """Migrate assets to the new theme directory structure."""
    print("Starting asset migration...")
    
    # Create theme directories if they don't exist
    (THEME_DIR / "css").mkdir(parents=True, exist_ok=True)
    (THEME_DIR / "img").mkdir(parents=True, exist_ok=True)
    (THEME_DIR / "fonts").mkdir(parents=True, exist_ok=True)
    
    # Copy files to new locations
    for src, dst in ASSET_MAPPINGS.items():
        src_path = STATIC_DIR / src
        dst_path = THEME_DIR / dst
        
        if src_path.exists():
            print(f"Copying {src_path} to {dst_path}")
            shutil.copy2(src_path, dst_path)
        else:
            print(f"Warning: Source file not found: {src_path}")
    
    print("\nAsset migration complete!")
    print("\nNext steps:")
    print("1. Update template files to reference the new asset locations")
    print("2. Test all pages to ensure assets load correctly")
    print("3. Remove old asset files once migration is confirmed working")

if __name__ == "__main__":
    migrate_assets()
