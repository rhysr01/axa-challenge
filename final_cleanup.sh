#!/bin/bash
# Final cleanup for AXA MVP project root
# This will remove all legacy/unused folders except for axa_app_mvp, .git, .gitignore, and readme.md
# Review before running!

set -e

rm -rf adapt
rm -rf axa-challenge
rm -rf qr
rm -rf utils
rm -rf vitalscan
rm -f cleanup_project.sh

echo "Final cleanup complete. Only axa_app_mvp/, .git, .gitignore, and readme.md remain."
