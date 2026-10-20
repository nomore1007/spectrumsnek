#!/usr/bin/env python3
"""Experimental Textual terminal interface for SpectrumSnek.

Run with: ./venv/bin/python textual_menu.py
The existing Whiptail launcher remains available while this interface is tested.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Grid, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Static

from spectrum_core import ROOT, device_status, tool_catalog



class UtilitiesScreen(Screen):
    """Compact Utilities submenu."""

    BINDINGS = [("escape", "go_back", "Back")]

    def compose(self) -> ComposeResult:
        yield Static("Utilities", classes="menu-title")
        with Grid(id="tool-grid"):
            yield Button("plugins", id="utility-plugins", variant="primary")
            yield Button("configure", id="utility-configure", variant="primary")
            yield Button("update", id="utility-update", variant="primary")
            yield Button("back", id="utility-back", variant="default")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id or ""
        if button_id == "utility-back":
            self.app.pop_screen()
        elif button_id == "utility-plugins":
            result = subprocess.run(
                ["bash", str(ROOT / "plugin_manager.sh"), "list"],
                cwd=ROOT, capture_output=True, text=True, check=False
            )
            output = result.stdout.strip() or result.stderr.strip() or "No plugin status returned."
            self.app.push_screen(MessageScreen("Installed Plugins", output))
        elif button_id == "utility-configure":
            self.app.push_screen(ServiceScreen())
        elif button_id == "utility-update":
            branch_result = subprocess.run(
                ["git", "-C", str(ROOT), "branch", "--show-current"],
                capture_output=True, text=True, check=False
            )
            branch = branch_result.stdout.strip()
            if branch_result.returncode or not branch:
                self.app.notify("Could not determine the current Git branch.", severity="error")
                return
            self.run_command(["git", "-C", str(ROOT), "pull", "--ff-only", "origin", branch], "Update")

    def run_command(self, command: list[str], label: str) -> None:
        try:
            with self.app.suspend():
                result = subprocess.run(command, cwd=ROOT, check=False)
            self.app.notify(f"{label} finished (exit {result.returncode})",
                            severity="warning" if result.returncode else "information")
        except OSError as exc:
            self.app.notify(f"{label} failed: {exc}", severity="error")

    def action_go_back(self) -> None:
        self.app.pop_screen()


class ServiceScreen(Screen):
    """Service controls under Utilities -> Configure."""

    BINDINGS = [("escape", "go_back", "Back")]

    def compose(self) -> ComposeResult:
        yield Static("Configure Web Service", classes="menu-title")
        with Grid(id="tool-grid"):
            for action in ("setup", "start", "stop", "restart", "status", "logs"):
                yield Button(action, id=f"service-{action}", variant="primary")
            yield Button("back", id="service-back", variant="default")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id or ""
        if button_id == "service-back":
            self.app.pop_screen()
            return
        if not button_id.startswith("service-"):
            return
        action = button_id.removeprefix("service-")
        script = ROOT / ("setup_service.sh" if action == "setup" else "service_manager.sh")
        command = ["bash", str(script)] if action == "setup" else ["bash", str(script), action]
        try:
            with self.app.suspend():
                result = subprocess.run(command, cwd=ROOT, check=False)
            self.app.notify(f"Service {action}: exit {result.returncode}",
                            severity="warning" if result.returncode else "information")
        except OSError as exc:
            self.app.notify(f"Service {action} failed: {exc}", severity="error")

    def action_go_back(self) -> None:
        self.app.pop_screen()


class MessageScreen(Screen):
    BINDINGS = [("escape", "go_back", "Back")]

    def __init__(self, title: str, message: str) -> None:
        super().__init__()
        self.message_title = title
        self.message = message

    def compose(self) -> ComposeResult:
        yield Static(self.message_title, classes="menu-title")
        yield Static(self.message)
        yield Button("back", id="message-back", variant="default")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "message-back":
            self.app.pop_screen()

    def action_go_back(self) -> None:
        self.app.pop_screen()


class SpectrumSnekApp(App):
    TITLE = "SpectrumSnek"
    SUB_TITLE = "Radio and SDR toolkit"
    CSS = """
    Screen { background: #101820; color: #edf2f4; }
    Header { height: 1; }
    #banner { height: 1; padding: 0 1; background: #172a3a; color: #f4f7f8; }
    #devices { height: 1; padding: 0 1; background: #203746; }
    #content { height: 1fr; padding: 0 1; }
    #tool-grid { grid-size: 2; grid-columns: 1fr 1fr; grid-gutter: 0 1; }
    Button { width: 100%; min-width: 1; min-height: 3; height: 3; margin: 0; padding: 0 1; }
    #footer-note { height: 1; padding: 0 1; color: #a9bac6; }
    .menu-title { height: 1; padding: 0 1; background: #172a3a; }
    """

    BINDINGS = [
        ("r", "refresh_status", "Refresh hardware"),
        ("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("SpectrumSnek", id="banner")
        yield Static(id="devices")
        with VerticalScroll(id="content"):
            with Grid(id="tool-grid"):
                for tool in tool_catalog():
                    yield Button(tool["id"], id=f"launch-{tool['id']}", variant="primary")
                yield Button("utilities", id="open-utilities", variant="default")
        yield Static("↑↓ navigate  Enter select  q quit  r refresh", id="footer-note")
        yield Footer()

    def on_mount(self) -> None:
        self.action_refresh_status()

    def action_refresh_status(self) -> None:
        status = device_status()
        labels = [
            ("RTL-SDR", status["rtl_sdr"]),
            ("Wi-Fi", status["wifi"]),
            ("Bluetooth", status["bluetooth"]),
        ]
        display = "  ".join(
            f"{'●' if present else '○'} {name}"
            for name, present in labels
        )
        self.query_one("#devices", Static).update(display)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "open-utilities":
            self.push_screen(UtilitiesScreen())
            return
        if not event.button.id or not event.button.id.startswith("launch-"):
            return
        tool_id = event.button.id.removeprefix("launch-")
        tool = next((item for item in tool_catalog() if item["id"] == tool_id), None)
        if tool is None:
            self.notify(f"Tool not found: {tool_id}", severity="error")
            return

        # Give the child process the terminal while existing tools run. This lets
        # legacy terminal tools continue to work during the UI transition.
        try:
            with self.suspend():
                result = subprocess.run(
                    tool["command"],
                    cwd=ROOT,
                    env={**os.environ, "PYTHONPATH": str(ROOT)},
                    check=False,
                )
            if result.returncode:
                self.notify(f"{tool['name']} exited with status {result.returncode}", severity="warning")
        except OSError as exc:
            self.notify(f"Could not launch {tool['name']}: {exc}", severity="error")
        self.action_refresh_status()

    def action_quit(self) -> None:
        self.exit()


def main() -> int:
    try:
        SpectrumSnekApp().run()
    except KeyboardInterrupt:
        return 130
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
