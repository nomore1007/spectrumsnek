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
    def __init__(self, mac: str, name: str, paired: bool = False):
        self.mac = mac
        self.name = name or f"[{mac}]"
        self.paired = paired

class BluetoothConnector:
    """Bluetooth device connector with curses interface."""

    def __init__(self):
        self.devices: List[BluetoothDevice] = []
        self.selected_index = 0
        self.status_message = ""

    def scan_devices(self) -> List[BluetoothDevice]:
        """Scan for available Bluetooth devices using hcitool."""
        try:
            output = ""  # Initialize output variable

            # Check if Bluetooth is available using bluetoothctl
            self.status_message = "Checking Bluetooth adapter..."
            show_result = subprocess.run(
                ["bluetoothctl", "show"],
                capture_output=True, text=True, timeout=5
            )

            if show_result.returncode != 0:
                self.status_message = f"Bluetooth controller not available: {show_result.stderr.strip()}"
                return []

            adapter_info = show_result.stdout.strip()
            if "Powered: no" in adapter_info:
                self.status_message = f"Bluetooth is powered off. Run: bluetoothctl power on"
                return []
            elif "Powered: yes" not in adapter_info:
                self.status_message = f"Bluetooth status unknown. Info: {adapter_info[:150]}"
                return []

            self.status_message = f"Adapter ready. Info: {adapter_info[:100]}"

            # Use bluetoothctl for scanning
            self.status_message = "Starting scan..."
            scan_on = subprocess.run(["bluetoothctl", "scan", "on"], timeout=2, capture_output=True)
            if scan_on.returncode != 0:
                self.status_message = f"Failed to start scan: {scan_on.stderr.strip()}"
                return []

            self.status_message = "Scanning... Put devices in pairing mode (40 sec)"
            time.sleep(40)  # Scan for 40 seconds

            self.status_message = "Stopping scan..."
            scan_off = subprocess.run(["bluetoothctl", "scan", "off"], timeout=2, capture_output=True)
            if scan_off.returncode != 0:
                self.status_message = f"Warning: Failed to stop scan: {scan_off.stderr.strip()}"

            # Get devices
            result = subprocess.run(
                ["bluetoothctl", "devices"],
                capture_output=True, text=True, timeout=5
            )

            if result.returncode != 0:
                self.status_message = f"Failed to get devices: {result.stderr.strip()}"
                return []

            output = result.stdout.strip()

            devices = []

            for line in output.split('\n'):
                if not line.strip():
                    continue

                # Parse: Device XX:XX:XX:XX:XX:XX Name
                match = re.match(r'Device\s+([0-9A-F:]{17})\s+(.*)', line)
                if match:
                    mac = match.group(1)
                    name = match.group(2).strip()

                    # Check if paired
                    paired_result = subprocess.run(
                        ["bluetoothctl", "info", mac],
                        capture_output=True, text=True, timeout=5
                    )
                    paired = "Paired: yes" in paired_result.stdout

                    devices.append(BluetoothDevice(mac, name, paired=paired))

            if not devices:
                self.status_message = f"No devices found. Devices output: {output[:200]}"
            else:
                self.status_message = f"Found {len(devices)} device(s): {[d.name for d in devices]}"

            return devices

        except subprocess.TimeoutExpired:
            self.status_message = "Scan timeout - try again"
            return []
        except FileNotFoundError:
            self.status_message = "hcitool not found. Install with: sudo apt install bluez"
            return []
        except Exception as e:
            self.status_message = f"Scan error: {e}"
            return []

            if "Powered: no" in show_result.stdout:
                self.status_message = "Bluetooth is powered off. Enable with: bluetoothctl power on"
                return []
            elif "Powered: yes" not in show_result.stdout:
                self.status_message = "Bluetooth status unknown. Try: sudo systemctl start bluetooth"
                return []

            # Start scan
            scan_on = subprocess.run(["bluetoothctl", "scan", "on"], timeout=2, capture_output=True)
            if scan_on.returncode != 0:
                self.status_message = "Failed to start scan"
                return []

            self.status_message = "Scanning... Put devices in pairing mode (35 sec)"
            time.sleep(35)  # Scan for 35 seconds

            # Stop scan
            subprocess.run(["bluetoothctl", "scan", "off"], timeout=2, capture_output=True)

            # Get devices
            result = subprocess.run(
                ["bluetoothctl", "devices"],
                capture_output=True, text=True, timeout=5
            )

            output = result.stdout.strip() or result.stderr.strip()

            if result.returncode != 0:
                self.status_message = f"Scan failed: {result.stderr.strip()}"
                return []

            devices = []

            for line in output.split('\n'):
                if not line.strip():
                    continue

                # Parse: Device XX:XX:XX:XX:XX:XX Name
                match = re.match(r'Device\s+([0-9A-F:]{17})\s+(.*)', line)
                if match:
                    mac = match.group(1)
                    name = match.group(2).strip()

                    # Check if paired
                    paired_result = subprocess.run(
                        ["bluetoothctl", "info", mac],
                        capture_output=True, text=True, timeout=5
                    )
                    paired = "Paired: yes" in paired_result.stdout

                    devices.append(BluetoothDevice(mac, name, paired=paired))

            if not devices:
                self.status_message = f"No devices found. Check devices are discoverable. Output: {result.stdout.strip()[:100]}"
            else:
                self.status_message = f"Found {len(devices)} device(s): {[d.name for d in devices]}"

            return devices

        except subprocess.TimeoutExpired:
            self.status_message = "Scan timeout - try again"
            return []
        except FileNotFoundError:
            self.status_message = "bluetoothctl not found. Install with: sudo apt install bluez"
            return []
        except Exception as e:
            self.status_message = f"Scan error: {e}"
            return []

            if "UP" not in hciconfig_result.stdout:
                self.status_message = "Bluetooth adapter is down. Run: sudo hciconfig hci0 up"
                return []

            # Use hcitool for scanning
            self.status_message = "Scanning... Put devices in pairing mode"
            result = subprocess.run(
                ["hcitool", "scan"],
                capture_output=True, text=True, timeout=15
            )

            if result.returncode != 0:
                self.status_message = f"Scan failed: {result.stderr.strip()}"
                return []

            devices = []

            for line in result.stdout.strip().split('\n'):
                if not line.strip():
                    continue

                # Skip header line
                if line.startswith('\t') or line.startswith('Scanning'):
                    continue

                # Parse: \tXX:XX:XX:XX:XX:XX\tName
                parts = line.strip().split('\t')
                if len(parts) >= 2:
                    mac = parts[0].strip()
                    name = parts[1].strip() if len(parts) > 1 else ""

                    # Validate MAC address format
                    if re.match(r'^([0-9A-F]{2}:){5}[0-9A-F]{2}$', mac, re.IGNORECASE):
                        # Check if paired using bluetoothctl
                        paired = False
                        try:
                            paired_result = subprocess.run(
                                ["bluetoothctl", "info", mac],
                                capture_output=True, text=True, timeout=3
                            )
                            paired = "Paired: yes" in paired_result.stdout
                        except:
                            pass

                        devices.append(BluetoothDevice(mac, name, paired=paired))

            if not devices:
                self.status_message = "No devices found. Make sure devices are discoverable."
            else:
                self.status_message = f"Found {len(devices)} device(s)"

            return devices

        except subprocess.TimeoutExpired:
            self.status_message = "Scan timeout - try again"
            return []
        except FileNotFoundError:
            self.status_message = "hcitool not found. Install with: sudo apt install bluez"
            return []
        except Exception as e:
            self.status_message = f"Scan error: {e}"
            return []

    def pair_device(self, device: BluetoothDevice) -> bool:
        """Pair with the Bluetooth device."""
        try:
            self.status_message = f"Pairing with {device.name}..."

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

            result = subprocess.run(
                ["bluetoothctl", "connect", device.mac],
                capture_output=True, text=True, timeout=30
            )

            if result.returncode == 0:
                self.status_message = f"Connected to {device.name}"
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