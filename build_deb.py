"""Cross-platform script to build a native Debian/Ubuntu .deb package without dpkg-deb."""
import os
import io
import time
import tarfile
import struct
from pathlib import Path

VERSION = "1.0.0"
PACKAGE_NAME = "dynamic-island"

SVG_ICON = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128" width="128" height="128">
  <rect x="8" y="32" width="112" height="64" rx="32" ry="32" fill="#000000" stroke="#333333" stroke-width="3"/>
  <circle cx="36" cy="64" r="12" fill="#0A84FF"/>
  <rect x="58" y="58" width="46" height="12" rx="6" ry="6" fill="#FFFFFF" opacity="0.85"/>
</svg>"""

DESKTOP_ENTRY = """[Desktop Entry]
Version=1.0
Type=Application
Name=Dynamic Island
Comment=iPhone Dynamic Island Desktop Overlay
Exec=/usr/bin/dynamic-island
Icon=dynamic-island
Terminal=false
Categories=Utility;DesktopUtility;
StartupNotify=false
X-GNOME-Autostart-enabled=true
"""

LAUNCHER_SCRIPT = """#!/bin/bash
export QT_QPA_PLATFORM=xcb
exec python3 /usr/share/dynamic-island/run.py "$@"
"""

CONTROL_FILE = f"""Package: {PACKAGE_NAME}
Version: {VERSION}
Section: utils
Priority: optional
Architecture: all
Depends: python3, python3-pyqt6, python3-psutil
Maintainer: Dynamic Island Developers
Description: iPhone Dynamic Island Desktop Overlay for Ubuntu
 A hardware-accelerated Dynamic Island desktop widget for Ubuntu Linux.
 Features real-time squircle morphing animations, media player controls,
 CPU/RAM/battery monitoring, Pomodoro focus timer, and clipboard history.
"""

POSTINST_SCRIPT = """#!/bin/sh
set -e
chmod +x /usr/bin/dynamic-island
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -f /usr/share/icons/hicolor 2>/dev/null || true
fi
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database 2>/dev/null || true
fi
exit 0
"""

POSTRM_SCRIPT = """#!/bin/sh
set -e
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -f /usr/share/icons/hicolor 2>/dev/null || true
fi
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database 2>/dev/null || true
fi
exit 0
"""


def create_tar_gz(files_dict: dict) -> bytes:
    """Create a .tar.gz in memory from a dict of {tar_path: (content_bytes, mode)}."""
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        for arcname, (data, mode) in files_dict.items():
            ti = tarfile.TarInfo(name=arcname)
            ti.size = len(data)
            ti.mtime = int(time.time())
            ti.mode = mode
            ti.type = tarfile.REGTYPE
            tar.addfile(ti, io.BytesIO(data))
    return buf.getvalue()


def create_ar_archive(members: list[tuple[str, bytes]]) -> bytes:
    """Pack files into standard Debian 'ar' format."""
    out = io.BytesIO()
    out.write(b"!<arch>\n")
    for filename, data in members:
        # AR header: 16 bytes name, 12 mtime, 6 uid, 6 gid, 8 mode, 10 size, 2 magic
        name_field = f"{filename:<16}".encode("ascii")
        mtime_field = f"{int(time.time()):<12}".encode("ascii")
        uid_field = b"0     "
        gid_field = b"0     "
        mode_field = b"100644  "
        size_field = f"{len(data):<10}".encode("ascii")
        magic = b"`\n"

        header = name_field + mtime_field + uid_field + gid_field + mode_field + size_field + magic
        out.write(header)
        out.write(data)
        if len(data) % 2 != 0:
            out.write(b"\n")
    return out.getvalue()


def build_deb(output_dir: Path):
    root_dir = Path(__file__).resolve().parent

    # 1. Control archive
    control_files = {
        "./control": (CONTROL_FILE.encode("utf-8"), 0o644),
        "./postinst": (POSTINST_SCRIPT.encode("utf-8"), 0o755),
        "./postrm": (POSTRM_SCRIPT.encode("utf-8"), 0o755),
    }
    control_tar_gz = create_tar_gz(control_files)

    # 2. Data archive
    data_files = {
        "./usr/bin/dynamic-island": (LAUNCHER_SCRIPT.encode("utf-8"), 0o755),
        "./usr/share/applications/dynamic-island.desktop": (DESKTOP_ENTRY.encode("utf-8"), 0o644),
        "./usr/share/icons/hicolor/scalable/apps/dynamic-island.svg": (SVG_ICON.encode("utf-8"), 0o644),
    }

    # Add source code files into /usr/share/dynamic-island/
    for py_file in (root_dir / "dynamic_island").rglob("*.py"):
        rel = py_file.relative_to(root_dir)
        data_files[f"./usr/share/dynamic-island/{rel.as_posix()}"] = (py_file.read_bytes(), 0o644)

    run_py = root_dir / "run.py"
    data_files["./usr/share/dynamic-island/run.py"] = (run_py.read_bytes(), 0o755)

    data_tar_gz = create_tar_gz(data_files)

    # 3. Assemble .deb archive (ar container: debian-binary, control.tar.gz, data.tar.gz)
    ar_members = [
        ("debian-binary", b"2.0\n"),
        ("control.tar.gz", control_tar_gz),
        ("data.tar.gz", data_tar_gz),
    ]

    deb_bytes = create_ar_archive(ar_members)

    output_dir.mkdir(parents=True, exist_ok=True)
    deb_path = output_dir / f"{PACKAGE_NAME}_{VERSION}_all.deb"
    deb_path.write_bytes(deb_bytes)
    print(f"[Ubuntu Package] Successfully generated: {deb_path} ({len(deb_bytes)} bytes)")
    return deb_path


if __name__ == "__main__":
    out_dir = Path(__file__).resolve().parent / "dist"
    build_deb(out_dir)
