#!/usr/bin/env python3
"""Hardware discovery and persistent device-selection screens for SpectrumSnek."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

from textual.app import ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Input, Static

from spectrum_core import ROOT

CONFIG_PATH = ROOT / "hardware_config.json"
CATEGORIES = {
    "wifi": "Wi-Fi",
    "bluetooth": "Bluetooth",
    "sdr": "SDR",
    "gps": "GPS",
}


def load_config() -> dict[str, Any]:
    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def save_config(config: dict[str, Any]) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    temp = CONFIG_PATH.with_suffix(".json.tmp")
    temp.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    os.replace(temp, CONFIG_PATH)


def discover(category: str) -> list[dict[str, str]]:
    """Find hardware using Linux sysfs and standard command-line tools."""
    devices: list[dict[str, str]] = []
    if category == "wifi":
        for path in sorted(Path("/sys/class/net").glob("*")):
            if (path / "wireless").exists():
                devices.append({"id": path.name, "label": f"{path.name} (Wi-Fi interface)"})
        if not devices and shutil.which("iw"):
            try:
                out = subprocess.run(["iw", "dev"], capture_output=True, text=True,
                                     timeout=3, check=False).stdout
                for name in re.findall(r"Interface\s+(\S+)", out):
                    devices.append({"id": name, "label": f"{name} (Wi-Fi interface)"})
            except (OSError, subprocess.TimeoutExpired):
                pass
    elif category == "bluetooth":
        for path in sorted(Path("/sys/class/bluetooth").glob("hci*")):
            devices.append({"id": path.name, "label": f"{path.name} (Bluetooth controller)"})
        if not devices and shutil.which("bluetoothctl"):
            try:
                out = subprocess.run(["bluetoothctl", "list"], capture_output=True,
                                     text=True, timeout=3, check=False).stdout
                for line in out.splitlines():
                    if line.startswith("Controller "):
                        parts = line.split(maxsplit=2)
                        if len(parts) >= 3:
                            devices.append({"id": parts[1], "label": f"{parts[2]} ({parts[1]})"})
            except (OSError, subprocess.TimeoutExpired):
                pass
    elif category == "sdr":
        usb_ids = {
            "0bda:2831", "0bda:2832", "0bda:2838", "0bda:0129",
            "1d19:1101", "1f4d:b803", "1f4d:c803", "0458:001a",
            "185b:0620", "0ccd:00a9", "0ccd:00b3", "0ccd:00d3",
        }
        if shutil.which("lsusb"):
            try:
                out = subprocess.run(["lsusb"], capture_output=True, text=True,
                                     timeout=3, check=False).stdout
                for line in out.splitlines():
                    match = re.search(r"ID\s+([0-9a-fA-F]{4}:[0-9a-fA-F]{4})", line)
                    if match and match.group(1).lower() in usb_ids:
                        devices.append({"id": match.group(1).lower(), "label": line.strip()})
            except (OSError, subprocess.TimeoutExpired):
                pass
    elif category == "gps":
        seen: set[str] = set()
        for pattern in ("/dev/ttyUSB*", "/dev/ttyACM*", "/dev/ttyAMA*", "/dev/serial/by-id/*"):
            for path in sorted(Path("/").glob(pattern.lstrip("/"))):
                device_id = str(path)
                if device_id not in seen and path.exists():
                    seen.add(device_id)
                    devices.append({"id": device_id, "label": f"{device_id} (serial GPS candidate)"})
        if shutil.which("gpspipe") and shutil.which("gpsd"):
            devices.append({"id": "gpsd:localhost:2947", "label": "gpsd on localhost:2947"})
    return devices


class ConfigureScreen(Screen):
    """Top-level Configure submenu."""

    BINDINGS = [("escape", "go_back", "Back")]

    def compose(self) -> ComposeResult:
        yield Static("Configure", classes="menu-title")
        with VerticalScroll(id="content"):
            with Horizontal(classes="tool-row"):
                yield Button("Hardware selection", id="configure-hardware", variant="primary")
                yield Button("Web service", id="configure-service", variant="primary")
            with Horizontal(classes="tool-row"):
                yield Button("Back", id="configure-back", variant="default")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "configure-hardware":
            self.app.push_screen(HardwareScreen())
        elif event.button.id == "configure-service":
            # Import at click time to avoid a circular import with textual_menu.
            from textual_menu import ServiceScreen
            self.app.push_screen(ServiceScreen())
        elif event.button.id == "configure-back":
            self.app.pop_screen()

    def action_go_back(self) -> None:
        self.app.pop_screen()


class HardwareScreen(Screen):
    BINDINGS = [("escape", "go_back", "Back")]

    def compose(self) -> ComposeResult:
        yield Static("Hardware selection", classes="menu-title")
        config = load_config()
        for category, label in CATEGORIES.items():
            found = discover(category)
            enabled = config.get("devices", {}).get(category, {})
            active = sum(1 for item in found if enabled.get(item["id"], True))
            yield Static(f"{label}: {len(found)} detected, {active} enabled")
            yield Button(f"{label} devices...", id=f"hardware-{category}", variant="primary")
        yield Button("Back", id="hardware-back", variant="default")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id or ""
        if button_id == "hardware-back":
            self.app.pop_screen()
        elif button_id.startswith("hardware-"):
            category = button_id.removeprefix("hardware-")
            if category in CATEGORIES:
                self.app.push_screen(DeviceScreen(category))

    def action_go_back(self) -> None:
        self.app.pop_screen()


class DeviceScreen(Screen):
    BINDINGS = [("escape", "go_back", "Back")]

    def __init__(self, category: str) -> None:
        super().__init__()
        self.category = category
        self.devices: list[dict[str, str]] = []

    def compose(self) -> ComposeResult:
        yield Static(f"{CATEGORIES[self.category]} devices", classes="menu-title")
        self.devices = discover(self.category)
        config = load_config()
        selected = config.setdefault("devices", {}).setdefault(self.category, {})
        if not self.devices:
            yield Static("No devices detected.")
        for index, device in enumerate(self.devices):
            enabled = selected.get(device["id"], True)
            state = "ON" if enabled else "OFF"
            yield Button(f"[{state}] {device['label']}", id=f"device-toggle-{index}",
                         variant="success" if enabled else "default")
        if self.category == "gps":
            gps = config.setdefault("gps", {})
            yield Static("Network GPS source (NMEA over TCP, e.g. gpsd):")
            yield Input(value=str(gps.get("host", "")), placeholder="Hostname or IP address",
                        id="gps-host")
            yield Input(value=str(gps.get("port", 2947)), placeholder="TCP port",
                        id="gps-port")
            yield Button("Save network GPS source", id="gps-save", variant="primary")
            yield Static(f"Network GPS: {'enabled' if gps.get('enabled', False) else 'disabled'}",
                         id="gps-network-status")
            yield Button("Toggle network GPS", id="gps-network-toggle", variant="primary")
        yield Button("Refresh devices", id="device-refresh", variant="primary")
        yield Button("Back", id="device-back", variant="default")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id or ""
        if button_id == "device-back":
            self.app.pop_screen()
            return
        if button_id == "device-refresh":
            self.refresh()
            return
        config = load_config()
        if button_id.startswith("device-toggle-"):
            index = int(button_id.rsplit("-", 1)[1])
            if index >= len(self.devices):
                self.refresh()
                return
            device = self.devices[index]
            selected = config.setdefault("devices", {}).setdefault(self.category, {})
            selected[device["id"]] = not selected.get(device["id"], True)
            save_config(config)
            self.refresh()
        elif button_id == "gps-save":
            host = self.query_one("#gps-host", Input).value.strip()
            port_text = self.query_one("#gps-port", Input).value.strip()
            if not host or not port_text.isdigit() or not 1 <= int(port_text) <= 65535:
                self.app.notify("Enter a host and a valid TCP port (1-65535).", severity="warning")
                return
            gps = config.setdefault("gps", {})
            gps.update({"host": host, "port": int(port_text)})
            save_config(config)
            self.app.notify("Network GPS source saved.")
        elif button_id == "gps-network-toggle":
            gps = config.setdefault("gps", {})
            if not gps.get("host") or not gps.get("port"):
                self.app.notify("Save a network GPS host and port first.", severity="warning")
                return
            gps["enabled"] = not gps.get("enabled", False)
            save_config(config)
            self.refresh()

    def refresh(self) -> None:
        self.app.pop_screen()
        self.app.push_screen(DeviceScreen(self.category))

    def action_go_back(self) -> None:
        self.app.pop_screen()
