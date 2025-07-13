#!/bin/bash
# AXA MVP Project Cleanup Script
# This will remove duplicate/legacy folders and virtual environments.
# Review before running!

set -e

# Remove Python virtual environments
rm -rf .venv
rm -rf axa-challenge/axa-challenge/venv
rm -rf adapt/.venv

# Remove nested/legacy axa-challenge folder (after confirming no unique code needed)
rm -rf axa-challenge/axa-challenge

# Remove top-level qr, utils, vitalscan if not needed (uncomment if confirmed)
# rm -rf qr
# rm -rf utils
# rm -rf vitalscan

# Remove the duplicate finder script itself
rm -f find_duplicates.py

# Done

echo "Cleanup complete. Review axa_app_mvp/ for your main project."
