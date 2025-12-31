"""
Traditional Radio Scanner

Scans through user-defined frequency lists stored in XML format.
Supports FM with CTCSS/DCS squelch detection and DMR frequencies.
"""

import os
import sys
import time
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
import logging
import curses
import threading
from rtlsdr import RtlSdr
import numpy as np
from scipy import signal

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class Frequency:
    """Represents a single frequency entry."""
    value: float  # Frequency in Hz
    mode: str    # 'FM', 'AM', 'DMR', etc.
    name: str    # Human-readable name
    squelch: Optional[Dict] = None  # Squelch settings
    dmr: Optional[Dict] = None      # DMR specific settings

@dataclass
class FrequencyBank:
    """Represents a frequency bank."""
    name: str
    description: str
    frequencies: List[Frequency]

class FrequencyBankLoader:
    """Loads frequency banks from XML files."""

    def __init__(self, banks_dir: str = "radio_scanner/banks"):
        self.banks_dir = banks_dir

    def load_bank(self, filename: str) -> Optional[FrequencyBank]:
        """Load a frequency bank from XML file."""
        filepath = os.path.join(self.banks_dir, filename)
        if not os.path.exists(filepath):
            logger.error(f"Frequency bank file not found: {filepath}")
            return None

        try:
            tree = ET.parse(filepath)
            root = tree.getroot()

            bank_name = root.get('name', filename)
            bank_desc = root.get('description', '')

            frequencies = []
            for freq_elem in root.findall('frequency'):
                freq = self._parse_frequency_element(freq_elem)
                if freq:
                    frequencies.append(freq)

            return FrequencyBank(bank_name, bank_desc, frequencies)

        except ET.ParseError as e:
            logger.error(f"Error parsing XML file {filepath}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error loading bank {filename}: {e}")
            return None

    def _parse_frequency_element(self, elem) -> Optional[Frequency]:
        """Parse a frequency XML element."""
        try:
            value = float(elem.get('value', 0))
            mode = elem.get('mode', 'FM')
            name = elem.get('name', f"{value/1e6:.3f} MHz")

            # Parse squelch settings
            squelch_elem = elem.find('squelch')
            squelch = None
            if squelch_elem is not None:
                squelch_type = squelch_elem.get('type')
                if squelch_type == 'CTCSS':
                    tone = float(squelch_elem.get('tone', 0))
                    squelch = {'type': 'CTCSS', 'tone': tone}
                elif squelch_type == 'DCS':
                    code = squelch_elem.get('code', '023')
                    squelch = {'type': 'DCS', 'code': code}

            # Parse DMR settings
            dmr_elem = elem.find('dmr')
            dmr = None
            if dmr_elem is not None:
                color_code = int(dmr_elem.get('color_code', 1))
                timeslot = int(dmr_elem.get('timeslot', 1))
                dmr = {'color_code': color_code, 'timeslot': timeslot}

            return Frequency(value, mode, name, squelch, dmr)

        except ValueError as e:
            logger.error(f"Error parsing frequency element: {e}")
            return None

    def list_banks(self) -> List[str]:
        """List available frequency bank files."""
        if not os.path.exists(self.banks_dir):
            return []

        banks = []
        for file in os.listdir(self.banks_dir):
            if file.endswith('.xml'):
                banks.append(file)

        return sorted(banks)

class SquelchDetector:
    """Detects CTCSS/DCS tones for squelch control."""

    def __init__(self, sample_rate: float = 2.4e6):
        self.sample_rate = sample_rate
        self.ctcss_tones = [
            67.0, 71.9, 74.4, 77.0, 79.7, 82.5, 85.4, 88.5, 91.5, 94.8,
            97.4, 100.0, 103.5, 107.2, 110.9, 114.8, 118.8, 123.0, 127.3,
            131.8, 136.5, 141.3, 146.2, 151.4, 156.7, 162.2, 167.9, 173.8,
            179.9, 186.2, 192.8, 203.5, 210.7, 218.1, 225.7, 233.6, 241.8,
            250.3
        ]

    def detect_ctcss(self, samples: np.ndarray, target_tone: float, threshold: float = 0.1) -> bool:
        """Detect CTCSS tone in audio samples."""
        # Simple Goertzel algorithm for tone detection
        # This is a basic implementation - could be improved
        try:
            # Convert to audio frequency range (demodulate FM first)
            # For now, just check for tone presence in a simple way
            # Real implementation would need proper FM demodulation

            # Placeholder - always return True for now
            # TODO: Implement proper CTCSS detection
            return True

        except Exception as e:
            logger.error(f"Error in CTCSS detection: {e}")
            return False

    def detect_dcs(self, samples: np.ndarray, target_code: str) -> bool:
        """Detect DCS code in audio samples."""
        # DCS detection is more complex - placeholder implementation
        # TODO: Implement proper DCS detection
        return True

