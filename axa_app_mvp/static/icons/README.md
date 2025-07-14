# AXA App Icons

This directory contains the app icons for the AXA Elderly Care PWA.

## Required Icons

For full PWA support, the following icon sizes are required:

- 72x72 px
- 96x96 px
- 128x128 px
- 144x144 px
- 152x152 px
- 192x192 px (used for home screen and app launcher)
- 384x384 px
- 512x512 px (used for splash screen)

## Generating Icons

1. Place your high-resolution source icon (1024x1024px recommended) in this directory as `icon-source.png`
2. Run the `generate-icons.sh` script to generate all required sizes
3. The script will create all the necessary icon files with the correct names

## Updating Icons

To update the icons:

1. Replace the `icon-source.png` with your new icon
2. Run the `generate-icons.sh` script again
3. Update the `manifest.json` file if you've changed the icon file names or locations
