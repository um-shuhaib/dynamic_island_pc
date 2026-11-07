#!/usr/bin/env bash
# Dynamic Island Uninstaller for Ubuntu / Debian Linux
set -e

echo "=============================================="
echo "  Dynamic Island for Ubuntu - Uninstallation"
echo "=============================================="

echo "[1/3] Closing running instances..."
pkill -f "dynamic-island" 2>/dev/null || true
pkill -f "dynamic_island/main.py" 2>/dev/null || true

echo "[2/3] Removing installed files..."
rm -rf "$HOME/.local/share/dynamic-island"
rm -f "$HOME/.local/bin/dynamic-island"
rm -f "$HOME/.local/share/applications/dynamic-island.desktop"
rm -f "$HOME/.config/autostart/dynamic-island.desktop"
rm -f "$HOME/.local/share/icons/hicolor/scalable/apps/dynamic-island.svg"
rm -rf "$HOME/.config/dynamic_island"

echo "[3/3] Updating system caches..."
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true
fi
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -f "$HOME/.local/share/icons/hicolor" 2>/dev/null || true
fi

echo "=============================================="
echo "  Dynamic Island has been successfully"
echo "  uninstalled from your Ubuntu system."
echo "=============================================="