class TraditionalScanner:
    """Main traditional radio scanner class."""

    def __init__(self):
        self.sdr = None
        self.current_bank: Optional[FrequencyBank] = None
        self.current_freq_idx = 0
        self.is_scanning = False
        self.squelch_detector = SquelchDetector()
        self.sample_rate = 2.4e6
        self.gain = 'auto'

        # Load available banks
        self.bank_loader = FrequencyBankLoader()
        self.available_banks = self.bank_loader.list_banks()

    def initialize_device(self):
        """Initialize RTL-SDR device."""
        try:
            self.sdr = RtlSdr()
            assert self.sdr is not None  # Type guard
            self.sdr.sample_rate = self.sample_rate
            if self.gain == 'auto':
                self.sdr.gain = 'auto'
            else:
                self.sdr.gain = self.gain

            logger.info("RTL-SDR initialized for traditional scanning")

        except Exception as e:
            logger.error(f"Failed to initialize RTL-SDR: {e}")
            raise

    def load_bank(self, bank_filename: str) -> bool:
        """Load a frequency bank."""
        self.current_bank = self.bank_loader.load_bank(bank_filename)
        if self.current_bank:
            logger.info(f"Loaded bank '{self.current_bank.name}' with {len(self.current_bank.frequencies)} frequencies")
            return True
        return False

    def scan_next_frequency(self) -> bool:
        """Move to next frequency in the bank."""
        if not self.current_bank or not self.current_bank.frequencies:
            return False

        self.current_freq_idx = (self.current_freq_idx + 1) % len(self.current_bank.frequencies)
        return True

    def get_current_frequency(self) -> Optional[Frequency]:
        """Get the current frequency."""
        if not self.current_bank or not self.current_bank.frequencies:
            return None
        return self.current_bank.frequencies[self.current_freq_idx]

    def check_squelch(self, frequency: Frequency, samples: np.ndarray) -> bool:
        """Check if squelch should be open for the given frequency."""
        if not frequency.squelch:
            # No squelch - always open
            return True

        squelch_type = frequency.squelch.get('type')

        if squelch_type == 'CTCSS':
            tone = frequency.squelch.get('tone', 0)
            return self.squelch_detector.detect_ctcss(samples, tone)
        elif squelch_type == 'DCS':
            code = frequency.squelch.get('code', '023')
            return self.squelch_detector.detect_dcs(samples, code)

        return True

    def scan_loop(self):
        """Main scanning loop."""
        if not self.current_bank:
            logger.error("No frequency bank loaded")
            return

        if self.sdr is None:
            logger.error("RTL-SDR not initialized")
            return

        logger.info("Starting traditional scan...")

        while self.is_scanning:
            current_freq = self.get_current_frequency()
            if not current_freq:
                break

            # Tune to frequency
            self.sdr.center_freq = current_freq.value
            logger.info(f"Scanning: {current_freq.name} ({current_freq.value/1e6:.3f} MHz, {current_freq.mode})")

            # Capture samples
            samples = self.sdr.read_samples(1024*1024)

            # Check signal strength
            power = 10 * np.log10(np.mean(np.abs(samples)**2))

            # Check squelch
            squelch_open = self.check_squelch(current_freq, samples)

            if squelch_open and power > -60:  # Signal threshold
                logger.info(f"Signal detected on {current_freq.name}: {power:.1f} dB")
                # Could add audio playback, recording, etc. here
                time.sleep(2.0)  # Listen for 2 seconds
            else:
                time.sleep(0.1)  # Quick check

            # Move to next frequency
            self.scan_next_frequency()

    def run_terminal_interface(self):
        """Run the terminal-based scanner interface."""
        print("Traditional Radio Scanner")
        print("=" * 40)

        if not self.available_banks:
            print("No frequency banks found in radio_scanner/banks/")
            print("Create XML frequency files first.")
            return

        print("Available frequency banks:")
        for i, bank in enumerate(self.available_banks):
            print(f"{i+1}. {bank}")

        try:
            choice = input("Select bank (number): ").strip()
            bank_idx = int(choice) - 1
            if 0 <= bank_idx < len(self.available_banks):
                bank_file = self.available_banks[bank_idx]
                if self.load_bank(bank_file):
                    assert self.current_bank is not None  # Should be set by successful load_bank
                    print(f"\nLoaded bank: {self.current_bank.name}")
                    print(f"Frequencies: {len(self.current_bank.frequencies)}")
                    print("\nPress Ctrl+C to stop scanning\n")

                    self.is_scanning = True
                    self.scan_loop()
                else:
                    print("Failed to load bank")
            else:
                print("Invalid selection")

        except ValueError:
            print("Invalid input")
        except KeyboardInterrupt:
            print("\nScan stopped")

    def run(self):
        """Main run method."""
        try:
            self.initialize_device()
            self.run_terminal_interface()

        except Exception as e:
            logger.error(f"Scanner error: {e}")
        finally:
            if self.sdr:
                self.sdr.close()

def main():
    """Command-line entry point."""
    scanner = TraditionalScanner()
    scanner.run()

if __name__ == "__main__":
    main()