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
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Button, Footer, Header, Label, Static

from spectrum_core import ROOT, device_status, tool_catalog


class SpectrumSnekApp(App):
    TITLE = "SpectrumSnek"
    SUB_TITLE = "Radio and SDR toolkit"
    CSS = """
    Screen { background: #101820; color: #edf2f4; }
    Header { height: 1; }
    #banner { height: 1; padding: 0 1; background: #172a3a; color: #f4f7f8; }
    #devices { height: 1; padding: 0 1; background: #203746; }
    #content { height: 1fr; padding: 0 1; }
    .tool-row { height: 3; margin: 0; padding: 0; }
    Button { width: 100%; min-width: 1; min-height: 3; margin: 0; padding: 0 1; }
    #footer-note { height: 1; padding: 0 1; color: #a9bac6; }
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
            for tool in tool_catalog():
                with Horizontal(classes="tool-row"):
                    # Show the actual tool identifier on the button instead of
                    # wasting scarce screen space on a generic "Launch" label.
                    yield Button(tool["id"], id=f"launch-{tool['id']}", variant="primary")
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
        display = "Hardware:  " + "   ".join(
            f"{'●' if present else '○'} {name} {'available' if present else 'not detected'}"
            for name, present in labels
        )
        self.query_one("#devices", Static).update(display)

    def on_button_pressed(self, event: Button.Pressed) -> None:
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
