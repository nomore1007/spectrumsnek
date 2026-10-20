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
from textual.containers import Horizontal, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Input, Select, Static

from spectrum_core import ROOT, device_status, tool_catalog


class UtilitiesScreen(Screen):
    """Compact Utilities submenu."""

    BINDINGS = [("escape", "go_back", "Back")]

    def compose(self) -> ComposeResult:
        yield Static("Utilities", classes="menu-title")
        with VerticalScroll(id="content"):
            with Horizontal(classes="tool-row"):
                yield Button("plugins", id="utility-plugins", variant="primary")
                yield Button("configure", id="utility-configure", variant="primary")
            with Horizontal(classes="tool-row"):
                yield Button("update", id="utility-update", variant="primary")
                yield Button("back", id="utility-back", variant="default")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id or ""
        if button_id == "utility-back":
            self.app.pop_screen()
        elif button_id == "utility-plugins":
            self.app.push_screen(PluginScreen())
        elif button_id == "utility-configure":
            self.app.push_screen(ServiceScreen())
        elif button_id == "utility-update":
            self.app.push_screen(AppUpdateScreen())

    def action_go_back(self) -> None:
        self.app.pop_screen()


def remote_branches(url: str) -> list[str]:
    """Return branch names published by a remote Git repository."""
    try:
        result = subprocess.run(
            ["git", "ls-remote", "--heads", url],
            cwd=ROOT, capture_output=True, text=True, check=False, timeout=20,
        )
    except (OSError, subprocess.TimeoutExpired):
        return []
    if result.returncode:
        return []
    branches = []
    for line in result.stdout.splitlines():
        fields = line.split()
        if len(fields) == 2 and fields[1].startswith("refs/heads/"):
            branches.append(fields[1][len("refs/heads/"):])
    return sorted(set(branches))


class AppUpdateScreen(Screen):
    """Select the branch used to update the main SpectrumSnek checkout."""

    BINDINGS = [("escape", "go_back", "Back")]

    def compose(self) -> ComposeResult:
        current = subprocess.run(
            ["git", "-C", str(ROOT), "branch", "--show-current"],
            capture_output=True, text=True, check=False,
        ).stdout.strip()
        remote = subprocess.run(
            ["git", "-C", str(ROOT), "remote", "get-url", "origin"],
            capture_output=True, text=True, check=False,
        ).stdout.strip()
        branches = remote_branches(remote) if remote else []
        if current and current not in branches:
            branches.insert(0, current)
        if not branches:
            branches = [current or "master"]
        selected = current if current in branches else branches[0]
        yield Static("Update SpectrumSnek", classes="menu-title")
        yield Static("Choose the branch to switch to and update from origin.")
        yield Select([(branch, branch) for branch in branches], value=selected,
                     id="app-update-branch", allow_blank=False)
        with Horizontal(classes="tool-row"):
            yield Button("Update selected branch", id="app-update-run", variant="primary")
            yield Button("Cancel", id="app-update-cancel", variant="default")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "app-update-cancel":
            self.app.pop_screen()
            return
        if event.button.id != "app-update-run":
            return
        branch = self.query_one("#app-update-branch", Select).value
        if not isinstance(branch, str) or not branch:
            self.app.notify("Select a branch first.", severity="warning")
            return
        fetch = subprocess.run(
            ["git", "-C", str(ROOT), "fetch", "origin", f"refs/heads/{branch}:refs/remotes/origin/{branch}"],
            cwd=ROOT, capture_output=True, text=True, check=False,
        )
        output = [(fetch.stdout + fetch.stderr).strip()]
        if fetch.returncode:
            self.app.push_screen(MessageScreen("Update failed", "\n".join(x for x in output if x)))
            return
        exists = subprocess.run(
            ["git", "-C", str(ROOT), "show-ref", "--verify", "--quiet", f"refs/heads/{branch}"],
            cwd=ROOT, check=False,
        ).returncode == 0
        switch = subprocess.run(
            ["git", "-C", str(ROOT), "switch", branch] if exists else
            ["git", "-C", str(ROOT), "switch", "--track", "-c", branch, f"origin/{branch}"],
            cwd=ROOT, capture_output=True, text=True, check=False,
        )
        output.append((switch.stdout + switch.stderr).strip())
        if switch.returncode:
            self.app.push_screen(MessageScreen("Update failed", "\n".join(x for x in output if x)))
            return
        pull = subprocess.run(
            ["git", "-C", str(ROOT), "pull", "--ff-only", "origin", branch],
            cwd=ROOT, capture_output=True, text=True, check=False,
        )
        output.append((pull.stdout + pull.stderr).strip())
        self.app.pop_screen()
        self.app.push_screen(MessageScreen(
            f"Update {'complete' if pull.returncode == 0 else 'failed'}",
            "\n".join(x for x in output if x) or f"git pull exited {pull.returncode}",
        ))

    def action_go_back(self) -> None:
        self.app.pop_screen()


