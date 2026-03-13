#!/usr/bin/env python3
"""
Traditional Radio Scanner

Scans through user-defined frequency lists stored in XML format.
Supports FM and AM demodulation with audio output.
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

# Try to import audio libraries
try:
    import sounddevice as sd
    SOUNDDEVICE_AVAILABLE = True
except ImportError:
    sd = None
    SOUNDDEVICE_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class Frequency:
    """Represents a single frequency entry."""
    value: float  # Frequency in Hz
    mode: str    # 'FM', 'AM', etc.
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

    def __init__(self, banks_dir: str = None):
        if banks_dir is None:
            # Get path relative to this script
            script_dir = os.path.dirname(os.path.abspath(__file__))
            self.banks_dir = os.path.join(script_dir, "banks")
        else:
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

            return Frequency(value, mode, name, squelch)

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

class Demodulator:
    """Handles radio signal demodulation."""
    
    def __init__(self, sample_rate: float, audio_rate: int = 48000):
        self.sample_rate = sample_rate
        self.audio_rate = audio_rate
        self.downsample_factor = int(sample_rate / audio_rate)
        
    def demodulate_fm(self, samples: np.ndarray) -> np.ndarray:
        """Demodulate FM signal."""
        # FM Demodulation: derivative of the phase
        phase_diff = np.angle(samples[1:] * np.conj(samples[:-1]))
        
        # Low-pass filter and decimate
        audio = signal.decimate(phase_diff, self.downsample_factor, ftype='fir')
        
        # Normalize and scale
        if np.max(np.abs(audio)) > 0:
            audio = audio / np.max(np.abs(audio)) * 0.5
            
        return audio.astype(np.float32)

    def demodulate_am(self, samples: np.ndarray) -> np.ndarray:
        """Demodulate AM signal."""
        # AM Demodulation: envelope detection (absolute value)
        envelope = np.abs(samples)
        
        # Remove DC offset
        audio = envelope - np.mean(envelope)
        
        # Low-pass filter and decimate
        audio = signal.decimate(audio, self.downsample_factor, ftype='fir')
        
        # Normalize
        if np.max(np.abs(audio)) > 0:
            audio = audio / np.max(np.abs(audio)) * 0.5
            
        return audio.astype(np.float32)

class TraditionalScanner:
    """Main traditional radio scanner class."""

    def __init__(self):
        self.sdr = None
        self.current_bank: Optional[FrequencyBank] = None
        self.current_freq_idx = 0
        self.is_scanning = False
        self.sample_rate = 1.2e6  # Reduced sample rate for better performance
        self.audio_rate = 48000
        self.gain = 'auto'
        self.demodulator = Demodulator(self.sample_rate, self.audio_rate)
        self.audio_stream = None
        self.squelch_threshold = -45  # dB

        # Load available banks
        self.bank_loader = FrequencyBankLoader()
        self.available_banks = self.bank_loader.list_banks()

    def initialize_device(self):
        """Initialize RTL-SDR device."""
        try:
            self.sdr = RtlSdr()
            self.sdr.sample_rate = self.sample_rate
            self.sdr.gain = self.gain
            logger.info(f"RTL-SDR initialized: {self.sample_rate/1e6} MHz SR, Gain: {self.gain}")
        except Exception as e:
            logger.error(f"Failed to initialize RTL-SDR: {e}")
            raise

    def initialize_audio(self):
        """Initialize audio output."""
        if SOUNDDEVICE_AVAILABLE:
            try:
                self.audio_stream = sd.OutputStream(
                    samplerate=self.audio_rate,
                    channels=1,
                    dtype='float32'
                )
                self.audio_stream.start()
                logger.info(f"Audio output started at {self.audio_rate} Hz")
            except Exception as e:
                logger.error(f"Failed to initialize audio: {e}")
                self.audio_stream = None

    def load_bank(self, bank_filename: str) -> bool:
        """Load a frequency bank."""
        self.current_bank = self.bank_loader.load_bank(bank_filename)
        return self.current_bank is not None

    def scan_next_frequency(self):
        """Move to next frequency."""
        if self.current_bank and self.current_bank.frequencies:
            self.current_freq_idx = (self.current_freq_idx + 1) % len(self.current_bank.frequencies)

    def get_current_frequency(self) -> Optional[Frequency]:
        """Get current frequency object."""
        if self.current_bank and 0 <= self.current_freq_idx < len(self.current_bank.frequencies):
            return self.current_bank.frequencies[self.current_freq_idx]
        return None

    def scan_loop(self):
        """Main scanning loop with audio output."""
        if not self.current_bank or self.sdr is None:
            return

        self.initialize_audio()
        logger.info("Scanning... Press Ctrl+C to stop.")

        while self.is_scanning:
            current_freq = self.get_current_frequency()
            if not current_freq: break

            # Tune and check signal
            self.sdr.center_freq = current_freq.value
            time.sleep(0.05)  # Wait for tuner to settle
            
            # Read a small chunk to check power
            samples = self.sdr.read_samples(64*1024)
            power = 10 * np.log10(np.mean(np.abs(samples)**2))

            if power > self.squelch_threshold:
                logger.info(f"Signal on {current_freq.name} ({current_freq.value/1e6:.3f} MHz): {power:.1f} dB")
                
                # Signal detected: stop scanning and play audio
                while self.is_scanning:
                    samples = self.sdr.read_samples(128*1024)
                    power = 10 * np.log10(np.mean(np.abs(samples)**2))
                    
                    if power < self.squelch_threshold - 5: # Hysteresis
                        logger.info("Signal lost, resuming scan.")
                        break
                        
                    # Demodulate based on mode
                    if current_freq.mode.upper() == 'AM':
                        audio = self.demodulator.demodulate_am(samples)
                    else:
                        audio = self.demodulator.demodulate_fm(samples)
                        
                    if self.audio_stream:
                        self.audio_stream.write(audio)
            else:
                self.scan_next_frequency()

    def run_terminal_interface(self):
        """Run interactive interface."""
        print("Traditional Radio Scanner")
        print("=" * 40)
        if not self.available_banks:
            print("No banks found in plugins/radio_scanner/banks/")
            return

        for i, bank in enumerate(self.available_banks):
            print(f"{i+1}. {bank}")

        try:
            choice = input("Select bank: ").strip()
            idx = int(choice) - 1
            if 0 <= idx < len(self.available_banks):
                if self.load_bank(self.available_banks[idx]):
                    self.is_scanning = True
                    self.scan_loop()
            else:
                print("Invalid choice")
        except (ValueError, KeyboardInterrupt):
            print("\nExiting")

def main():
    """CLI entry point."""
    import argparse
    parser = argparse.ArgumentParser(description="Traditional Radio Scanner")
    parser.add_argument('--bank', type=str, help='Bank filename to load')
    parser.add_argument('--gain', type=str, default='auto', help='SDR gain')
    parser.add_argument('--squelch', type=float, default=-45, help='Squelch threshold in dB')
    args = parser.parse_args()

    scanner = TraditionalScanner()
    scanner.squelch_threshold = args.squelch
    if args.gain != 'auto':
        try: scanner.gain = int(args.gain)
        except ValueError: pass
    
    try:
        scanner.initialize_device()
        if args.bank:
            if scanner.load_bank(args.bank):
                scanner.is_scanning = True
                scanner.scan_loop()
        else:
            scanner.run_terminal_interface()
    finally:
        if scanner.sdr: scanner.sdr.close()
        if scanner.audio_stream: 
            scanner.audio_stream.stop()
            scanner.audio_stream.close()

if __name__ == "__main__":
    main()
