#!/bin/bash
# Oi360 PDF Suite Installer for Ubuntu/Linux
# Run this from the dist folder after building with PyInstaller

APP_NAME="Oi360_Suite"
ICON_NAME="logo.png"
DESKTOP_NAME="oi360-pdf-suite"

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "========================================="
echo "  Installing Oi360 PDF Suite..."
echo "========================================="

# Check if files exist in current directory
if [ ! -f "$SCRIPT_DIR/$APP_NAME" ]; then
    echo "ERROR: $APP_NAME not found in $SCRIPT_DIR"
    echo "Make sure to run this script from the dist folder!"
    exit 1
fi

if [ ! -f "$SCRIPT_DIR/$ICON_NAME" ]; then
    echo "WARNING: $ICON_NAME not found, icon may not display correctly"
fi

# Create folders if missing
mkdir -p ~/.local/bin
mkdir -p ~/.local/share/icons/hicolor/256x256/apps
mkdir -p ~/.local/share/applications

# Copy App
echo "Copying application..."
cp "$SCRIPT_DIR/$APP_NAME" ~/.local/bin/
chmod +x ~/.local/bin/"$APP_NAME"

# Copy Icon (to proper hicolor location for better compatibility)
echo "Installing icon..."
if [ -f "$SCRIPT_DIR/$ICON_NAME" ]; then
    cp "$SCRIPT_DIR/$ICON_NAME" ~/.local/share/icons/hicolor/256x256/apps/${DESKTOP_NAME}.png
fi

# Create the Desktop Entry
echo "Creating menu shortcut..."
cat > ~/.local/share/applications/${DESKTOP_NAME}.desktop <<EOL
[Desktop Entry]
Version=1.0
Type=Application
Name=Oi360 PDF Suite
GenericName=PDF Manager
Comment=Premium PDF Splitter and Merger - Powered by GRACE
Exec=$HOME/.local/bin/$APP_NAME
Icon=${DESKTOP_NAME}
Terminal=false
Categories=Office;Utility;PDF;
Keywords=pdf;split;merge;document;
StartupNotify=true
EOL

# Refresh icon cache and desktop database
echo "Refreshing system..."
gtk-update-icon-cache ~/.local/share/icons/hicolor 2>/dev/null || true
update-desktop-database ~/.local/share/applications 2>/dev/null || true

echo ""
echo "========================================="
echo "  Installation Complete!"
echo "========================================="
echo ""
echo "You can now:"
echo "  1. Search for 'Oi360' in your application menu"
echo "  2. Or run from terminal: ~/.local/bin/$APP_NAME"
echo ""
echo "To uninstall, run: ./uninstall.sh"