class PluginScreen(Screen):
    """List add-ons by name and open an action submenu for each."""

    BINDINGS = [("escape", "go_back", "Back")]

    def compose(self) -> ComposeResult:
        yield Static("Add-ons", classes="menu-title")
        with VerticalScroll(id="content"):
            with Horizontal(classes="tool-row"):
                yield Button("ADS-B Radar", id="plugin-adsb", variant="primary")
                yield Button("OUI-Spy", id="plugin-oui", variant="primary")\n                yield Button("LoRa Monitor", id="plugin-lora", variant="primary")
            yield Static("Installed add-ons", classes="menu-title")
            yield Static("Loading add-on status...", id="plugin-status")
            with Horizontal(classes="tool-row"):
                yield Button("Update all", id="plugin-update-all", variant="primary")
                yield Button("Add from GitHub URL", id="plugin-add-github", variant="primary")
            with Horizontal(classes="tool-row"):
                yield Button("Back", id="plugin-back", variant="default")

    def on_mount(self) -> None:
        self.refresh_status()

    def refresh_status(self) -> None:
        manager = subprocess.run(
            ["bash", str(ROOT / "plugin_manager.sh"), "list"],
            cwd=ROOT, capture_output=True, text=True, check=False
        )
        lines = []
        if manager.returncode == 0:
            for line in manager.stdout.splitlines():
                fields = line.split("\t")
                if len(fields) >= 3:
                    state = "installed" if fields[2] == "ON" else "not installed"
                    lines.append(f"{fields[1]}: {state}")
        discovered = subprocess.run(
            [sys.executable, str(ROOT / "plugin_menu.py"), "--list"],
            cwd=ROOT, capture_output=True, text=True, check=False,
            env={**os.environ, "PYTHONPATH": str(ROOT)}
        )
        if discovered.returncode == 0:
            for line in discovered.stdout.splitlines():
                fields = line.split("\t", 1)
                if len(fields) == 2 and fields[0] not in {"adsb_radar", "oui_spy", "lora_monitor"}:
                    lines.append(f"{fields[1]} ({fields[0]}): installed")
        self.query_one("#plugin-status", Static).update("\n".join(lines or ["No add-ons are installed."]))

    def run_manager(self, args: list[str], label: str) -> None:
        try:
            result = subprocess.run(
                ["bash", str(ROOT / "plugin_manager.sh"), *args],
                cwd=ROOT, capture_output=True, text=True, check=False,
                env={**os.environ, "PYTHONPATH": str(ROOT)}
            )
            output = (result.stdout + ("\n" if result.stdout and result.stderr else "") + result.stderr).strip()
            if not output:
                output = f"{label} finished with exit status {result.returncode}."
            self.refresh_status()
            self.app.push_screen(MessageScreen(
                f"{label}: {'success' if result.returncode == 0 else 'failed'}", output
            ))
        except OSError as exc:
            self.app.push_screen(MessageScreen(f"{label}: failed", str(exc)))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id or ""
        if button_id == "plugin-back":
            self.app.pop_screen()
        elif button_id == "plugin-add-github":
            self.app.push_screen(GitHubPluginScreen())
        elif button_id == "plugin-update-all":
            self.run_manager(["update", "all"], "Update all add-ons")
        elif button_id == "plugin-adsb":
            self.app.push_screen(PluginActionsScreen("adsb_radar", "ADS-B Radar"))
        elif button_id == "plugin-oui":
            self.app.push_screen(PluginActionsScreen("oui_spy", "OUI-Spy"))

    def action_go_back(self) -> None:
        self.app.pop_screen()


