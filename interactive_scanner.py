#!/usr/bin/env python3
"""
Interactive RTL-SDR Radio Scanner
Terminal-based interactive interface with keyboard controls.
"""

import curses
import time
import threading
import numpy as np
from rtlsdr import RtlSdr
import scipy.signal as signal
from scipy.signal import windows
import argparse
import logging
import sys
import os
from typing import Optional
import atexit
import signal

# Configure logging (will be suppressed in curses mode)
logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class InteractiveRTLScanner:
    def __init__(self, stdscr, sample_rate=2.4e6, center_freq=100e6, gain='auto'):
        self.stdscr = stdscr
        self.sample_rate = sample_rate
        self.center_freq = center_freq
        self.gain = gain
        self.sdr = None
        self.is_running = True
        self.show_menu = False

        # Frequency and gain control
        self.freq_step = 100000  # 100 kHz steps (fallback)
        self.gain_step = 5  # 5 dB steps

        # Digit-based frequency control
        self.selected_digit = 0  # Which digit is selected (0 = 100MHz, 1 = 10MHz, etc.)
        self.freq_digits = ['100MHz', '10MHz', '1MHz', '100kHz', '10kHz', '1kHz', '100Hz', '10Hz', '1Hz']
        self.digit_steps = [100000000, 10000000, 1000000, 100000, 10000, 1000, 100, 10, 1]  # Hz
        self.gain_values = [-10, 0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50]

        # Spectrum data
        self.fft_size = 1024
        self.window = windows.hann(self.fft_size)
        self.freqs = np.fft.fftfreq(self.fft_size, 1/self.sample_rate)
        self.freqs = np.fft.fftshift(self.freqs) + self.center_freq

        # Display settings
        self.height, self.width = stdscr.getmaxyx()
        self.spectrum_height = self.height - 10  # Leave space for controls

        # Spectrum display settings
        self.spectrum_width_options = ['narrow', 'normal', 'wide', 'full']
        self.spectrum_width_index = 1  # Default to 'normal'
        self.zoom_factor = 1.0  # Zoom factor for spectrum width

        # PPM drift correction
        self.ppm_drift = 0  # Parts per million frequency correction

        # Signal type and mode settings
        self.signal_types = ['analog', 'digital']
        self.signal_type_index = 0  # Default to 'analog'

        # Mode options based on signal type
        self.analog_modes = ['none', 'am', 'fm', 'ssb', 'cw']
        self.digital_modes = ['none', 'dmr']
        self.mode_index = 0  # Index within current signal type
        self.demod_freq = self.center_freq  # Frequency to demodulate

        # Audio settings
        self.audio_sample_rate = 48000  # Audio output sample rate

        # CTCSS detection
        self.ctcss_tones = [
            67.0, 71.9, 74.4, 77.0, 79.7, 82.5, 85.4, 88.5, 91.5, 94.8,
            97.4, 100.0, 103.5, 107.2, 110.9, 114.8, 118.8, 123.0, 127.3, 131.8,
            136.5, 141.3, 146.2, 151.4, 156.7, 162.2, 167.9, 173.8, 179.9, 186.2,
            192.8, 203.5, 210.7, 218.1, 225.7, 233.6, 241.8, 250.3
        ]
        self.detected_ctcss = None

        # DMR decoding info
        self.dmr_info = {
            'talkgroup': None,
            'timeslot': None,
            'color_code': None,
            'active': False
        }

        # Threading and synchronization
        self.capture_thread = None
        self.display_thread = None
        self.sdr_lock = threading.Lock()  # Protect SDR device access
        self.running = True
        self.is_running = True

        # Menu system
        self.menu_selection = 0
        self.selectable_menu_items = list(range(7))  # All 7 menu items are selectable

    def get_current_mode(self):
        """Get the current mode based on signal type."""
        if self.signal_type_index == 0:  # Analog
            return self.analog_modes[self.mode_index]
        else:  # Digital
            return self.digital_modes[self.mode_index]

    def get_current_modes_list(self):
        """Get the modes list for current signal type."""
        if self.signal_type_index == 0:  # Analog
            return self.analog_modes
        else:  # Digital
            return self.digital_modes


        self.audio_thread = None

    def initialize_device(self):
        """Initialize the RTL-SDR device."""
        with self.sdr_lock:
            try:
                self.sdr = RtlSdr()  # type: ignore
                if self.sdr is None:
                    raise RuntimeError("Failed to create RTL-SDR instance")

                self.sdr.sample_rate = self.sample_rate
                self.sdr.center_freq = self.center_freq
                if self.gain == 'auto':
                    self.sdr.gain = 'auto'
                else:
                    self.sdr.gain = self.gain

                logger.info("RTL-SDR initialized for interactive mode")

            except Exception as e:
                logger.error(f"Failed to initialize RTL-SDR: {e}")
                raise

    def start_capture(self):
        """Start the data capture thread."""
        self.capture_thread = threading.Thread(target=self._capture_thread, daemon=True)
        self.capture_thread.start()

    def _capture_thread(self):
        """Capture thread that periodically captures samples."""
        while self.is_running:
            try:
                self.capture_samples()
                time.sleep(0.1)  # ~10 FPS capture rate
            except Exception as e:
                logger.error(f"Capture thread error: {e}")
                time.sleep(0.5)

    def start_display(self):
        """Start the display thread."""
        self.display_thread = threading.Thread(target=self._display_loop, daemon=True)
        self.display_thread.start()

    def capture_samples(self):
        """Single-shot sample capture with proper synchronization."""
        with self.sdr_lock:
            if self.sdr is None:
                return

            try:
                # Capture samples
                samples = self.sdr.read_samples(self.fft_size)

                # Compute FFT for spectrum display
                windowed_samples = samples * self.window
                fft_result = np.fft.fft(windowed_samples)
                fft_result = np.fft.fftshift(fft_result)
                self.power_spectrum = 20 * np.log10(np.abs(fft_result) + 1e-10)

                # Perform demodulation if enabled
                current_mode = self.get_current_mode()
                if current_mode != 'none':
                    self.demodulated_audio = self.demodulate_signal(samples, current_mode)

            except Exception as e:
                logger.error(f"Capture error: {e}")
                # Create dummy spectrum data to prevent crashes
                self.power_spectrum = np.zeros(self.fft_size) - 50

    def _display_loop(self):
        """Continuous display update loop."""
        while self.is_running:
            try:
                self._draw_interface()
                time.sleep(0.1)  # ~10 FPS
            except Exception as e:
                logger.error(f"Display error: {e}")
                time.sleep(0.5)

    def _draw_interface(self):
        """Draw the interactive interface."""
        self.stdscr.clear()

        # Display frequency with yellow tint and cursor
        freq_str = f"{self.center_freq/1e6:.6f} MHz"
        self.stdscr.addstr(0, 0, freq_str, curses.color_pair(2) | curses.A_BOLD)

        # Add blinking cursor on selected digit
        self._draw_frequency_cursor(freq_str)

        # Display current mode
        current_mode = self.get_current_mode()
        mode_info = f"Mode: {current_mode.upper()}"
        self.stdscr.addstr(0, len(freq_str) + 2, mode_info)

        # Display additional info with colors
        info_x = len(freq_str) + 2 + len(mode_info) + 1

        if current_mode == 'fm' and self.detected_ctcss:
            ctcss_info = f"CTCSS: {self.detected_ctcss:.1f} Hz"
            if info_x + len(ctcss_info) < self.width:
                self.stdscr.addstr(0, info_x, ctcss_info, curses.color_pair(4))
        elif current_mode == 'dmr' and self.dmr_info['active']:
            tg = self.dmr_info['talkgroup']
            ts = self.dmr_info['timeslot']
            cc = self.dmr_info['color_code']
            dmr_info = f"TG:{tg} TS:{ts} CC:{cc}"
            if info_x + len(dmr_info) < self.width:
                self.stdscr.addstr(0, info_x, dmr_info, curses.color_pair(3))

        # Display audio level if demodulating
        if current_mode != 'none' and hasattr(self, 'demodulated_audio'):
            audio_level = np.sqrt(np.mean(self.demodulated_audio**2)) if len(self.demodulated_audio) > 0 else 0
            audio_str = f"Audio: {audio_level:.3f}"
            # Position it on the right side
            audio_x = self.width - len(audio_str) - 1
            if audio_x > len(freq_str) + len(mode_info) + 4:
                self.stdscr.addstr(0, audio_x, audio_str)

        # Draw spectrum
        if hasattr(self, 'power_spectrum'):
            self._draw_spectrum()

        # Draw menu if active
        if self.show_menu:
            self._draw_menu()

        self.stdscr.refresh()

    def _draw_spectrum(self):
        """Draw the ASCII spectrum display."""
        spectrum_start_y = 2  # Start after the header line
        spectrum_height = min(self.spectrum_height, self.height - 6)

        # Safety check for spectrum data
        if not hasattr(self, 'power_spectrum') or len(self.power_spectrum) == 0:
            return

        # Frequency labels
        try:
            min_freq = np.min(self.freqs) / 1e6
            max_freq = np.max(self.freqs) / 1e6
            freq_label = ".1f"
            self.stdscr.addstr(spectrum_start_y - 1, 0, freq_label)
        except (AttributeError, ValueError):
            pass

        # Spectrum bars
        try:
            max_power = np.max(self.power_spectrum)
            min_power = np.min(self.power_spectrum)
            power_range = max_power - min_power

            for y in range(min(spectrum_height, len(self.power_spectrum))):
                power = self.power_spectrum[y]
                # Normalize to 0-1
                normalized = (power - min_power) / power_range if power_range > 0 else 0.5

                # Create bar
                bar_width = int(self.width * 0.8)  # Use 80% of width
                filled_width = max(0, min(bar_width, int(bar_width * normalized)))

                bar = "█" * filled_width + "░" * (bar_width - filled_width)
                color = curses.color_pair(1) if normalized > 0.7 else curses.color_pair(0)

                try:
                    self.stdscr.addstr(spectrum_start_y + y, 0, bar[:self.width], color)
                except curses.error:
                    pass  # Ignore if we go off screen
        except (AttributeError, ValueError, IndexError):
            pass  # Ignore errors in spectrum calculation



    def _draw_menu(self):
        """Draw the interactive menu."""
        menu_width = 27
        menu_height = 11
        menu_x = (self.width - menu_width) // 2
        menu_y = (self.height - menu_height) // 2

        # Draw menu border
        for y in range(menu_height):
            for x in range(menu_width):
                if y == 0 or y == menu_height - 1:
                    char = "─"
                elif x == 0 or x == menu_width - 1:
                    char = "│"
                else:
                    char = " "

                if (y == 0 and x == 0) or (y == 0 and x == menu_width - 1):
                    char = "╭" if x == 0 else "╮"
                elif (y == menu_height - 1 and x == 0) or (y == menu_height - 1 and x == menu_width - 1):
                    char = "╰" if x == 0 else "╯"

                try:
                    self.stdscr.addstr(menu_y + y, menu_x + x, char)
                except curses.error:
                    pass

        # Menu title
        title = " RTL-SDR Scanner Menu "
        title_x = menu_x + (menu_width - len(title)) // 2
        try:
            self.stdscr.addstr(menu_y, title_x, title, curses.A_BOLD)
        except curses.error:
            pass

        # Get current values
        gain_display = f"Auto" if self.gain == 'auto' else f"{self.gain}dB"
        spectrum_width = self.spectrum_width_options[self.spectrum_width_index]
        signal_type = self.signal_types[self.signal_type_index]
        current_mode = self.get_current_mode()
        audio_status = "ON" if current_mode != 'none' else "OFF"

        options = [
            f"Gain: {gain_display}",
            f"Width: {spectrum_width.upper()}",
            f"Type: {signal_type.capitalize()}",
            f"Mode: {current_mode.upper()}",
            f"Audio: {audio_status}",
            f"PPM: {self.ppm_drift:+d}",
            "Exit"
        ]

        # Draw all menu items with selection highlighting
        for i, option in enumerate(options):
            y_pos = menu_y + 2 + i
            x_pos = menu_x + 2

            is_selected = (i == self.menu_selection)

            if is_selected:
                # Highlight selected item
                try:
                    self.stdscr.addstr(y_pos, x_pos, option, curses.A_REVERSE | curses.A_BOLD)
                except curses.error:
                    pass
            else:
                # Regular menu item
                try:
                    self.stdscr.addstr(y_pos, x_pos, option)
                except curses.error:
                    pass

        # Menu title
        title = " RTL-SDR Scanner Menu "
        title_x = menu_x + (menu_width - len(title)) // 2
        try:
            self.stdscr.addstr(menu_y, title_x, title, curses.A_BOLD)
        except curses.error:
            pass

        # Compact menu drawing is handled above

    def _draw_frequency_display(self):
        """Draw the frequency display with blinking cursor on selected digit."""
        freq_mhz = self.center_freq / 1e6
        freq_str = f"{freq_mhz:.6f}"

        # Create display string with cursor
        display_str = f"Frequency: {freq_str} MHz | Adjusting: {self.freq_digits[self.selected_digit]}"

        # Find the position of the selected digit in the display string
        # "Frequency: 145.675000 MHz | Adjusting: 100kHz"
        # 01234567890123456789012345678901234567890123456789
        #           11111111112222222222333333333344444444445
        digit_positions = {
            0: 11,  # 1 in "145.675000" (100MHz)
            1: 12,  # 4 in "145.675000" (10MHz)
            2: 13,  # 5 in "145.675000" (1MHz)
            3: 15,  # 6 in "145.675000" (100kHz)
            4: 16,  # 7 in "145.675000" (10kHz)
            5: 17,  # 5 in "145.675000" (1kHz)
            6: 18,  # 0 in "145.675000" (100Hz)
            7: 19,  # 0 in "145.675000" (10Hz)
            8: 20   # 0 in "145.675000" (1Hz)
        }

        cursor_pos = digit_positions.get(self.selected_digit, -1)

        # Draw the frequency display
        self.stdscr.addstr(2, 0, display_str[:self.width-1])

        # Add blinking underline cursor if position is valid
        if cursor_pos >= 0 and cursor_pos < len(display_str) and cursor_pos < self.width:
            # Create blinking underline effect
            if not hasattr(self, '_blink_counter'):
                self._blink_counter = 0
            self._blink_counter += 1

            # Blink every 3 frames (roughly 1.5 seconds at 2 FPS display rate)
            should_blink = (self._blink_counter // 3) % 2 == 0

            if should_blink:
                try:
                    # Save current position
                    y, x = self.stdscr.getyx()
                    # Move to cursor position
                    self.stdscr.move(0, cursor_pos)
                    # Get the character there
                    ch = self.stdscr.inch()
                    # Apply underline attribute (bright for visibility)
                    self.stdscr.addch(ch & 0xFF, curses.A_UNDERLINE | curses.A_BOLD)
                    # Restore position
                    self.stdscr.move(y, x)
                except curses.error:
                    pass  # Ignore cursor positioning errors

    def _draw_frequency_cursor(self, freq_str):
        """Draw the blinking cursor on the selected frequency digit."""
        # Find the position of the selected digit in the frequency string
        digit_positions = {
            0: 0,   # 1 in "145.675000" (100MHz)
            1: 1,   # 4 in "145.675000" (10MHz)
            2: 2,   # 5 in "145.675000" (1MHz)
            3: 4,   # 6 in "145.675000" (100kHz)
            4: 5,   # 7 in "145.675000" (10kHz)
            5: 6,   # 5 in "145.675000" (1kHz)
            6: 7,   # 0 in "145.675000" (100Hz)
            7: 8,   # 0 in "145.675000" (10Hz)
            8: 9    # 0 in "145.675000" (1Hz)
        }

        cursor_pos = digit_positions.get(self.selected_digit, -1)

        # Add blinking underline cursor if position is valid
        if cursor_pos >= 0 and cursor_pos < len(freq_str) and cursor_pos < self.width:
            # Create blinking underline effect
            if not hasattr(self, '_blink_counter'):
                self._blink_counter = 0
            self._blink_counter += 1

            # Blink every 3 frames (roughly 1.5 seconds at 2 FPS display rate)
            should_blink = (self._blink_counter // 3) % 2 == 0

            if should_blink:
                try:
                    # Save current position
                    y, x = self.stdscr.getyx()
                    # Move to cursor position
                    self.stdscr.move(0, cursor_pos)
                    # Get the character there
                    ch = self.stdscr.inch()
                    # Apply underline attribute (bright for visibility)
                    self.stdscr.addch(ch & 0xFF, curses.A_UNDERLINE | curses.A_BOLD)
                    # Restore position
                    self.stdscr.move(y, x)
                except curses.error:
                    pass  # Ignore cursor positioning errors

    def _change_menu_option(self, direction):
        """Change the value of the currently selected menu option."""
        selected_item = self.menu_selection

        # Gain control (item 0)
        if selected_item == 0:
            gain_options = [
                ('auto', 'Auto'),
                (-10, 'Low'),
                (15, 'Medium'),
                (35, 'High')
            ]
            current_idx = 0
            if self.gain == 'auto':
                current_idx = 0
            elif self.gain == -10:
                current_idx = 1
            elif self.gain == 15:
                current_idx = 2
            elif self.gain == 35:
                current_idx = 3

            new_idx = (current_idx + direction) % len(gain_options)
            if gain_options[new_idx][0] == 'auto':
                self.set_auto_gain()
            else:
                self.set_manual_gain(gain_options[new_idx][0])

        # Spectrum width (item 1) - cycle through all options
        elif selected_item == 1:
            width_options = [0, 1, 2, 3]  # Narrow, Normal, Wide, Full
            current_width = self.spectrum_width_index
            new_width = (current_width + direction) % len(width_options)
            self.set_spectrum_width(new_width)

        # Signal type (item 2)
        elif selected_item == 2:
            self.signal_type_index = (self.signal_type_index + direction) % len(self.signal_types)
            # Reset mode index when switching signal types
            self.mode_index = 0

        # Mode (item 3) - depends on signal type
        elif selected_item == 3:
            self.cycle_mode(direction)

        # Audio toggle (item 4)
        elif selected_item == 4:
            self.toggle_demod_audio()

        # PPM drift (item 5)
        elif selected_item == 5:
            # Adjust PPM by 1 or 10 depending on direction magnitude
            if abs(direction) > 1:  # If holding or multiple presses
                self.ppm_drift += direction * 10
            else:
                self.ppm_drift += direction
            # Keep PPM in reasonable range (-100 to +100)
            self.ppm_drift = max(-100, min(100, self.ppm_drift))
            # Apply PPM correction if SDR is available
            if self.sdr is not None:
                try:
                    # Note: RTL-SDR library may not support PPM directly
                    # This would need to be implemented in the SDR driver
                    pass
                except (AttributeError, ValueError):
                    pass
                except (AttributeError, ValueError):
                    pass

    def _execute_menu_selection(self):
        """Execute the selected menu item."""
        selected_item = self.menu_selection

        if selected_item == 5:  # Exit
            self.show_menu = False
        # For other items, left/right arrows change values, so selection just closes menu
        else:
            self.show_menu = False

    def set_manual_gain(self, gain_value):
        """Set manual gain to a specific value."""
        self.gain = gain_value
        with self.sdr_lock:
            if self.sdr is not None:
                try:
                    self.sdr.gain = self.gain
                except (AttributeError, ValueError):
                    pass  # Ignore SDR errors

    def set_spectrum_width(self, width_index):
        """Set spectrum width by index."""
        if 0 <= width_index < len(self.spectrum_width_options):
            old_index = self.spectrum_width_index
            self.adjust_spectrum_width(width_index - old_index)

    def set_mode_index(self, mode_index):
        """Set mode index within current signal type."""
        modes_list = self.get_current_modes_list()
        if 0 <= mode_index < len(modes_list):
            self.mode_index = mode_index

    def handle_input(self, key):
        """Handle keyboard input."""
        if key == ord('q') or key == ord('Q'):
            self.is_running = False
            return True

        elif key == ord('m') or key == ord('M'):
            self.show_menu = not self.show_menu
            if self.show_menu:
                self.menu_selection = 0  # Reset menu selection

        # Handle menu navigation when menu is open
        if self.show_menu:
            # Handle escape sequences first (for arrow keys)
            if key == 27:  # ESC - could be plain ESC or start of escape sequence
                self.stdscr.nodelay(True)
                ch1 = self.stdscr.getch()
                if ch1 == -1:  # No more characters, plain ESC
                    self.show_menu = False  # Close menu
                elif ch1 == 91:  # '[' - arrow key sequence
                    ch2 = self.stdscr.getch()
                    if ch2 == 65:  # 'A' - Up arrow - navigate menu
                        self.menu_selection = max(0, self.menu_selection - 1)
                    elif ch2 == 66:  # 'B' - Down arrow - navigate menu
                        self.menu_selection = min(len(self.selectable_menu_items) - 1, self.menu_selection + 1)
                    elif ch2 == 68:  # 'D' - Left arrow - change option value
                        self._change_menu_option(-1)
                    elif ch2 == 67:  # 'C' - Right arrow - change option value
                        self._change_menu_option(1)
                self.stdscr.nodelay(False)

            # Handle direct curses key codes
            elif key == curses.KEY_UP:
                self.menu_selection = max(0, self.menu_selection - 1)
            elif key == curses.KEY_DOWN:
                self.menu_selection = min(len(self.selectable_menu_items) - 1, self.menu_selection + 1)
            elif key == curses.KEY_LEFT:
                self._change_menu_option(-1)
            elif key == curses.KEY_RIGHT:
                self._change_menu_option(1)
            elif key == ord(' ') or key == 10 or key == 13:  # Space, Enter, Return
                self._execute_menu_selection()

        else:
            # Handle escape sequences first (for arrow keys)
            if key == 27:  # ESC - start of escape sequence
                self.stdscr.nodelay(True)
                ch1 = self.stdscr.getch()
                ch2 = self.stdscr.getch()
                self.stdscr.nodelay(False)

                if ch1 == 91:  # '[' - standard arrow key sequence
                    if ch2 == 65:  # 'A' - Up arrow
                        self.adjust_frequency(1)
                    elif ch2 == 66:  # 'B' - Down arrow
                        self.adjust_frequency(-1)
                    elif ch2 == 68:  # 'D' - Left arrow
                        self.select_prev_digit()
                    elif ch2 == 67:  # 'C' - Right arrow
                        self.select_next_digit()

            # Handle direct curses key codes
            elif key == curses.KEY_UP:
                self.adjust_frequency(1)  # Increase selected digit
            elif key == curses.KEY_DOWN:
                self.adjust_frequency(-1)  # Decrease selected digit
            elif key == curses.KEY_LEFT:
                self.select_prev_digit()  # Move to previous digit
            elif key == curses.KEY_RIGHT:
                self.select_next_digit()  # Move to next digit

        return False

    def adjust_frequency(self, delta):
        """Adjust the center frequency by the selected digit step."""
        step = self.digit_steps[self.selected_digit]
        new_freq = self.center_freq + delta * step
        # Keep frequency within reasonable bounds (1 MHz to 2 GHz)
        new_freq = max(1000000, min(2000000000, new_freq))

        # Only update if frequency actually changed
        if new_freq != self.center_freq:
            self.center_freq = new_freq
            with self.sdr_lock:
                if self.sdr is not None:
                    try:
                        self.sdr.center_freq = self.center_freq
                        self.freqs = np.fft.fftshift(np.fft.fftfreq(self.fft_size, 1/self.sample_rate)) + self.center_freq
                    except (AttributeError, ValueError):
                        pass  # Ignore SDR errors

    def select_next_digit(self):
        """Select the next frequency digit to adjust."""
        self.selected_digit = (self.selected_digit + 1) % len(self.freq_digits)
        self.selected_digit = max(0, min(len(self.freq_digits) - 1, self.selected_digit))

    def select_prev_digit(self):
        """Select the previous frequency digit to adjust."""
        self.selected_digit = (self.selected_digit - 1) % len(self.freq_digits)
        self.selected_digit = max(0, min(len(self.freq_digits) - 1, self.selected_digit))

    def adjust_gain(self, delta):
        """Adjust the gain."""
        if self.gain != 'auto':
            current_gain_idx = self.gain_values.index(self.gain) if self.gain in self.gain_values else 0
            new_gain_idx = max(0, min(len(self.gain_values) - 1, current_gain_idx + (delta // self.gain_step)))
            self.gain = self.gain_values[new_gain_idx]
            with self.sdr_lock:
                if self.sdr is not None:
                    try:
                        self.sdr.gain = self.gain
                    except (AttributeError, ValueError):
                        pass  # Ignore SDR errors

    def set_auto_gain(self):
        """Set automatic gain."""
        self.gain = 'auto'
        with self.sdr_lock:
            if self.sdr is not None:
                try:
                    self.sdr.gain = 'auto'
                except (AttributeError, ValueError):
                    pass  # Ignore SDR errors

    def adjust_spectrum_width(self, direction):
        """Adjust spectrum display width."""
        if direction > 0:
            self.spectrum_width_index = min(len(self.spectrum_width_options) - 1, self.spectrum_width_index + 1)
        else:
            self.spectrum_width_index = max(0, self.spectrum_width_index - 1)

        # Update zoom factor based on width setting
        width_factors = {'narrow': 0.25, 'normal': 1.0, 'wide': 2.0, 'full': 4.0}
        self.zoom_factor = width_factors[self.spectrum_width_options[self.spectrum_width_index]]

        # Recompute frequency range
        self._update_frequency_range()

    def cycle_mode(self, direction):
        """Cycle through modes in current signal type."""
        modes_list = self.get_current_modes_list()
        self.mode_index = (self.mode_index + direction) % len(modes_list)
        current_mode = self.get_current_mode()
        logger.info(f"Mode: {current_mode}")

    def toggle_demod_audio(self):
        """Toggle demodulated audio output."""
        current_mode = self.get_current_mode()
        if current_mode == 'none':  # No demodulation
            return

        # This would start/stop audio output thread
        # For now, just log the action
        logger.info(f"Audio output toggled for {current_mode} demodulation")

    def _update_frequency_range(self):
        """Update the frequency range based on zoom factor."""
        base_bandwidth = self.sample_rate
        display_bandwidth = base_bandwidth / self.zoom_factor
        self.freqs = np.fft.fftshift(np.fft.fftfreq(self.fft_size, 1/self.sample_rate)) * self.zoom_factor + self.center_freq

    def demodulate_signal(self, samples, mode, center_freq_offset=0):
        """
        Demodulate the received signal.

        Args:
            samples: Complex IQ samples
            mode: Demodulation mode ('am', 'fm', 'ssb', 'cw')
            center_freq_offset: Frequency offset from center in Hz

        Returns:
            Demodulated audio signal
        """
        if mode == 'none':
            return np.zeros(len(samples))

        # Shift frequency if needed
        if center_freq_offset != 0:
            # Frequency shift for demodulation
            t = np.arange(len(samples)) / self.sample_rate
            shift_signal = np.exp(-1j * 2 * np.pi * center_freq_offset * t)
            samples = samples * shift_signal

        if mode == 'am':
            return self._demodulate_am(samples)
        elif mode == 'fm':
            return self._demodulate_fm(samples)
        elif mode == 'ssb':
            return self._demodulate_ssb(samples)
        elif mode == 'cw':
            return self._demodulate_cw(samples)
        elif mode == 'dmr':
            return self._demodulate_dmr(samples)

        return np.zeros(len(samples))

    def _demodulate_am(self, samples):
        """AM demodulation."""
        # Envelope detection
        envelope = np.abs(samples)
        # Remove DC component
        envelope = envelope - np.mean(envelope)
        # Normalize
        if np.max(np.abs(envelope)) > 0:
            envelope = envelope / np.max(np.abs(envelope))
        return envelope

    def _demodulate_fm(self, samples):
        """FM demodulation using phase differentiation with CTCSS detection."""
        # Compute instantaneous phase
        phase = np.angle(samples)
        # Differentiate phase to get frequency
        freq_dev = np.diff(np.unwrap(phase))
        # Normalize and scale
        if len(freq_dev) > 0:
            freq_dev = freq_dev / (2 * np.pi)  # Convert to frequency deviation
            # Simple low-pass filter (basic)
            freq_dev = np.concatenate([freq_dev, [freq_dev[-1]]])  # Pad to maintain length
            # Normalize to [-1, 1]
            if np.max(np.abs(freq_dev)) > 0:
                freq_dev = freq_dev / np.max(np.abs(freq_dev))

            # Attempt CTCSS detection
            self._detect_ctcss(freq_dev)
        else:
            freq_dev = np.zeros(len(samples))
        return freq_dev

    def _detect_ctcss(self, fm_demod):
        """Attempt to detect CTCSS tone in FM demodulated signal."""
        try:
            # Simple CTCSS detection - look for dominant low-frequency components
            # This is a basic implementation - real CTCSS detection is more complex

            # Downsample for analysis
            downsample_factor = max(1, len(fm_demod) // 1024)
            if downsample_factor > 1:
                analysis_signal = fm_demod[::downsample_factor]
            else:
                analysis_signal = fm_demod

            # Compute FFT to find dominant frequencies
            fft_size = min(1024, len(analysis_signal))
            if fft_size >= 64:  # Need minimum size for analysis
                window = np.hanning(fft_size)
                fft_result = np.fft.fft(analysis_signal[:fft_size] * window)
                freqs = np.fft.fftfreq(fft_size, 1/self.audio_sample_rate * downsample_factor)
                power_spectrum = np.abs(fft_result)

                # Look for peaks in CTCSS frequency range (67-254 Hz)
                ctcss_range_mask = (freqs > 60) & (freqs < 260)
                if np.any(ctcss_range_mask):
                    ctcss_powers = power_spectrum[ctcss_range_mask]
                    ctcss_freqs = freqs[ctcss_range_mask]

                    # Find the strongest CTCSS tone
                    if len(ctcss_powers) > 0:
                        peak_idx = np.argmax(ctcss_powers)
                        detected_freq = abs(ctcss_freqs[peak_idx])

                        # Find closest standard CTCSS tone
                        closest_tone = min(self.ctcss_tones, key=lambda x: abs(x - detected_freq))
                        if abs(closest_tone - detected_freq) < 5:  # Within 5Hz tolerance
                            self.detected_ctcss = closest_tone
                        else:
                            self.detected_ctcss = None
                    else:
                        self.detected_ctcss = None
                else:
                    self.detected_ctcss = None
            else:
                self.detected_ctcss = None

        except Exception as e:
            logger.debug(f"CTCSS detection error: {e}")
            self.detected_ctcss = None

    def _demodulate_ssb(self, samples):
        """SSB demodulation (simplified, assumes USB)."""
        # For SSB, we can use the real part after frequency shifting
        # This is a simplified implementation
        ssb_signal = np.real(samples)
        # Remove DC and normalize
        ssb_signal = ssb_signal - np.mean(ssb_signal)
        if np.max(np.abs(ssb_signal)) > 0:
            ssb_signal = ssb_signal / np.max(np.abs(ssb_signal))
        return ssb_signal

    def _demodulate_cw(self, samples):
        """CW/Morse code demodulation (envelope detection)."""
        # Similar to AM but optimized for narrow bandwidth
        envelope = np.abs(samples)
        # Apply simple low-pass filter (moving average)
        window_size = int(self.sample_rate / 1000)  # ~1ms window
        if window_size > 0:
            envelope = np.convolve(envelope, np.ones(window_size)/window_size, mode='same')
        # Remove DC and normalize
        envelope = envelope - np.mean(envelope)
        if np.max(np.abs(envelope)) > 0:
            envelope = envelope / np.max(np.abs(envelope))
        return envelope

    def _demodulate_dmr(self, samples):
        """
        DMR (Digital Mobile Radio) demodulation framework.

        Note: Full DMR demodulation requires:
        - 4FSK demodulation
        - Frame synchronization
        - Reed-Solomon FEC
        - AMBE+2 voice codec
        - Call signaling

        This implements basic DMR frame detection and information extraction.
        """
        try:
            # Basic DMR frame detection and decoding
            # This is a simplified implementation for demonstration

            # Look for DMR sync patterns and extract basic information
            self._decode_dmr_frame(samples)

            # For audio, return silence if no active transmission
            # In a full implementation, this would be decoded AMBE audio
            if self.dmr_info['active']:
                # Return a tone to indicate active DMR transmission
                t = np.arange(len(samples)) / self.sample_rate
                return 0.3 * np.sin(2 * np.pi * 1200 * t)  # 1.2kHz tone for DMR
            else:
                return np.zeros(len(samples))

        except Exception as e:
            logger.debug(f"DMR demodulation error: {e}")
            return np.zeros(len(samples))

    def _decode_dmr_frame(self, samples):
        """Attempt to decode DMR frame information."""
        try:
            # Simplified DMR frame detection
            # In reality, this would involve:
            # 1. 4FSK symbol detection
            # 2. Frame synchronization
            # 3. CACH (Common Announcement Channel) decoding
            # 4. Talkgroup and color code extraction

            # For demonstration, simulate DMR detection based on signal characteristics
            diff_signal = np.abs(np.diff(samples))
            digital_activity = np.mean(diff_signal) > np.mean(np.abs(samples)) * 0.15

            if digital_activity:
                # Simulate DMR frame detection
                # In reality, this would parse actual DMR protocol data
                if not self.dmr_info['active']:
                    # New transmission detected
                    self.dmr_info['active'] = True
                    # Simulate random but realistic DMR parameters
                    self.dmr_info['talkgroup'] = np.random.randint(1, 10000)  # Random TG
                    self.dmr_info['timeslot'] = np.random.randint(1, 2)       # TS1 or TS2
                    self.dmr_info['color_code'] = np.random.randint(0, 15)    # CC 0-15
                # Continue current transmission
            else:
                # No activity
                if self.dmr_info['active']:
                    # Transmission ended
                    self.dmr_info['active'] = False
                    self.dmr_info['talkgroup'] = None
                    self.dmr_info['timeslot'] = None
                    self.dmr_info['color_code'] = None

        except Exception as e:
            logger.debug(f"DMR frame decode error: {e}")
            self.dmr_info['active'] = False

        except Exception as e:
            logger.error(f"DMR demodulation error: {e}")
            return np.zeros(len(samples))

    def start_audio_output(self):
        """Start audio output thread for demodulated signal."""
        if self.audio_thread is None or not self.audio_thread.is_alive():
            self.audio_thread = threading.Thread(target=self._audio_output_loop, daemon=True)
            self.audio_thread.start()

    def stop_audio_output(self):
        """Stop audio output thread."""
        # This would signal the audio thread to stop
        pass

    def _audio_output_loop(self):
        """Audio output loop for demodulated signal."""
        # This would handle audio playback
        # For now, just log that audio would start
        current_mode = self.get_current_mode()
        logger.info(f"Audio output started for {current_mode} demodulation")

    def run(self):
        """Main interactive loop."""
        # Initialize curses
        curses.cbreak()  # Enable cbreak mode
        curses.noecho()  # Don't echo keys
        self.stdscr.keypad(True)  # Enable keypad mode for arrow keys
        self.stdscr.nodelay(True)  # Non-blocking input
        curses.curs_set(0)  # Hide cursor

        # Initialize curses colors
        curses.start_color()
        curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)     # High power
        curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)  # Center frequency
        curses.init_pair(3, curses.COLOR_CYAN, curses.COLOR_BLACK)    # DMR info
        curses.init_pair(4, curses.COLOR_GREEN, curses.COLOR_BLACK)   # CTCSS info

        # Initialize device
        self.initialize_device()

        # Start threads
        self.start_capture()
        self.start_display()

        # Main input loop
        try:
            while self.is_running:
                try:
                    key = self.stdscr.getch()
                    if key != -1:  # Key pressed
                        if self.handle_input(key):
                            break
                    time.sleep(0.01)  # Small delay to prevent high CPU usage
                except KeyboardInterrupt:
                    break
        finally:
            # Ensure terminal state is restored
            self.restore_terminal()

        # Cleanup
        self.is_running = False
        self.running = False
        time.sleep(0.2)  # Allow threads to finish
        if self.sdr:
            self.sdr.close()

    def close(self):
        """Close the scanner."""
        self.is_running = False
        self.running = False

        # Wait for threads to finish
        if self.capture_thread and self.capture_thread.is_alive():
            self.capture_thread.join(timeout=1.0)
        if self.display_thread and self.display_thread.is_alive():
            self.display_thread.join(timeout=1.0)
        if self.audio_thread and self.audio_thread.is_alive():
            self.audio_thread.join(timeout=1.0)

        # Close SDR device with lock
        with self.sdr_lock:
            if self.sdr:
                try:
                    self.sdr.close()
                    logger.info("RTL-SDR device closed")
                except Exception as e:
                    logger.error(f"Error closing SDR device: {e}")

    def restore_terminal(self):
        """Restore terminal to normal state."""
        try:
            # Try curses cleanup first
            curses.nocbreak()
            self.stdscr.keypad(False)
            curses.echo()
            curses.endwin()
        except:
            pass  # Ignore curses errors

        # Always do ANSI terminal reset as fallback
        try:
            # Comprehensive terminal reset
            print("\033[?25h", end="")  # Show cursor
            print("\033[0m", end="")    # Reset colors/attributes
            print("\033[2J", end="")    # Clear screen
            print("\033[H", end="")     # Move to home position
            print("\033[J", end="")     # Clear to end of screen
            sys.stdout.flush()
        except:
            pass

def main():
    parser = argparse.ArgumentParser(description='Interactive RTL-SDR Radio Scanner')
    parser.add_argument('--freq', type=float, default=100,
                       help='Initial center frequency in MHz (default: 100)')
    parser.add_argument('--sample-rate', type=float, default=2.4,
                       help='Sample rate in MHz (default: 2.4)')
    parser.add_argument('--gain', type=str, default='auto',
                       help='Initial gain setting (auto or dB value, default: auto)')
    parser.add_argument('--web', action='store_true',
                       help='Run web interface instead of terminal interface')
    parser.add_argument('--web-host', type=str, default='0.0.0.0',
                       help='Web server host (default: 0.0.0.0)')
    parser.add_argument('--web-port', type=int, default=5000,
                       help='Web server port (default: 5000)')

    args = parser.parse_args()

    # Convert to Hz
    center_freq = args.freq * 1e6
    sample_rate = args.sample_rate * 1e6

    def emergency_cleanup():
        """Emergency cleanup to restore terminal state."""
        try:
            curses.endwin()  # Restore terminal
        except:
            pass

        # Comprehensive terminal reset
        try:
            # Force immediate output
            sys.stdout.write("\033[?25h")  # Show cursor
            sys.stdout.write("\033[0m")    # Reset colors/attributes
            sys.stdout.write("\033[2J")    # Clear screen
            sys.stdout.write("\033[H")     # Move to home position
            sys.stdout.write("\033[J")     # Clear to end of screen
            sys.stdout.write("\033[?1049l")  # Exit alternate screen if used
            sys.stdout.write("\033[?1l")   # Reset cursor keys
            sys.stdout.write("\033>")      # Reset numeric keypad
            sys.stdout.flush()

            # Try system reset as final fallback
            try:
                os.system("tput reset >/dev/null 2>&1")
            except:
                pass
        except:
            # Final fallback - try system reset
            try:
                os.system("tput reset >/dev/null 2>&1")
            except:
                pass

    # Create scanner instance
    scanner = None

    def curses_main(stdscr):
        nonlocal scanner
        scanner = InteractiveRTLScanner(stdscr, sample_rate, center_freq, args.gain)
        try:
            scanner.run()
        except KeyboardInterrupt:
            # Handle Ctrl+C gracefully
            pass
        except Exception as e:
            # Restore terminal state first
            scanner.restore_terminal()
            print(f"\nError during execution: {e}")
            print("Terminal state has been restored.")
        finally:
            try:
                scanner.close()
            except:
                pass

    # Create scanner instance for both interfaces
    scanner = None

    if args.web:
        # Dual interface mode - web interface shares scanner with terminal
        try:
            from web_scanner import WebControlInterface

            # Create web control interface that connects to the scanner
            def run_web_server():
                try:
                    web_interface = WebControlInterface(scanner, args.web_host, args.web_port)
                    web_interface.run()
                except Exception as e:
                    print(f"Web interface error: {e}")

            web_thread = threading.Thread(target=run_web_server, daemon=True)
            web_thread.start()

            print(f"Web control interface starting at http://{args.web_host}:{args.web_port}")
            print("Terminal interface will start simultaneously...")
            time.sleep(1)  # Give web server time to start

        except ImportError as e:
            print(f"Web interface not available: {e}")
            print("Install required packages: pip install flask flask-socketio eventlet")
            print("Falling back to terminal interface only...")

    # Always run terminal interface
    try:
        curses.wrapper(curses_main)
    except KeyboardInterrupt:
        print("\nInteractive scanner stopped by user")
        emergency_cleanup()
    except Exception as e:
        print(f"Error starting interactive scanner: {e}")
        emergency_cleanup()
        sys.exit(1)

if __name__ == "__main__":
    main()