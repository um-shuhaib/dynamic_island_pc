# Dynamic Island for Desktop (Windows & Linux) 🏝️

An ultra-sleek, hardware-accelerated **iPhone Dynamic Island** overlay for Windows and Linux built with Python & PyQt6.

Features real-time squircle morphing animations, digital clock & date, zero-click hover expand, mouse-wheel tab cycling, media controls, hardware monitoring, Pomodoro focus timer, clipboard history, and an interactive **Visual Calibration Wizard** for screen alignment.

---

## 🚀 Quick Install on Any Device

### 🪟 Windows (1-Click Install)
1. Open Command Prompt or PowerShell:
   ```cmd
   git clone <YOUR_GIT_REPO_URL>
   cd <REPO_NAME>
   install.bat
   ```
2. **What this does:**
   - Automatically installs required dependencies (`PyQt6`, `psutil`).
   - Creates a **Desktop shortcut** and **Start Menu** entry.
   - Registers in Windows **Settings → Installed Apps / Add or remove programs**.
   - Launches the Dynamic Island immediately.

#### How to Uninstall on Windows
- Go to **Windows Settings → Apps → Installed Apps → Dynamic Island → Uninstall**.
- *OR* double-click `uninstall.bat` in the repository or Start Menu.

---

### 🐧 Ubuntu / Debian Linux (1-Click Install)
1. Open Terminal:
   ```bash
   git clone <YOUR_GIT_REPO_URL>
   cd <REPO_NAME>
   chmod +x install.sh
   ./install.sh
   ```
2. **What this does:**
   - Installs system packages (`python3-pyqt6`, `python3-psutil`).
   - Creates `~/.local/bin/dynamic-island` executable.
   - Installs desktop icon and shortcut in the Ubuntu Application Grid.
   - Configures automatic startup on boot.

#### How to Uninstall on Ubuntu
```bash
chmod +x uninstall.sh
./uninstall.sh
```

---

## 🎮 How to Interact

| Action | Result |
| :--- | :--- |
| **Hover Over Island** | Automatically expands into full drawer with tabs (zero clicks needed) |
| **Move Cursor Away** | Automatically collapses back to small date & time pill |
| **Scroll Mouse Wheel / Trackpad** | Seamlessly cycles through tabs (**Clock ➔ Media ➔ System ➔ Focus ➔ History**) |
| **Right Click on Island** | Opens quick context menu (Settings, Minimize, Exit) |
| **Left Click System Tray** | Toggles island visibility |

---

## 🛠️ Building Standalone Binaries

### Build Windows `.exe` (No Python Needed for End Users)
```cmd
build_exe.bat
```
The output executable will be generated at `dist/DynamicIsland/DynamicIsland.exe`.

### Build Ubuntu `.deb` Package
```bash
python build_deb.py
```
The output Debian package will be generated at `dist/dynamic-island_1.0.0_all.deb`.

---

## 📁 Repository Structure

```
├── dynamic_island/
│   ├── main.py                  # Entry point & CLI arguments
│   ├── config.py                # Resilient JSON configuration manager
│   ├── ui/
│   │   ├── island_window.py     # Translucent frameless pill & hover/scroll engine
│   │   ├── calibration_wizard.py# Interactive visual calibration wizard
│   │   ├── tray_icon.py         # System tray icon & context menu
│   │   └── widgets/
│   │       ├── pill_base.py     # Anti-aliased OLED squircle renderer
│   │       ├── clock_view.py    # Digital clock, full calendar date & weekdays
│   │       ├── media_view.py    # Animated sound bars & expanded playback controls
│   │       ├── system_view.py   # CPU, RAM, Battery, and Net traffic gauges
│   │       ├── pomodoro_view.py # Focus/break timer with alerts
│   │       ├── clipboard_view.py# Clipboard history stack
│   │       └── alert_banner.py  # Morphing event banner
│   └── core/
│       ├── media/               # Windows WinRT & Linux MPRIS2 media controllers
│       ├── system_monitor.py    # psutil background thread
│       ├── clipboard_manager.py # QClipboard listener
│       ├── fullscreen.py        # Active fullscreen window detector
│       └── autostart.py         # Windows Registry & Linux desktop auto-start
├── packaging/                   # Packaging scripts for Windows and Ubuntu
├── build_deb.py                 # Debian .deb package generator
├── build_exe.bat                # Windows PyInstaller generator
├── install.bat                  # 1-Click Windows installer & uninstaller registrar
├── uninstall.bat                # 1-Click Windows uninstaller
├── install.sh                   # 1-Click Ubuntu/Linux installer
├── uninstall.sh                 # 1-Click Ubuntu/Linux uninstaller
├── run.py                       # Python launcher
└── requirements.txt             # Dependencies
```