class PluginActionsScreen(Screen):
    """Action submenu for a single add-on, including branch selection."""

    BINDINGS = [("escape", "go_back", "Back")]

    def __init__(self, plugin_id: str, label: str) -> None:
        super().__init__()
        self.plugin_id = plugin_id
        self.label = label

    def compose(self) -> ComposeResult:
        branches_result = subprocess.run(
            ["bash", str(ROOT / "plugin_manager.sh"), "branches", self.plugin_id],
            cwd=ROOT, capture_output=True, text=True, check=False, timeout=25,
        )
        branches = [line.strip() for line in branches_result.stdout.splitlines() if line.strip()]
        installed = (ROOT / "plugins" / self.plugin_id / ".git").is_dir()
        current = ""
        if installed:
            result = subprocess.run(
                ["git", "-C", str(ROOT / "plugins" / self.plugin_id), "branch", "--show-current"],
                capture_output=True, text=True, check=False,
            )
            current = result.stdout.strip()
        if current and current not in branches:
            branches.insert(0, current)
        if not branches:
            branches = ["main"]
        selected = current if current in branches else branches[0]
        yield Static(self.label, classes="menu-title")
        yield Static(f"Status: {'installed' if installed else 'not installed'}")
        yield Static("Branch used for install, update, or branch change:")
        yield Select([(branch, branch) for branch in branches], value=selected,
                     id="plugin-branch-select", allow_blank=False)
        with Horizontal(classes="tool-row"):
            yield Button("Install", id="plugin-action-install", variant="primary")
            yield Button("Uninstall", id="plugin-action-uninstall", variant="error")
        with Horizontal(classes="tool-row"):
            yield Button("Update", id="plugin-action-update", variant="primary")
            yield Button("Change branch", id="plugin-action-branch", variant="primary")
        with Horizontal(classes="tool-row"):
            yield Button("Back", id="plugin-action-back", variant="default")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id or ""
        if button_id == "plugin-action-back":
            self.app.pop_screen()
            return
        branch = self.query_one("#plugin-branch-select", Select).value
        if not isinstance(branch, str) or not branch:
            self.app.notify("Select a branch first.", severity="warning")
            return
        if button_id == "plugin-action-uninstall":
            self.app.push_screen(ConfirmRemoveScreen(self.plugin_id, f"Uninstall {self.label}"))
        elif button_id == "plugin-action-install":
            self.app.pop_screen()
            plugin_screen = self.app.screen
            if isinstance(plugin_screen, PluginScreen):
                plugin_screen.run_manager(["install", self.plugin_id, branch], f"Install {self.label} ({branch})")
        elif button_id == "plugin-action-update":
            self.app.pop_screen()
            plugin_screen = self.app.screen
            if isinstance(plugin_screen, PluginScreen):
                plugin_screen.run_manager(["update", self.plugin_id, branch], f"Update {self.label} ({branch})")
        elif button_id == "plugin-action-branch":
            self.app.pop_screen()
            plugin_screen = self.app.screen
            if isinstance(plugin_screen, PluginScreen):
                plugin_screen.run_manager(["branch", self.plugin_id, branch], f"Change {self.label} to {branch}")

    def action_go_back(self) -> None:
        self.app.pop_screen()


