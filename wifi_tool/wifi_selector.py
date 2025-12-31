#!/usr/bin/env python3
"""
WiFi Network Selector - SpectrumSnek 🐍📻

Curses-based interface for scanning and connecting to WiFi networks.
"""

import curses
import subprocess
import time
import re
from typing import List, Dict, Any, Optional

class WiFiNetwork:
    """Represents a WiFi network."""
    def __init__(self, ssid: str, signal: int, security: str, bssid: str = ""):
        self.ssid = ssid or "<Hidden>"
        self.signal = signal
        self.security = security
        self.bssid = bssid

class WiFiSelector:
    """WiFi network selector with curses interface."""

    def __init__(self):
        self.networks: List[WiFiNetwork] = []
        self.selected_index = 0
        self.status_message = ""

    def scan_networks(self) -> List[WiFiNetwork]:
        """Scan for available WiFi networks using nmcli."""
        try:
            result = subprocess.run(
                ["nmcli", "-t", "-f", "SSID,SIGNAL,SECURITY,BSSID", "device", "wifi", "list"],
                capture_output=True, text=True, timeout=10
            )

            if result.returncode != 0:
                self.status_message = f"Scan failed: {result.stderr.strip()}"
                return []

            networks = []
            seen_ssids = set()

            for line in result.stdout.strip().split('\n'):
                if not line.strip():
                    continue

                parts = line.split(':')
                if len(parts) >= 3:
                    ssid = parts[0]
                    signal = int(parts[1]) if parts[1].isdigit() else 0
                    security = parts[2] if len(parts) > 2 else ""
                    bssid = parts[3] if len(parts) > 3 else ""

                    # Skip duplicates (same SSID)
                    if ssid not in seen_ssids:
                        networks.append(WiFiNetwork(ssid, signal, security, bssid))
                        seen_ssids.add(ssid)

            networks.sort(key=lambda x: x.signal, reverse=True)
            return networks

        except subprocess.TimeoutExpired:
            self.status_message = "Scan timeout"
            return []
        except FileNotFoundError:
            self.status_message = "nmcli not found. Install NetworkManager."
            return []
        except Exception as e:
            self.status_message = f"Scan error: {e}"
            return []

    def connect_to_network(self, network: WiFiNetwork) -> bool:
        """Connect to the selected WiFi network."""
        try:
            self.status_message = f"Connecting to {network.ssid}..."

            if network.security and network.security != "--":
                # Secure network, might need password
                # For simplicity, try without password first, then prompt if fails
                result = subprocess.run(
                    ["nmcli", "device", "wifi", "connect", network.ssid],
                    capture_output=True, text=True, timeout=30
                )

                if result.returncode != 0 and "Secrets were required" in result.stderr:
                    # Need password
                    password = self.prompt_password(network.ssid)
                    if password:
                        result = subprocess.run(
                            ["nmcli", "device", "wifi", "connect", network.ssid, "password", password],
                            capture_output=True, text=True, timeout=30
                        )

                if result.returncode == 0:
                    self.status_message = f"Connected to {network.ssid}"
                    return True
                else:
                    self.status_message = f"Failed to connect: {result.stderr.strip()}"
                    return False
            else:
                # Open network
                result = subprocess.run(
                    ["nmcli", "device", "wifi", "connect", network.ssid],
                    capture_output=True, text=True, timeout=30
                )

                if result.returncode == 0:
                    self.status_message = f"Connected to {network.ssid}"
                    return True
                else:
                    self.status_message = f"Failed to connect: {result.stderr.strip()}"
                    return False

        except subprocess.TimeoutExpired:
            self.status_message = "Connection timeout"
            return False
        except Exception as e:
            self.status_message = f"Connection error: {e}"
            return False

    def prompt_password(self, ssid: str) -> Optional[str]:
        """Prompt for WiFi password (simple text input)."""
        # For now, since curses is complex for password, use input()
        # In full implementation, could use curses text box
        try:
            password = input(f"Password for {ssid}: ")
            return password.strip()
        except KeyboardInterrupt:
            return None

    def draw_interface(self, stdscr):
        """Draw the WiFi selector interface."""
        stdscr.clear()
        height, width = stdscr.getmaxyx()

        # Title
        title = "WiFi Network Selector 🐍📻"
        stdscr.addstr(0, (width - len(title)) // 2, title, curses.A_BOLD)

        # Status
        if self.status_message:
            status = self.status_message[:width-4]
            stdscr.addstr(2, 2, f"Status: {status}")

        # Networks
        start_y = 4
        if not self.networks:
            stdscr.addstr(start_y, 4, "No networks found. Press 'r' to rescan.")
        else:
            for i, network in enumerate(self.networks):
                y = start_y + i * 3
                if y + 2 >= height:
                    break

                # Network info
                signal_bars = "█" * (network.signal // 20) + "░" * (5 - network.signal // 20)
                security_icon = "🔒" if network.security and network.security != "--" else "📶"

                if i == self.selected_index:
                    stdscr.addstr(y, 4, f"> {security_icon} {network.ssid}", curses.A_REVERSE | curses.A_BOLD)
                else:
                    stdscr.addstr(y, 4, f"  {security_icon} {network.ssid}")

                # Details
                details = f"Signal: {signal_bars} ({network.signal}%)"
                if network.security and network.security != "--":
                    details += f" | Security: {network.security}"
                stdscr.addstr(y + 1, 6, details)

        # Instructions
        instructions = "↑↓ navigate, Enter connect, 'r' rescan, 'b' back, 'q' quit"
        stdscr.addstr(height - 2, (width - len(instructions)) // 2, instructions, curses.A_DIM)

        stdscr.refresh()

    def run_interface(self, stdscr):
        """Run the interactive interface."""
        curses.curs_set(0)
        curses.start_color()
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)

        # Initial scan
        self.networks = self.scan_networks()

        while True:
            self.draw_interface(stdscr)

            try:
                key = stdscr.getch()

                if key == ord('b') or key == ord('B'):
                    return
                elif key == ord('q') or key == ord('Q'):
                    import sys
                    sys.exit(0)
                elif key == ord('r') or key == ord('R'):
                    self.status_message = "Scanning..."
                    stdscr.refresh()
                    self.networks = self.scan_networks()
                    self.selected_index = 0
                elif key == curses.KEY_UP:
                    if self.networks:
                        self.selected_index = max(0, self.selected_index - 1)
                elif key == curses.KEY_DOWN:
                    if self.networks:
                        self.selected_index = min(len(self.networks) - 1, self.selected_index + 1)
                elif key == ord('\n') or key == ord('\r') or key == curses.KEY_ENTER:
                    if self.networks and 0 <= self.selected_index < len(self.networks):
                        network = self.networks[self.selected_index]
                        curses.endwin()  # Exit curses for password input
                        if self.connect_to_network(network):
                            print(f"Successfully connected to {network.ssid}")
                        else:
                            print(f"Failed to connect to {network.ssid}")
                        print("\nReturning to menu...")
                        time.sleep(2)
                        curses.wrapper(self.run_interface)  # Re-enter curses
                        return
                elif key == 27:  # ESC
                    return

                time.sleep(0.05)

            except KeyboardInterrupt:
                return

    def run(self):
        """Main run method."""
        print("WiFi Network Selector")
        print("====================")

        # Check if nmcli is available
        try:
            subprocess.run(["nmcli", "--version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("nmcli not found. Please install NetworkManager:")
            print("  sudo apt install network-manager")
            return

        try:
            curses.wrapper(self.run_interface)
        except KeyboardInterrupt:
            print("\nWiFi selector stopped by user")
        except Exception as e:
            print(f"Error in WiFi selector: {e}")

if __name__ == "__main__":
    selector = WiFiSelector()
    selector.run()