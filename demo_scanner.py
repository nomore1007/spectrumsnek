#!/usr/bin/env python3
"""
RTL-SDR Radio Scanner Demo
Demonstrates functionality without requiring actual RTL-SDR hardware.
"""

import numpy as np
import time
import argparse

def generate_demo_signal(center_freq=100e6, sample_rate=2.4e6, num_samples=1024*1024):
    """Generate a demo signal with some simulated radio stations."""
    # Create time array
    t = np.arange(num_samples) / sample_rate

    # Generate base noise
    signal = np.random.normal(0, 0.1, num_samples) + 1j * np.random.normal(0, 0.1, num_samples)

    # Add some simulated signals (FM stations, etc.)
    frequencies = [
        -0.5e6,  # 99.5 MHz
        0.0,     # 100.0 MHz (center)
        0.5e6,   # 100.5 MHz
        1.0e6,   # 101.0 MHz
    ]

    for freq_offset in frequencies:
        # AM modulated signal
        carrier_freq = freq_offset
        modulation_freq = 1000  # 1 kHz modulation
        modulation_index = 0.3

        carrier = np.exp(1j * 2 * np.pi * carrier_freq * t)
        modulation = 1 + modulation_index * np.sin(2 * np.pi * modulation_freq * t)
        am_signal = carrier * modulation * 0.5

        signal += am_signal

    return signal

def demo_spectrum(center_freq=100e6, sample_rate=2.4e6, duration=None):
    """Run a spectrum analysis demo in terminal."""
    print(f"RTL-SDR Demo: Spectrum Analysis at {center_freq/1e6:.1f} MHz")
    print("Note: This is simulated data - no RTL-SDR hardware required")
    print("Press Ctrl+C to stop")

    # Generate demo signal
    samples = generate_demo_signal(center_freq, sample_rate)

    # Compute FFT parameters
    fft_size = 2048
    window = np.hanning(fft_size)
    freqs = np.fft.fftfreq(fft_size, 1/sample_rate)
    freqs = np.fft.fftshift(freqs) + center_freq

    start_time = time.time()
    frame_count = 0

    try:
        while duration is None or time.time() - start_time < duration:
            # Add some time variation to make it look dynamic
            noise_factor = 0.1 * np.sin(time.time() * 2)
            demo_samples = samples[frame_count*fft_size:(frame_count+1)*fft_size] * (1 + noise_factor)

            # Apply window and compute FFT
            windowed_samples = demo_samples * window
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
            _display_demo_spectrum(freqs, power_spectrum, frame_count, peak_freq, peak_power, avg_power, noise_floor, center_freq)

            frame_count += 1
            time.sleep(0.5)  # Update every 0.5 seconds

    except KeyboardInterrupt:
        print("\nDemo spectrum capture stopped by user")

def _display_demo_spectrum(freqs, power_spectrum, frame_count, peak_freq, peak_power, avg_power, noise_floor, center_freq):
    """Display demo spectrum data in terminal format."""
    # Clear screen (works on most terminals)
    print("\033[2J\033[H", end="")

    # Header
    print(f"RTL-SDR Demo Spectrum Analyzer - Frame {frame_count}")
    print(f"Center: {center_freq/1e6:.1f} MHz | Sample Rate: 2.4 MHz")
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

def demo_scan(start_freq=88e6, end_freq=108e6):
    """Run a frequency scanning demo."""
    print(f"RTL-SDR Demo: Frequency Scan from {start_freq/1e6:.1f} MHz to {end_freq/1e6:.1f} MHz")
    print("Note: This is simulated data - no RTL-SDR hardware required")

    current_freq = start_freq
    step_size = 2e6  # 2 MHz steps

    print("\nScanning for signals...")
    print("Frequency (MHz) | Power Level (dB) | Status")
    print("-" * 45)

    while current_freq <= end_freq:
        # Generate demo signal at this frequency
        samples = generate_demo_signal(current_freq, 2.4e6, 1024*100)

        # Calculate power
        power = 10 * np.log10(np.mean(np.abs(samples)**2))

        # Add some random variation
        power += np.random.normal(0, 5)

        # Determine if it's a "signal"
        if power > -40:
            status = "SIGNAL DETECTED"
        elif power > -50:
            status = "weak signal"
        else:
            status = "noise"

        print(f"{current_freq/1e6:11.1f}   | {power:11.1f}      | {status}")

        # Simulate dwell time
        time.sleep(0.1)

        current_freq += step_size

    print("\nScan complete!")

def main():
    parser = argparse.ArgumentParser(description='RTL-SDR Radio Scanner Demo')
    parser.add_argument('--freq', type=float, default=100,
                       help='Center frequency in MHz (default: 100)')
    parser.add_argument('--mode', choices=['spectrum', 'scan'],
                       default='spectrum', help='Demo mode')
    parser.add_argument('--start-freq', type=float, default=88,
                       help='Start frequency for scanning (MHz)')
    parser.add_argument('--end-freq', type=float, default=108,
                       help='End frequency for scanning (MHz)')
    parser.add_argument('--duration', type=float,
                       help='Demo duration in seconds (default: infinite for spectrum)')

    args = parser.parse_args()

    center_freq = args.freq * 1e6

    if args.mode == 'spectrum':
        duration = args.duration if args.duration is not None else None
        demo_spectrum(center_freq, duration=duration)
    elif args.mode == 'scan':
        start_freq = args.start_freq * 1e6
        end_freq = args.end_freq * 1e6
        demo_scan(start_freq, end_freq)

if __name__ == "__main__":
    main()