class GitHubPluginScreen(Screen):
    """Collect a GitHub repository URL and install it as a plugin."""

    BINDINGS = [("escape", "go_back", "Back")]

    def compose(self) -> ComposeResult:
        yield Static("Add Plugin from GitHub", classes="menu-title")
        yield Static(
            "Enter a public GitHub repository URL. The repository must contain "
            "a plugin __init__.py at its root and implement the SpectrumSnek plugin API."
        )
        yield Input(placeholder="https://github.com/owner/repository", id="github-url")
        yield Input(placeholder="Branch (optional, defaults to repository default)", id="github-branch")
        with Horizontal(classes="tool-row"):
            yield Button("Install plugin", id="github-install", variant="primary")
            yield Button("Cancel", id="github-cancel", variant="default")

    def install_url(self) -> None:
        url = self.query_one("#github-url", Input).value.strip()
        if not url:
            self.app.notify("Enter a GitHub repository URL first.", severity="warning")
            return
        branch = self.query_one("#github-branch", Input).value.strip()
        self.app.pop_screen()
        plugin_screen = self.app.screen
        if isinstance(plugin_screen, PluginScreen):
            args = ["install-url", url] + ([branch] if branch else [])
            plugin_screen.run_manager(args, "Add GitHub plugin")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "github-cancel":
            self.app.pop_screen()
        elif event.button.id == "github-install":
            self.install_url()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "github-url":
            self.install_url()

    def action_go_back(self) -> None:
        self.app.pop_screen()


class ConfirmRemoveScreen(Screen):
    """Confirm destructive removal of an installed plugin directory."""

    BINDINGS = [("escape", "go_back", "Cancel")]

    def __init__(self, plugin_id: str, label: str) -> None:
        super().__init__()
        self.plugin_id = plugin_id
        self.label = label

    def compose(self) -> ComposeResult:
        yield Static("Remove Plugin", classes="menu-title")
        yield Static(f"Remove {self.plugin_id}? Its plugin directory and local Git checkout will be deleted.")
        with Horizontal(classes="tool-row"):
            yield Button("Remove plugin", id="confirm-remove", variant="error")
            yield Button("Cancel", id="cancel-remove", variant="default")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel-remove":
            self.app.pop_screen()
            return
        if event.button.id == "confirm-remove":
            plugin_id = self.plugin_id
            self.app.pop_screen()
            parent = self.app.screen
            if isinstance(parent, PluginActionsScreen):
                self.app.pop_screen()
                parent = self.app.screen
            if isinstance(parent, PluginScreen):
                parent.run_manager(["remove", plugin_id], self.label)

    def action_go_back(self) -> None:
        self.app.pop_screen()


class ServiceScreen(Screen):
    """Service controls under Utilities -> Configure."""

    BINDINGS = [("escape", "go_back", "Back")]

    def compose(self) -> ComposeResult:
        yield Static("Configure Web Service", classes="menu-title")
        with VerticalScroll(id="content"):
            actions = ("setup", "start", "stop", "restart", "status", "logs", "back")
            for index in range(0, len(actions), 2):
                with Horizontal(classes="tool-row"):
                    for action in actions[index:index + 2]:
                        yield Button(
                            action,
                            id="service-back" if action == "back" else f"service-{action}",
                            variant="default" if action == "back" else "primary",
                        )

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
        with VerticalScroll(id="message-content"):
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
    #message-content { height: 1fr; padding: 0 1; }
    #tool-grid { height: auto; }
    .tool-row { height: 3; width: 100%; }
    Button { width: 1fr; min-width: 1; min-height: 3; height: 3; margin: 0; padding: 0 1; }
    Input { width: 100%; }
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
            buttons = [
                (tool.get("name") or tool["id"].replace("_", " ").title(),
                 f"launch-{tool['id']}", "primary")
                for tool in tool_catalog()
            ]
            buttons.append(("utilities", "open-utilities", "default"))
            for index in range(0, len(buttons), 2):
                with Horizontal(classes="tool-row"):
                    for label, button_id, variant in buttons[index:index + 2]:
                        yield Button(label, id=button_id, variant=variant)
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
