#!/usr/bin/env python3
"""
RTL-SDR Radio Scanner
A Python program for scanning and analyzing radio frequencies using RTL-SDR dongle.
"""

import numpy as np
from rtlsdr import RtlSdr
import scipy.signal as signal
from scipy.signal import windows
from scipy.io.wavfile import write
import time
import argparse
import logging
import sys
from datetime import datetime
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RTLSDRScanner:
    def __init__(self, sample_rate=2.4e6, center_freq=100e6, gain='auto'):
        """
        Initialize the RTL-SDR scanner.

        Args:
            sample_rate (float): Sample rate in Hz (default: 2.4 MHz)
            center_freq (float): Center frequency in Hz (default: 100 MHz)
            gain (str or float): Gain setting ('auto' or specific dB value)
        """
        self.sample_rate = sample_rate
        self.center_freq = center_freq
        self.gain = gain
        self.sdr = None
        self.is_scanning = False

    def initialize_device(self):
        """Initialize and configure the RTL-SDR device."""
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

            logger.info("RTL-SDR initialized:")
            logger.info(f"  Sample Rate: {self.sdr.sample_rate / 1e6:.1f} MHz")
            logger.info(f"  Center Frequency: {self.sdr.center_freq / 1e6:.1f} MHz")
            logger.info(f"  Gain: {self.sdr.gain}")

        except Exception as e:
            logger.error(f"Failed to initialize RTL-SDR: {e}")
            raise

    def scan_frequencies(self, freq_range, num_samples=1024*1024, dwell_time=0.1):
        """
        Scan a range of frequencies.

        Args:
            freq_range (tuple): (start_freq, end_freq) in Hz
            num_samples (int): Number of samples to capture
            dwell_time (float): Time to dwell on each frequency in seconds
        """
        if self.sdr is None:
            raise RuntimeError("RTL-SDR not initialized. Call initialize_device() first.")

        start_freq, end_freq = freq_range
        current_freq = start_freq

        logger.info(f"Starting frequency scan from {start_freq/1e6:.1f} MHz to {end_freq/1e6:.1f} MHz")

        try:
            while current_freq <= end_freq and self.is_scanning:
                self.sdr.center_freq = current_freq
                logger.info(f"Scanning frequency: {current_freq/1e6:.1f} MHz")

                # Capture samples
                samples = self.sdr.read_samples(num_samples)

                # Process samples (basic power measurement)
                power = 10 * np.log10(np.mean(np.abs(samples)**2))

                logger.info(f"Power level: {power:.1f} dB")

                # Save interesting signals
                if power > -50:  # Threshold for interesting signals
                    self.save_recording(samples, current_freq, f"signal_{current_freq/1e6:.1f}MHz")

                time.sleep(dwell_time)
                current_freq += self.sample_rate / 2  # Step by half bandwidth

        except KeyboardInterrupt:
            logger.info("Scan interrupted by user")
        except Exception as e:
            logger.error(f"Error during scanning: {e}")

    def capture_spectrum(self, num_samples=1024*1024, duration=None):
        """
        Capture and display real-time spectrum in terminal.

        Args:
            num_samples (int): Number of samples to capture per frame
            duration (float): Total duration to capture in seconds (None = run indefinitely)
        """
        if self.sdr is None:
            raise RuntimeError("RTL-SDR not initialized. Call initialize_device() first.")

        logger.info("Starting spectrum capture (terminal mode)...")
        logger.info(f"Center frequency: {self.center_freq/1e6:.1f} MHz")
        logger.info("Press Ctrl+C to stop")

        start_time = time.time()
        frame_count = 0

        try:
            while duration is None or time.time() - start_time < duration:
                # Capture samples
                samples = self.sdr.read_samples(num_samples)

                # Compute FFT
                fft_size = 1024
                window = windows.hann(fft_size)
                freqs = np.fft.fftfreq(fft_size, 1/self.sample_rate)
                freqs = np.fft.fftshift(freqs) + self.center_freq

                # Apply window and compute FFT
                windowed_samples = samples[:fft_size] * window
                fft_result = np.fft.fft(windowed_samples)
                fft_result = np.fft.fftshift(fft_result)
                power_spectrum = 20 * np.log10(np.abs(fft_result) + 1e-10)

                # Find peak signal
                peak_idx = np.argmax(power_spectrum)
                peak_freq = freqs[peak_idx] / 1e6
                peak_power = power_spectrum[peak_idx]

                # Calculate average power and noise floor
                avg_power = np.mean(power_spectrum)
                noise_floor = np.percentile(power_spectrum, 10)  # 10th percentile

                # Display spectrum as text
                self._display_text_spectrum(freqs, power_spectrum, frame_count, peak_freq, peak_power, avg_power, noise_floor)

                frame_count += 1
                time.sleep(0.5)  # Update every 0.5 seconds

        except KeyboardInterrupt:
            logger.info("\nSpectrum capture stopped by user")

    def _display_text_spectrum(self, freqs, power_spectrum, frame_count, peak_freq, peak_power, avg_power, noise_floor):
        """Display spectrum data in terminal format."""
        # Clear screen (works on most terminals)
        print("\033[2J\033[H", end="")

        # Header
        print(f"RTL-SDR Spectrum Analyzer - Frame {frame_count}")
        print(f"Center: {self.center_freq/1e6:.1f} MHz | Sample Rate: {self.sample_rate/1e6:.1f} MHz")
        print("-" * 60)

        # Statistics
        print(".1f")
        print(".1f")
        print(".1f")
        print("-" * 60)

        # Simple ASCII spectrum display
        # Create a simple bar graph for the spectrum
        min_freq = np.min(freqs) / 1e6
        max_freq = np.max(freqs) / 1e6
        freq_range = max_freq - min_freq

        # Downsample for display (show ~50 frequency bins)
        display_bins = 50
        bin_size = len(power_spectrum) // display_bins

        print("Spectrum (ASCII):")
        print(".1f")
        bars = ""
        for i in range(display_bins):
            start_idx = i * bin_size
            end_idx = min((i + 1) * bin_size, len(power_spectrum))
            bin_power = np.mean(power_spectrum[start_idx:end_idx])

            # Normalize power to 0-10 scale for bar height
            # Adjust for typical RTL-SDR range (-80dB to -20dB)
            normalized_power = max(0, min(10, int((bin_power + 80) / 6)))
            bars += "█" * normalized_power + "░" * (10 - normalized_power)

        print(bars)
        print(".1f")
        print("\nPress Ctrl+C to stop...")

    def save_recording(self, samples, frequency, filename):
        """
        Save captured samples as WAV file.

        Args:
            samples: IQ samples
            frequency (float): Center frequency in Hz
            filename (str): Output filename (without extension)
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            full_filename = f"{filename}_{timestamp}.wav"

            # Convert complex samples to real for WAV format
            # Take magnitude for audio representation
            audio_data = np.abs(samples).astype(np.float32)

            # Normalize to [-1, 1] range
            audio_data = audio_data / np.max(np.abs(audio_data))

            # Convert to 16-bit PCM
            audio_data = (audio_data * 32767).astype(np.int16)

            write(full_filename, int(self.sample_rate), audio_data)

            logger.info(f"Recording saved: {full_filename}")

        except Exception as e:
            logger.error(f"Failed to save recording: {e}")

    def record_fm_radio(self, frequency, duration=10.0, filename=None):
        """
        Record FM radio station.

        Args:
            frequency (float): Frequency in Hz
            duration (float): Recording duration in seconds
            filename (str): Output filename
        """
        if self.sdr is None:
            raise RuntimeError("RTL-SDR not initialized. Call initialize_device() first.")

        if filename is None:
            filename = f"fm_{frequency/1e6:.1f}MHz_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        self.sdr.center_freq = frequency
        logger.info(f"Recording FM station at {frequency/1e6:.1f} MHz for {duration} seconds")

        num_samples = int(self.sample_rate * duration)
        samples = self.sdr.read_samples(num_samples)

        self.save_recording(samples, frequency, filename)

    def close(self):
        """Close the RTL-SDR device."""
        if self.sdr:
            self.sdr.close()
            logger.info("RTL-SDR device closed")

def main():
    parser = argparse.ArgumentParser(description='RTL-SDR Radio Scanner')
    parser.add_argument('--freq', type=float, default=100e6,
                       help='Center frequency in MHz (default: 100)')
    parser.add_argument('--sample-rate', type=float, default=2.4,
                       help='Sample rate in MHz (default: 2.4)')
    parser.add_argument('--gain', type=str, default='auto',
                       help='Gain setting (auto or dB value)')
    parser.add_argument('--mode', choices=['scan', 'spectrum', 'record'],
                       default='spectrum', help='Operation mode')
    parser.add_argument('--start-freq', type=float,
                       help='Start frequency for scanning (MHz)')
    parser.add_argument('--end-freq', type=float,
                       help='End frequency for scanning (MHz)')
    parser.add_argument('--duration', type=float,
                       help='Duration in seconds (spectrum: infinite by default, record: 10.0)')
    parser.add_argument('--web', action='store_true',
                       help='Run web interface instead of terminal interface')
    parser.add_argument('--web-host', type=str, default='0.0.0.0',
                       help='Web server host (default: 0.0.0.0)')
    parser.add_argument('--web-port', type=int, default=5000,
                       help='Web server port (default: 5000)')
    parser.add_argument('--output', type=str,
                       help='Output filename for recordings')

    args = parser.parse_args()

    # Convert frequencies to Hz
    center_freq = args.freq * 1e6
    sample_rate = args.sample_rate * 1e6

    scanner = None
    try:
        scanner = RTLSDRScanner(sample_rate, center_freq, args.gain)
        scanner.initialize_device()

        scanner.is_scanning = True

        if args.mode == 'scan':
            if not args.start_freq or not args.end_freq:
                logger.error("Scan mode requires --start-freq and --end-freq")
                sys.exit(1)
            freq_range = (args.start_freq * 1e6, args.end_freq * 1e6)
            scanner.scan_frequencies(freq_range)

        elif args.mode == 'spectrum':
            # For spectrum mode, None means run indefinitely
            spectrum_duration = args.duration
            scanner.capture_spectrum(duration=spectrum_duration)

        elif args.mode == 'record':
            # For record mode, use default duration if not specified
            record_duration = args.duration if args.duration is not None else 10.0
            scanner.record_fm_radio(center_freq, record_duration, args.output)

    except KeyboardInterrupt:
        logger.info("Program interrupted by user")
    except Exception as e:
        logger.error(f"Program error: {e}")
        sys.exit(1)
    finally:
        if scanner is not None:
            scanner.close()

if __name__ == "__main__":
    main()