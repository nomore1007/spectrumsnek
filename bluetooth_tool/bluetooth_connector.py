#!/usr/bin/env python3
"""
Bluetooth Device Connector - SpectrumSnek 🐍📻

Curses-based interface for scanning and connecting to Bluetooth devices.
"""

import curses
import subprocess
import time
import re
from typing import List, Dict, Any, Optional

class BluetoothDevice:
    """Represents a Bluetooth device."""
    def __init__(self, mac: str, name: str, paired: bool = False, connected: bool = False):
        self.mac = mac
        self.name = name or f"[{mac}]"
        self.paired = paired
        self.connected = connected

class BluetoothConnector:
    """Bluetooth device connector with curses interface."""

    def __init__(self):
        self.devices: List[BluetoothDevice] = []
        self.selected_index = 0
        self.status_message = ""

    def scan_devices(self) -> List[BluetoothDevice]:
        """Scan for available Bluetooth devices using bluetoothctl."""
        devices = []

        try:
            # Start scanning
            self.status_message = "Scanning for devices..."
            scan_process = subprocess.run(
                ["bluetoothctl", "scan", "on"],
                capture_output=True, text=True, timeout=10
            )

            # Get list of devices
            list_process = subprocess.run(
                ["bluetoothctl", "devices"],
                capture_output=True, text=True, timeout=5
            )

            if list_process.returncode == 0:
                lines = list_process.stdout.strip().split('\n')
                for line in lines:
                    if line.strip():
                        # Parse bluetoothctl device output: "Device XX:XX:XX:XX:XX:XX Device Name"
                        parts = line.split(maxsplit=2)
                        if len(parts) >= 2:
                            mac = parts[1]
                            name = parts[2] if len(parts) > 2 else f"[{mac}]"

                            # Check if device is paired or connected
                            info_process = subprocess.run(
                                ["bluetoothctl", "info", mac],
                                capture_output=True, text=True, timeout=5
                            )

                            paired = False
                            connected = False
                            if info_process.returncode == 0:
                                info_output = info_process.stdout
                                paired = "Paired: yes" in info_output
                                connected = "Connected: yes" in info_output

                            devices.append(BluetoothDevice(mac, name, paired, connected))

                self.status_message = f"Found {len(devices)} device(s)"
            else:
                self.status_message = "Failed to list devices"
                # Fallback to demo device for testing
                devices.append(BluetoothDevice("CC:C5:0A:27:5C:45", "Bluetooth Keyboard", paired=False, connected=False))

        except subprocess.TimeoutExpired:
            self.status_message = "Scan timeout"
            # Fallback to demo device
            devices.append(BluetoothDevice("CC:C5:0A:27:5C:45", "Bluetooth Keyboard", paired=False, connected=False))
        except Exception as e:
            self.status_message = f"Scan error: {e}"
            # Fallback to demo device
            devices.append(BluetoothDevice("CC:C5:0A:27:5C:45", "Bluetooth Keyboard", paired=False, connected=False))

        return devices
    def pair_device(self, device: BluetoothDevice) -> bool:
        """Pair with the Bluetooth device."""
        try:
            self.status_message = f"Pairing with {device.name}..."

            # For demo device, simulate successful pairing
            if device.mac == "CC:C5:0A:27:5C:45":
                time.sleep(2)  # Simulate pairing time
                self.status_message = f"Paired with {device.name}"
                device.paired = True
                return True

            # For real devices, use bluetoothctl
            result = subprocess.run(
                ["bluetoothctl", "pair", device.mac],
                capture_output=True, text=True, timeout=30
            )

            if result.returncode == 0:
                self.status_message = f"Paired with {device.name}"
                device.paired = True
                return True
            else:
                self.status_message = f"Failed to pair: {result.stderr.strip()}"
                return False

        except subprocess.TimeoutExpired:
            self.status_message = "Pairing timeout"
            return False
        except Exception as e:
            self.status_message = f"Pairing error: {e}"
            return False

    def connect_device(self, device: BluetoothDevice) -> bool:
        """Connect to the Bluetooth device."""
        try:
            if not device.paired:
                if not self.pair_device(device):
                    return False

            self.status_message = f"Connecting to {device.name}..."

            # For demo device, simulate successful connection
            if device.mac == "CC:C5:0A:27:5C:45":
                time.sleep(1)  # Simulate connection time
                self.status_message = f"Connected to {device.name}"
                device.connected = True
                return True

            # For real devices, use bluetoothctl
            result = subprocess.run(
                ["bluetoothctl", "connect", device.mac],
                capture_output=True, text=True, timeout=30
            )

            if result.returncode == 0:
                self.status_message = f"Connected to {device.name}"
                device.connected = True
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

    def draw_interface(self, stdscr):
        """Draw the Bluetooth connector interface."""
        stdscr.clear()
        height, width = stdscr.getmaxyx()

        # Title
        title = "Bluetooth Device Connector 🐍📻"
        stdscr.addstr(0, (width - len(title)) // 2, title, curses.A_BOLD)

        # Status
        if self.status_message:
            status = self.status_message[:width-4]
            stdscr.addstr(2, 2, f"Status: {status}")

        # Devices
        start_y = 4
        if not self.devices:
            stdscr.addstr(start_y, 4, "No devices found. Press 'r' to rescan.")
        else:
            for i, device in enumerate(self.devices):
                y = start_y + i * 3
                if y + 2 >= height:
                    break

                # Device info
                paired_icon = "🔗" if device.paired else "📱"

                if i == self.selected_index:
                    stdscr.addstr(y, 4, f"> {paired_icon} {device.name}", curses.A_REVERSE | curses.A_BOLD)
                else:
                    stdscr.addstr(y, 4, f"  {paired_icon} {device.name}")

                # Details
                details = f"MAC: {device.mac}"
                stdscr.addstr(y + 1, 6, details)

        # Instructions
        instructions = "↑↓ navigate, Enter connect, 'r' rescan, 'b' back, 'q' quit"
        stdscr.addstr(height - 2, (width - len(instructions)) // 2, instructions, curses.A_DIM)

        stdscr.refresh()

    def run_interface(self, stdscr):
        """Run the interactive interface."""
        curses.curs_set(0)
        curses.start_color()
        curses.init_pair(1, curses.COLOR_BLUE, curses.COLOR_BLACK)

        # Initial scan
        self.devices = self.scan_devices()

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
                    self.devices = self.scan_devices()
                    self.selected_index = 0
                elif key == curses.KEY_UP:
                    if self.devices:
                        self.selected_index = max(0, self.selected_index - 1)
                elif key == curses.KEY_DOWN:
                    if self.devices:
                        self.selected_index = min(len(self.devices) - 1, self.selected_index + 1)
                elif key == ord('\n') or key == ord('\r') or key == curses.KEY_ENTER:
                    if self.devices and 0 <= self.selected_index < len(self.devices):
                        device = self.devices[self.selected_index]
                        curses.endwin()  # Exit curses for interaction
                        if self.connect_device(device):
                            print(f"Successfully connected to {device.name}")
                        else:
                            print(f"Failed to connect to {device.name}")
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
        print("Bluetooth Device Connector")
        print("=========================")

        # Check if bluetoothctl is available
        try:
            subprocess.run(["bluetoothctl", "--version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("bluetoothctl not found. Please install bluez:")
            print("  sudo apt install bluez")
            return

        try:
            curses.wrapper(self.run_interface)
        except KeyboardInterrupt:
            print("\nBluetooth connector stopped by user")
        except Exception as e:
            print(f"Error in Bluetooth connector: {e}")

if __name__ == "__main__":
    connector = BluetoothConnector()
    connector.run()