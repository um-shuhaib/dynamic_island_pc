#!/usr/bin/env bash
# Dynamic Island Installer for Ubuntu / Linux
set -e

echo "=============================================="
echo "  Dynamic Island for Linux - Installation"
echo "=============================================="

# 1. Install dependencies
echo "[1/4] Checking dependencies (PyQt6 & psutil)..."
if command -v apt-get >/dev/null 2>&1; then
    MISSING=""
    if ! python3 -c "import PyQt6" >/dev/null 2>&1; then MISSING="$MISSING python3-pyqt6"; fi
    if ! python3 -c "import psutil" >/dev/null 2>&1; then MISSING="$MISSING python3-psutil"; fi
    if [ -n "$MISSING" ]; then
        echo "Installing system packages: $MISSING..."
        sudo apt-get update -qq && sudo apt-get install -y $MISSING
    fi
else
    pip3 install -r requirements.txt --quiet || pip install -r requirements.txt --quiet
fi

# 2. Target directories
INSTALL_DIR="$HOME/.local/share/dynamic-island"
BIN_DIR="$HOME/.local/bin"
DESKTOP_DIR="$HOME/.local/share/applications"
AUTOSTART_DIR="$HOME/.config/autostart"
ICON_DIR="$HOME/.local/share/icons/hicolor/scalable/apps"

echo "[2/4] Copying files to $INSTALL_DIR..."
mkdir -p "$INSTALL_DIR" "$BIN_DIR" "$DESKTOP_DIR" "$AUTOSTART_DIR" "$ICON_DIR"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp -r "$SCRIPT_DIR/dynamic_island" "$INSTALL_DIR/"
cp "$SCRIPT_DIR/run.py" "$INSTALL_DIR/"
cp "$SCRIPT_DIR/requirements.txt" "$INSTALL_DIR/"

# 3. Create launcher script
echo "[3/4] Creating launcher command..."
cat << 'EOF' > "$BIN_DIR/dynamic-island"
#!/usr/bin/env bash
export QT_QPA_PLATFORM=xcb
exec python3 "$HOME/.local/share/dynamic-island/run.py" "$@"
EOF
chmod +x "$BIN_DIR/dynamic-island"

# Icon
cat << 'EOF' > "$ICON_DIR/dynamic-island.svg"
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128" width="128" height="128">
  <rect x="8" y="32" width="112" height="64" rx="32" ry="32" fill="#000000" stroke="#333333" stroke-width="3"/>
  <circle cx="36" cy="64" r="12" fill="#0A84FF"/>
  <rect x="58" y="58" width="46" height="12" rx="6" ry="6" fill="#FFFFFF" opacity="0.85"/>
</svg>
EOF

# 4. Desktop entry
echo "[4/4] Creating application shortcuts..."
cat << EOF > "$DESKTOP_DIR/dynamic-island.desktop"
[Desktop Entry]
Version=1.0
Type=Application
Name=Dynamic Island
Comment=iPhone Dynamic Island Desktop Overlay
Exec=$BIN_DIR/dynamic-island
Icon=dynamic-island
Terminal=false
Categories=Utility;DesktopUtility;
StartupNotify=false
X-GNOME-Autostart-enabled=true
EOF
chmod +x "$DESKTOP_DIR/dynamic-island.desktop"
cp "$DESKTOP_DIR/dynamic-island.desktop" "$AUTOSTART_DIR/"

if command -v update-desktop-database >/dev/null 2>&1; then update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true; fi
if command -v gtk-update-icon-cache >/dev/null 2>&1; then gtk-update-icon-cache -f "$HOME/.local/share/icons/hicolor" 2>/dev/null || true; fi

echo "=============================================="
echo "  Installation Complete!"
echo "  Launch anytime by running: dynamic-island"
echo "  or find 'Dynamic Island' in your App menu."
echo "=============================================="
