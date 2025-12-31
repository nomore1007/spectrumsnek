#!/usr/bin/env python3
"""
Audio Output Selector - SpectrumSnek 🐍📻

Curses-based interface for selecting audio output devices, including Bluetooth.
"""

import curses
import pyaudio
import subprocess
import time
from typing import List, Dict, Any, Optional

class AudioDevice:
    """Represents an audio device."""
    def __init__(self, index: int, name: str, max_output_channels: int, is_bluetooth: bool = False):
        self.index = index
        self.name = name
        self.max_output_channels = max_output_channels
        self.is_bluetooth = is_bluetooth

class AudioOutputSelector:
    """Audio output device selector with curses interface."""

    def __init__(self):
        self.devices: List[AudioDevice] = []
        self.selected_index = 0
        self.current_default = None
        self.status_message = ""

    def scan_devices(self) -> List[AudioDevice]:
        """Scan for available audio output devices."""
        try:
            audio = pyaudio.PyAudio()
            devices = []

            for i in range(audio.get_device_count()):
                info = audio.get_device_info_by_index(i)
                max_out = int(info.get('maxOutputChannels', 0))
                if max_out > 0:  # Output device
                    name = str(info.get('name', f'Device {i}'))
                    is_bt = 'blue' in name.lower() or 'bluetooth' in name.lower()
                    devices.append(AudioDevice(i, name, max_out, is_bt))

            audio.terminate()
            return devices

        except Exception as e:
            self.status_message = f"Error scanning devices: {e}"
            return []

    def get_current_default(self) -> Optional[AudioDevice]:
        """Get the current default output device."""
        try:
            audio = pyaudio.PyAudio()
            default_info = audio.get_default_output_device_info()
            audio.terminate()

            for device in self.devices:
                if device.index == default_info['index']:
                    return device
            return None
        except Exception:
            return None

    def set_default_device(self, device: AudioDevice) -> bool:
        """Set the default audio output device."""
        try:
            # Note: pyaudio doesn't directly set system default
            # This would require system-specific commands
            # For now, just show instructions
            self.status_message = f"To set {device.name} as default, use system audio settings"
            return True
        except Exception as e:
            self.status_message = f"Error setting device: {e}"
            return False

    def test_audio_device(self, device: AudioDevice) -> bool:
        """Test audio output on the selected device."""
        try:
            audio = pyaudio.PyAudio()
            stream = audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=44100,
                output=True,
                output_device_index=device.index
            )

            # Generate a short test tone
            import numpy as np
            duration = 0.5
            frequency = 440  # A4 note
            samples = np.sin(2 * np.pi * frequency * np.arange(44100 * duration)).astype(np.int16)

            stream.write(samples.tobytes())
            stream.stop_stream()
            stream.close()
            audio.terminate()

            self.status_message = f"Test tone played on {device.name}"
            return True

        except Exception as e:
            self.status_message = f"Test failed: {e}"
            return False

    def draw_interface(self, stdscr):
        """Draw the audio selector interface."""
        stdscr.clear()
        height, width = stdscr.getmaxyx()

        # Title
        title = "Audio Output Selector 🐍📻"
        stdscr.addstr(0, (width - len(title)) // 2, title, curses.A_BOLD)

        # Current default
        if self.current_default:
            default_info = f"Current Default: {self.current_default.name}"
            stdscr.addstr(2, 2, default_info)

        # Status
        if self.status_message:
            status = self.status_message[:width-4]
            stdscr.addstr(4, 2, f"Status: {status}")

        # Devices
        start_y = 6
        if not self.devices:
            stdscr.addstr(start_y, 4, "No audio output devices found.")
        else:
            for i, device in enumerate(self.devices):
                y = start_y + i * 4
                if y + 3 >= height:
                    break

                # Device info
                icon = "🔵" if device.is_bluetooth else "🔊"
                status_indicator = " (Default)" if self.current_default and device.index == self.current_default.index else ""

                if i == self.selected_index:
                    stdscr.addstr(y, 4, f"> {icon} {device.name}{status_indicator}", curses.A_REVERSE | curses.A_BOLD)
                else:
                    stdscr.addstr(y, 4, f"  {icon} {device.name}{status_indicator}")

                # Details
                details = f"Index: {device.index} | Channels: {device.max_output_channels}"
                stdscr.addstr(y + 1, 6, details)

                # Bluetooth note
                if device.is_bluetooth:
                    stdscr.addstr(y + 2, 6, "Bluetooth audio device", curses.A_DIM)

        # Instructions
        instructions = "↑↓ navigate, Enter test, 's' set default, 'r' rescan, 'q' quit"
        stdscr.addstr(height - 2, (width - len(instructions)) // 2, instructions, curses.A_DIM)

        stdscr.refresh()

    def run_interface(self, stdscr):
        """Run the interactive interface."""
        curses.curs_set(0)

        # Initial scan
        self.devices = self.scan_devices()
        self.current_default = self.get_current_default()

        while True:
            self.draw_interface(stdscr)

            try:
                key = stdscr.getch()

                if key == ord('q') or key == ord('Q'):
                    return
                elif key == ord('r') or key == ord('R'):
                    self.status_message = "Rescanning devices..."
                    stdscr.refresh()
                    self.devices = self.scan_devices()
                    self.current_default = self.get_current_default()
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
                        self.test_audio_device(device)
                elif key == ord('s') or key == ord('S'):
                    if self.devices and 0 <= self.selected_index < len(self.devices):
                        device = self.devices[self.selected_index]
                        self.set_default_device(device)
                elif key == 27:  # ESC
                    return

                time.sleep(0.05)

            except KeyboardInterrupt:
                return

    def run(self):
        """Main run method."""
        print("Audio Output Selector")
        print("====================")

        # Check if pyaudio is available
        try:
            import pyaudio
        except ImportError:
            print("pyaudio not found. Please install with: pip install pyaudio")
            return

        try:
            curses.wrapper(self.run_interface)
        except KeyboardInterrupt:
            print("\nAudio selector stopped by user")
        except Exception as e:
            print(f"Error in audio selector: {e}")

if __name__ == "__main__":
    selector = AudioOutputSelector()
    selector.run()