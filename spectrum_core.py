#!/usr/bin/env python3
"""Shared discovery and hardware-status helpers for SpectrumSnek interfaces."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
PLUGINS_DIR = ROOT / "plugins"
BUILTIN_PLUGINS = {"rtl_scanner", "radio_scanner", "system_tools", "__pycache__"}

RTL_USB_IDS = {
    "0bda:2831", "0bda:2832", "0bda:2838", "0bda:0129",
    "1d19:1101", "1f4d:b803", "1f4d:c803", "0458:001a",
    "185b:0620", "0ccd:00a9", "0ccd:00b3", "0ccd:00d3",
}


def device_status() -> dict[str, bool]:
    """Return best-effort hardware availability without opening devices."""
    return {
        "rtl_sdr": _rtl_sdr_detected(),
        "wifi": _wifi_detected(),
        "bluetooth": _bluetooth_detected(),
    }


def _rtl_sdr_detected() -> bool:
    import shutil
    import subprocess

    lsusb = shutil.which("lsusb")
    if not lsusb:
        return False
    try:
        output = subprocess.run(
            [lsusb], capture_output=True, text=True, timeout=2, check=False
        ).stdout.lower()
        return any(device_id in output for device_id in RTL_USB_IDS)
    except (OSError, subprocess.TimeoutExpired):
        return False


def _wifi_detected() -> bool:
    for interface in Path("/sys/class/net").glob("*"):
        if (interface / "wireless").exists():
            return True
    try:
        import shutil
        import subprocess

        iw = shutil.which("iw")
        if iw:
            result = subprocess.run(
                [iw, "dev"], capture_output=True, text=True, timeout=2, check=False
            )
            return "Interface " in result.stdout
    except (OSError, subprocess.TimeoutExpired):
        pass
    return False


def _bluetooth_detected() -> bool:
    if any(Path("/sys/class/bluetooth").glob("hci*")):
        return True
    try:
        import shutil
        import subprocess

        bluetoothctl = shutil.which("bluetoothctl")
        if bluetoothctl:
            result = subprocess.run(
                [bluetoothctl, "list"], capture_output=True, text=True,
                timeout=2, check=False
            )
            return "Controller " in result.stdout
    except (OSError, subprocess.TimeoutExpired):
        pass
    return False


def discover_plugins() -> list[dict[str, Any]]:
    """Discover installed plugins implementing get_module_info() and run()."""
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    discovered = []
    if not PLUGINS_DIR.is_dir():
        return discovered

    for path in sorted(PLUGINS_DIR.iterdir(), key=lambda item: item.name.casefold()):
        if (
            not path.is_dir()
            or path.name.startswith("_")
            or path.name in BUILTIN_PLUGINS
            or not (path / "__init__.py").is_file()
        ):
            continue
        try:
            module = importlib.import_module(f"plugins.{path.name}")
            get_info = getattr(module, "get_module_info", None)
            info = get_info() if callable(get_info) else getattr(module, "MODULE_INFO", {})
            if not isinstance(info, dict) or not callable(getattr(module, "run", None)):
                continue
            discovered.append({
                "id": path.name,
                "name": str(info.get("name") or path.name.replace("_", " ").title()),
                "description": str(info.get("description") or "Installed plugin"),
                "version": str(info.get("version") or "unknown"),
                "author": str(info.get("author") or "Unknown"),
            })
        except Exception as exc:
            print(f"SpectrumSnek: skipping plugin {path.name}: {exc}", file=sys.stderr)
    return discovered


def tool_catalog() -> list[dict[str, Any]]:
    """Describe the built-in tools and discovered third-party plugins."""
    tools = [
        {
            "id": "rtl_scanner",
            "name": "RTL-SDR Scanner",
            "description": "Inspect radio spectrum and listen to supported signals.",
            "command": [sys.executable, str(ROOT / "plugins/rtl_scanner/scanner.py")],
        },
        {
            "id": "radio_scanner",
            "name": "Traditional Radio Scanner",
            "description": "Scan configured radio frequency banks.",
            "command": [sys.executable, str(ROOT / "plugins/radio_scanner/scanner.py")],
        },
        {
            "id": "system_tools",
            "name": "System Tools",
            "description": "Wi-Fi, Bluetooth, audio, and system utilities.",
            "command": [sys.executable, str(ROOT / "plugins/system_tools/system_menu.py")],
        },
    ]
    for plugin in discover_plugins():
        tools.append({
            **plugin,
            "command": [sys.executable, str(ROOT / "plugin_menu.py"), "--run", plugin["id"]],
        })
    return tools
