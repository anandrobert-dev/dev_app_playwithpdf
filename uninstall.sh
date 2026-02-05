#!/bin/bash
# Oi360 PDF Suite Uninstaller

echo "Uninstalling Oi360 PDF Suite..."

rm -f ~/.local/bin/Oi360_Suite
rm -f ~/.local/share/icons/hicolor/256x256/apps/oi360-pdf-suite.png
rm -f ~/.local/share/applications/oi360-pdf-suite.desktop

# Refresh
gtk-update-icon-cache ~/.local/share/icons/hicolor 2>/dev/null || true
update-desktop-database ~/.local/share/applications 2>/dev/null || true

echo "Uninstall complete!"
