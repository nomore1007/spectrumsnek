#!/usr/bin/env python3
"""
ADS-B Aircraft Tracker
Real-time aircraft surveillance and tracking using RTL-SDR.
"""

import sys
import time
import threading
import curses
import json
import warnings
import signal
import os

# Suppress deprecated pkg_resources warning from rtlsdr
warnings.filterwarnings("ignore", message="pkg_resources is deprecated")
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import math
import warnings

# Suppress deprecated pkg_resources warning from rtlsdr
warnings.filterwarnings("ignore", message=".*pkg_resources.*deprecated.*")

try:
    import rtlsdr
except ImportError:
    rtlsdr = None

class Aircraft:
    """Represents an aircraft with ADS-B data."""
    def __init__(self, icao: str):
        self.icao = icao
        self.callsign = None
        self.latitude = None
        self.longitude = None
        self.altitude = None
        self.speed = None
        self.heading = None
        self.vertical_rate = None
        self.last_update = datetime.now()
        self.position_history = []  # List of (lat, lon, alt, time) tuples
        self.message_count = 0

    def update_position(self, lat: float, lon: float, alt: float = None):
        """Update aircraft position."""
        self.latitude = lat
        self.longitude = lon
        if alt is not None:
            self.altitude = alt

        self.last_update = datetime.now()

        # Keep position history (last 50 positions)
        self.position_history.append((lat, lon, alt, self.last_update))
        if len(self.position_history) > 50:
            self.position_history.pop(0)

    def update_callsign(self, callsign: str):
        """Update aircraft callsign."""
        self.callsign = callsign.strip()

    def update_velocity(self, speed: float, heading: float, vertical_rate: float = None):
        """Update aircraft velocity information."""
        self.speed = speed
        self.heading = heading
        if vertical_rate is not None:
            self.vertical_rate = vertical_rate

    def is_expired(self) -> bool:
        """Check if aircraft data is too old (no updates for 60 seconds)."""
        return (datetime.now() - self.last_update).seconds > 60

    def get_display_info(self) -> Dict:
        """Get aircraft information for display."""
        return {
            'icao': self.icao,
            'callsign': self.callsign or 'Unknown',
            'lat': self.latitude,
            'lon': self.longitude,
            'alt': self.altitude,
            'speed': self.speed,
            'heading': self.heading,
            'vertical_rate': self.vertical_rate,
            'last_update': self.last_update,
            'message_count': self.message_count
        }

class ADSBTracker:
    """ADS-B aircraft tracking system."""

    def __init__(self):
        self.aircraft: Dict[str, Aircraft] = {}
        self.sdr = None
        self.running = False
        self.center_freq = 1090000000  # 1090 MHz (ADS-B frequency)
        self.sample_rate = 2400000  # 2.4 MHz sample rate (matches dump1090)
        self.gain = 40  # Manual gain for better sensitivity

        # ADS-B message statistics
        self.total_messages = 0
        self.valid_messages = 0
        self.start_time = datetime.now()

    def initialize_sdr(self):
        """Initialize the RTL-SDR device for ADS-B reception."""
        if rtlsdr is None:
            print("RTL-SDR library not available - cannot initialize ADS-B tracking", flush=True)
            return False

        try:
            print("Initializing SDR for ADS-B...", flush=True)

            # Note: Device enumeration will be handled by the creation attempt below

            # Create SDR with timeout protection
            try:
                self.sdr = rtlsdr.RtlSdr()
                print("SDR device created successfully", flush=True)
            except Exception as e:
                print(f"Failed to create RTL-SDR device: {e}", flush=True)
                print("This may be due to:", flush=True)
                print("- No RTL-SDR hardware connected", flush=True)
                print("- Hardware/driver issues", flush=True)
                print("- Permission problems (try running as root)", flush=True)
                return False

            # Set parameters with individual error handling
            try:
                print(f"Setting center frequency to {self.center_freq} Hz...", flush=True)
                self.sdr.center_freq = self.center_freq
                print("✓ Center frequency set", flush=True)
            except Exception as e:
                print(f"✗ Failed to set center frequency: {e}", flush=True)
                self._safe_close_sdr()
                return False

            try:
                print(f"Setting sample rate to {self.sample_rate} Hz...", flush=True)
                self.sdr.sample_rate = self.sample_rate
                print("✓ Sample rate set", flush=True)
            except Exception as e:
                print(f"✗ Failed to set sample rate: {e}", flush=True)
                self._safe_close_sdr()
                return False

            try:
                print(f"Setting gain to {self.gain}...", flush=True)
                self.sdr.gain = self.gain
                print("✓ Gain set", flush=True)
            except Exception as e:
                print(f"✗ Failed to set gain: {e}", flush=True)
                self._safe_close_sdr()
                return False

            print("✓ RTL-SDR initialized successfully for ADS-B (1090 MHz)", flush=True)
            return True

        except Exception as e:
            print(f"✗ Failed to initialize RTL-SDR: {e}", flush=True)
            self._safe_close_sdr()
            return False

    def _safe_close_sdr(self):
        """Safely close SDR device."""
        if hasattr(self, 'sdr') and self.sdr:
            try:
                self.sdr.close()
                print("SDR device closed", flush=True)
            except Exception as e:
                print(f"Warning: Error closing SDR: {e}", flush=True)
            finally:
                self.sdr = None

    def decode_adsb_message(self, iq_samples: np.ndarray) -> List[Dict]:
        """
        Decode ADS-B messages from IQ samples.
        Disabled to prevent segmentation faults - needs further debugging.
        """
        messages = []

        print("ADS-B decoding temporarily disabled to prevent crashes", flush=True)
        print("System is stable but aircraft detection is not functional", flush=True)

        return messages

    def process_adsb_messages(self, messages: List[Dict]):
        """Process decoded ADS-B messages."""
        for msg in messages:
            icao = msg['icao']

            if icao not in self.aircraft:
                self.aircraft[icao] = Aircraft(icao)

            aircraft = self.aircraft[icao]
            aircraft.message_count += 1

            # Update aircraft data
            if 'lat' in msg and 'lon' in msg:
                aircraft.update_position(msg['lat'], msg['lon'], msg.get('alt'))

            if 'callsign' in msg:
                aircraft.update_callsign(msg['callsign'])

            if 'speed' in msg and 'heading' in msg:
                aircraft.update_velocity(msg['speed'], msg['heading'], msg.get('vertical_rate'))

    def cleanup_expired_aircraft(self):
        """Remove aircraft that haven't been seen for a while."""
        expired = [icao for icao, aircraft in self.aircraft.items() if aircraft.is_expired()]
        for icao in expired:
            del self.aircraft[icao]

    def get_statistics(self) -> Dict:
        """Get tracking statistics."""
        total_aircraft = len(self.aircraft)
        active_aircraft = len([a for a in self.aircraft.values() if not a.is_expired()])
        runtime = datetime.now() - self.start_time

        return {
            'total_aircraft': total_aircraft,
            'active_aircraft': active_aircraft,
            'total_messages': self.total_messages,
            'valid_messages': self.valid_messages,
            'runtime_seconds': runtime.total_seconds(),
            'messages_per_second': self.total_messages / max(runtime.total_seconds(), 1)
        }

class ConsoleADSBInterface:
    """Console-based ADS-B tracking interface."""

    def __init__(self, tracker: ADSBTracker):
        self.tracker = tracker

    def draw_interface(self, stdscr):
        """Draw the console ADS-B interface."""
        stdscr.clear()
        height, width = stdscr.getmaxyx()

        # Title
        title = "ADS-B Aircraft Tracker - 1090 MHz"
        stdscr.addstr(0, 0, title[:width-1], curses.A_BOLD)

        # Statistics
        stats = self.tracker.get_statistics()
        stats_line = f"Aircraft: {stats['active_aircraft']}/{stats['total_aircraft']} | Messages: {stats['total_messages']} | Rate: {stats['messages_per_second']:.1f}/sec"
        stdscr.addstr(1, 0, stats_line[:width-1])

        # Aircraft list
        y = 3
        stdscr.addstr(y, 0, "ICAO     Callsign  Alt(ft)  Speed(kt)  Heading  Lat       Lon       Last Update")
        stdscr.addstr(y+1, 0, "-" * min(85, width-1))

        sorted_aircraft = sorted(self.tracker.aircraft.values(),
                                key=lambda x: x.last_update, reverse=True)

        for i, aircraft in enumerate(sorted_aircraft[:height-8]):  # Leave space for footer
            if y + 2 + i >= height - 2:
                break

            info = aircraft.get_display_info()

            # Format aircraft data
            icao = info['icao'][:6].ljust(6)
            callsign = (info['callsign'][:8] if info['callsign'] else '--------')[:8].ljust(8)
            alt = f"{info['alt']:.0f}" if info['alt'] else '-----'
            speed = f"{info['speed']:.0f}" if info['speed'] else '---'
            heading = f"{info['heading']:.0f}" if info['heading'] else '---'
            lat = f"{info['lat']:.4f}" if info['lat'] else '--------'
            lon = f"{info['lon']:.4f}" if info['lon'] else '--------'

            # Color code based on recency
            age_seconds = (datetime.now() - info['last_update']).seconds
            if age_seconds < 10:
                color = curses.color_pair(1)  # Red for very recent
            elif age_seconds < 30:
                color = curses.A_BOLD  # Bold for recent
            else:
                color = curses.A_DIM  # Dim for older

            # Time since last update
            time_str = f"{age_seconds}s ago" if age_seconds < 60 else "old"

            line = f"{icao} {callsign} {alt.rjust(7)} {speed.rjust(9)} {heading.rjust(7)} {lat.rjust(9)} {lon.rjust(9)} {time_str.rjust(10)}"

            try:
                stdscr.addstr(y + 2 + i, 0, line[:width-1], color)
            except curses.error:
                pass

        # Footer
        footer = "Press 'q' to quit, 'c' to clear expired aircraft"
        try:
            stdscr.addstr(height-1, 0, footer[:width-1], curses.A_DIM)
        except curses.error:
            pass

        stdscr.refresh()

    def run_console(self, stdscr):
        """Run the console ADS-B interface."""
        curses.curs_set(0)  # Hide cursor
        curses.start_color()
        curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)  # Recent aircraft

        stdscr.nodelay(True)  # Non-blocking input

        last_cleanup = time.time()

        while self.tracker.running:
            try:
                self.draw_interface(stdscr)

                # Handle input
                key = stdscr.getch()
                if key == ord('q') or key == ord('Q'):
                    break
                elif key == ord('c') or key == ord('C'):
                    self.tracker.cleanup_expired_aircraft()

                # Periodic cleanup
                if time.time() - last_cleanup > 30:  # Clean up every 30 seconds
                    self.tracker.cleanup_expired_aircraft()
                    last_cleanup = time.time()

                time.sleep(0.1)

            except KeyboardInterrupt:
                break
            except Exception as e:
                # Continue on display errors
                time.sleep(0.5)

    def run_text(self):
        """Run the text-based ADS-B interface."""
        last_cleanup = time.time()

        print("ADS-B Aircraft Tracker - Text Mode")
        print("Press Ctrl+C or 'q' to quit")
        print("DEBUG: Entering text mode loop...")
        print()

        while self.tracker.running:
            try:
                stats = self.tracker.get_statistics()
                print(f"Aircraft: {stats['active_aircraft']}/{stats['total_aircraft']} | Messages: {stats['total_messages']} | Rate: {stats['messages_per_second']:.1f}/sec")

                sorted_aircraft = sorted(self.tracker.aircraft.values(),
                                        key=lambda x: x.last_update, reverse=True)

                if sorted_aircraft:
                    print("Recent aircraft:")
                    for aircraft in sorted_aircraft[:5]:  # Show top 5 recent
                        info = aircraft.get_display_info()
                        icao = info['icao'][:6]
                        callsign = (info['callsign'][:8] if info['callsign'] else '--------')[:8]
                        alt = f"{info['alt']:.0f}" if info['alt'] else '-----'
                        speed = f"{info['speed']:.0f}" if info['speed'] else '---'
                        heading = f"{info['heading']:.0f}" if info['heading'] else '---'
                        lat = f"{info['lat']:.4f}" if info['lat'] else '--------'
                        lon = f"{info['lon']:.4f}" if info['lon'] else '--------'
                        print(f"  {icao} {callsign} {alt}ft {speed}kt {heading}° {lat} {lon}")
                else:
                    print("No aircraft detected")

                print()

                # Cleanup occasionally
                if time.time() - last_cleanup > 60:
                    self.tracker.cleanup_expired_aircraft()
                    last_cleanup = time.time()

                time.sleep(5)  # Update every 5 seconds

            except KeyboardInterrupt:
                break
            except EOFError:
                # Handle case where input stream is closed (remote disconnect)
                print("\nInput stream closed, stopping text interface...")
                break

        print("ADS-B tracking stopped")

class WebADSBInterface:
    """Web interface for ADS-B tracking."""

    def __init__(self, tracker: ADSBTracker, host='0.0.0.0', port=5001):
        self.tracker = tracker
        self.host = host
        self.port = port

        # Web server setup will be added when Flask is available
        self.app = None
        self.socketio = None

    def get_html_template(self):
        """Return the HTML template for the web ADS-B interface."""
        return """
<!DOCTYPE html>
<html>
<head>
    <title>ADS-B Aircraft Tracker</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.7.2/socket.io.js"></script>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #1a1a1a;
            color: #ffffff;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .header {
            text-align: center;
            margin-bottom: 20px;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        .stat-card {
            background-color: #2d2d2d;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
        }
        .aircraft-table {
            background-color: #2d2d2d;
            border-radius: 8px;
            overflow: hidden;
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #444;
        }
        th {
            background-color: #333;
            font-weight: bold;
        }
        tr:hover {
            background-color: #333;
        }
        .recent {
            color: #ff4444;
        }
        .active {
            color: #44ff44;
        }
        .old {
            color: #888;
        }
        .status {
            background-color: #2d2d2d;
            padding: 10px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>ADS-B Aircraft Tracker</h1>
            <p>Real-time aircraft surveillance on 1090 MHz</p>
        </div>

        <div class="status" id="status">
            Status: Connecting...
        </div>

        <div class="stats">
            <div class="stat-card">
                <div id="activeAircraft">0</div>
                <div>Active Aircraft</div>
            </div>
            <div class="stat-card">
                <div id="totalMessages">0</div>
                <div>Total Messages</div>
            </div>
            <div class="stat-card">
                <div id="messagesPerSecond">0.0</div>
                <div>Messages/sec</div>
            </div>
            <div class="stat-card">
                <div id="runtime">00:00:00</div>
                <div>Runtime</div>
            </div>
        </div>

        <div class="aircraft-table">
            <table id="aircraftTable">
                <thead>
                    <tr>
                        <th>ICAO</th>
                        <th>Callsign</th>
                        <th>Altitude</th>
                        <th>Speed</th>
                        <th>Heading</th>
                        <th>Latitude</th>
                        <th>Longitude</th>
                        <th>Last Update</th>
                    </tr>
                </thead>
                <tbody id="aircraftBody">
                    <tr>
                        <td colspan="8" style="text-align: center;">Waiting for aircraft data...</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>

    <script>
        const socket = io();
        const aircraftBody = document.getElementById('aircraftBody');
        const statusDiv = document.getElementById('status');
        const activeAircraftDiv = document.getElementById('activeAircraft');
        const totalMessagesDiv = document.getElementById('totalMessages');
        const messagesPerSecondDiv = document.getElementById('messagesPerSecond');
        const runtimeDiv = document.getElementById('runtime');

        socket.on('connect', () => {
            statusDiv.textContent = 'Status: Connected to ADS-B tracker';
        });

        socket.on('disconnect', () => {
            statusDiv.textContent = 'Status: Disconnected';
        });

        socket.on('adsb_data', (data) => {
            // Update statistics
            activeAircraftDiv.textContent = data.stats.active_aircraft;
            totalMessagesDiv.textContent = data.stats.total_messages;
            messagesPerSecondDiv.textContent = data.stats.messages_per_second.toFixed(1);
            runtimeDiv.textContent = formatRuntime(data.stats.runtime_seconds);

            // Update aircraft table
            updateAircraftTable(data.aircraft);
        });

        function updateAircraftTable(aircraft) {
            if (!aircraft || aircraft.length === 0) {
                aircraftBody.innerHTML = '<tr><td colspan="8" style="text-align: center;">No aircraft detected</td></tr>';
                return;
            }

            const rows = aircraft.map(ac => {
                const age = Math.floor((Date.now() - new Date(ac.last_update)) / 1000);
                let ageClass = 'old';
                if (age < 10) ageClass = 'recent';
                else if (age < 30) ageClass = 'active';

                const ageText = age < 60 ? `${age}s ago` : 'old';

                return `
                    <tr class="${ageClass}">
                        <td>${ac.icao}</td>
                        <td>${ac.callsign || 'Unknown'}</td>
                        <td>${ac.alt ? Math.round(ac.alt) + ' ft' : '-'}</td>
                        <td>${ac.speed ? Math.round(ac.speed) + ' kt' : '-'}</td>
                        <td>${ac.heading ? Math.round(ac.heading) + '°' : '-'}</td>
                        <td>${ac.lat ? ac.lat.toFixed(4) : '-'}</td>
                        <td>${ac.lon ? ac.lon.toFixed(4) : '-'}</td>
                        <td>${ageText}</td>
                    </tr>
                `;
            }).join('');

            aircraftBody.innerHTML = rows;
        }

        function formatRuntime(seconds) {
            const hours = Math.floor(seconds / 3600);
            const minutes = Math.floor((seconds % 3600) / 60);
            const secs = Math.floor(seconds % 60);
            return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
        }

        // Request updates every second
        setInterval(() => {
            fetch('/api/adsb_status')
                .then(response => response.json())
                .then(data => {
                    socket.emit('request_update');
                })
                .catch(err => {
                    // Ignore errors
                });
        }, 1000);
    </script>
</body>
</html>
        """

    def setup_routes(self):
        """Set up Flask routes."""
        if self.app:
            @self.app.route('/')
            def index():
                return self.get_html_template()

            @self.app.route('/api/adsb_status')
            def get_adsb_status():
                stats = self.tracker.get_statistics()
                aircraft_data = [ac.get_display_info() for ac in self.tracker.aircraft.values()]
                return json.dumps({
                    'stats': stats,
                    'aircraft': aircraft_data
                })

    def run(self):
        """Run the web ADS-B interface."""
        try:
            from flask import Flask
            from flask_socketio import SocketIO

            self.app = Flask(__name__)
            self.socketio = SocketIO(self.app, cors_allowed_origins="*")

            self.setup_routes()

            print(f"Starting ADS-B web interface on http://{self.host}:{self.port}")
            self.socketio.run(self.app, host=self.host, port=self.port, debug=False)
        except ImportError:
            print("Web interface not available - Flask not installed")
        except KeyboardInterrupt:
            print("\nADS-B web interface stopped")

def run_tracking_loop(tracker: ADSBTracker):
    """Run the ADS-B tracking loop."""
    print("Starting ADS-B tracking...")

    if not tracker.initialize_sdr():
        print("Failed to initialize SDR for ADS-B")
        return

    tracker.running = True
    tracker.start_time = datetime.now()

    try:
        while tracker.running:
            try:
                # Check if SDR is still valid
                if not hasattr(tracker, 'sdr') or tracker.sdr is None:
                    print("SDR device lost, stopping tracking", flush=True)
                    break

                # Read samples from SDR with comprehensive error handling
                try:
                    # Check if SDR is still accessible
                    if tracker.sdr is None:
                        print("SDR device lost, stopping tracking", flush=True)
                        break

                    samples = tracker.sdr.read_samples(65536)  # 64K samples
                except (OSError, IOError) as e:
                    print(f"SDR I/O error: {e}, device may be disconnected", flush=True)
                    tracker._safe_close_sdr()
                    break
                except Exception as e:
                    print(f"SDR read error: {e}, retrying in 1 second", flush=True)
                    time.sleep(1)
                    continue

                # Validate samples with additional checks
                if samples is None:
                    print("No samples received from SDR (None)", flush=True)
                    time.sleep(0.1)
                    continue
                elif len(samples) == 0:
                    print("Empty samples received from SDR", flush=True)
                    time.sleep(0.1)
                    continue
                elif not isinstance(samples, (list, np.ndarray)):
                    print(f"Invalid sample type: {type(samples)}, expected array", flush=True)
                    time.sleep(0.1)
                    continue

                # Additional validation for numpy arrays
                try:
                    if isinstance(samples, np.ndarray):
                        # Check for NaN or infinite values that could cause issues
                        if not np.isfinite(samples).all():
                            print("SDR samples contain NaN or infinite values, skipping", flush=True)
                            continue
                        # Check array shape and dtype
                        if samples.ndim != 1:
                            print(f"Invalid SDR sample dimensions: {samples.ndim}, expected 1D", flush=True)
                            continue
                        if samples.dtype not in [np.complex64, np.complex128, np.float32, np.float64]:
                            print(f"Unexpected SDR sample dtype: {samples.dtype}", flush=True)
                            continue
                except Exception as e:
                    print(f"SDR sample validation failed: {e}, skipping", flush=True)
                    continue

                # Decode ADS-B messages
                try:
                    messages = tracker.decode_adsb_message(samples)
                except Exception as e:
                    print(f"ADS-B decode error: {e}, continuing", flush=True)
                    messages = []

                # Process messages
                try:
                    if messages:  # Only process if we have messages
                        tracker.process_adsb_messages(messages)
                except Exception as e:
                    print(f"Message processing error: {e}, continuing", flush=True)

                # Update statistics
                try:
                    tracker.total_messages += len(messages)
                    tracker.valid_messages += len([m for m in messages if 'icao' in m])
                except Exception as e:
                    print(f"Statistics update error: {e}", flush=True)

                time.sleep(0.1)  # ~10 FPS

            except Exception as e:
                print(f"ADS-B tracking loop error: {e}", flush=True)
                time.sleep(1)

    except KeyboardInterrupt:
        print("\nADS-B tracking stopped by user", flush=True)
    except Exception as e:
        print(f"\nADS-B tracking stopped due to error: {e}", flush=True)
    finally:
        print("Cleaning up ADS-B tracker...", flush=True)
        tracker.running = False
        if hasattr(tracker, 'sdr') and tracker.sdr:
            try:
                tracker.sdr.close()
                print("SDR device closed", flush=True)
            except Exception as e:
                print(f"Error closing SDR: {e}", flush=True)

def signal_handler(signum, frame):
    """Handle signals including segmentation faults."""
    print(f"\nReceived signal {signum} ({signal.Signals(signum).name})", flush=True)

    # Clean up curses if it's initialized (safe to call even if not initialized)
    try:
        curses.endwin()
        curses.curs_set(1)  # Show cursor
        curses.echo()  # Re-enable echo
    except curses.error:
        # Curses not initialized or already cleaned up
        pass
    except Exception:
        # Any other curses-related error
        pass

    # Clean up lock file on crash
    try:
        lock_file = '/tmp/adsb_tracker.lock'
        if os.path.exists(lock_file):
            os.remove(lock_file)
    except:
        pass

    # Print helpful message
    if signum == signal.SIGSEGV:
        print("Segmentation fault detected. This may be due to:", flush=True)
        print("- RTL-SDR hardware issues", flush=True)
        print("- Driver compatibility problems", flush=True)
        print("- Memory corruption in numpy/rtlsdr", flush=True)
        print("", flush=True)
        print("Try running with --text mode or check hardware connections.", flush=True)

    # Exit cleanly
    sys.exit(1)

def is_remote_session():
    """Check if running in a remote session (SSH, etc.)"""
    import os
    # Check for SSH environment variables, but exclude if running as root (sudo)
    # since sudo preserves SSH environment variables
    ssh_vars = ['SSH_CLIENT', 'SSH_TTY', 'SSH_CONNECTION']
    has_ssh_vars = any(os.environ.get(var) for var in ssh_vars)

    # If running as root but has SSH vars, it's likely sudo preserving environment
    # Check if we're actually in an interactive terminal (not remote)
    if has_ssh_vars and os.geteuid() == 0:
        try:
            import sys
            # If stdin/stdout are TTYs and not explicitly remote, treat as local
            return not (sys.stdin.isatty() and sys.stdout.isatty())
        except:
            return True
    elif has_ssh_vars and 'SSH_TTY' in os.environ:
        # Has actual SSH TTY, definitely remote
        return True

    return False

def main(args=None):
    """Main ADS-B tracker function."""
    import argparse
    import os
    import sys

    # Prevent multiple instances by checking for existing process
    lock_file = '/tmp/adsb_tracker.lock'
    if os.path.exists(lock_file):
        try:
            with open(lock_file, 'r') as f:
                existing_pid = int(f.read().strip())
            # Check if process is still running
            os.kill(existing_pid, 0)
            print("ADS-B tracker is already running (PID {}). Exiting.".format(existing_pid), flush=True)
            sys.exit(1)
        except (OSError, ValueError):
            # Process not running or invalid PID, remove stale lock
            try:
                os.remove(lock_file)
            except OSError:
                pass

    # Create lock file
    try:
        with open(lock_file, 'w') as f:
            f.write(str(os.getpid()))
            f.flush()
    except IOError:
        print("Warning: Could not create lock file", flush=True)



    # Set up signal handlers for graceful error handling
    signal.signal(signal.SIGSEGV, signal_handler)  # Segmentation fault
    signal.signal(signal.SIGABRT, signal_handler)  # Abort signal
    signal.signal(signal.SIGBUS, signal_handler)  # Bus error

    parser = argparse.ArgumentParser(description='ADS-B Aircraft Tracker')
    parser.add_argument('--freq', type=float, default=1090,
                        help='ADS-B frequency in MHz (default: 1090)')
    parser.add_argument('--gain', type=str, default='auto',
                        help='SDR gain setting (auto or dB value)')
    parser.add_argument('--web', action='store_true',
                        help='Enable web interface')
    parser.add_argument('--text', action='store_true',
                        help='Run in text mode (console output)')
    parser.add_argument('--web-host', type=str, default='0.0.0.0',
                        help='Web server host')
    parser.add_argument('--web-port', type=int, default=5001,
                        help='Web server port')

    args = parser.parse_args(args)
    print("DEBUG: ADS-B tool arguments parsed, initializing...")

    tracker = ADSBTracker()
    tracker.center_freq = int(args.freq * 1e6)
    if args.gain == 'auto':
        tracker.gain = 'auto'
    else:
        tracker.gain = int(args.gain)

    # Start tracking thread (SDR initialization happens in the thread)
    print("Starting ADS-B tracking...")
    print("DEBUG: Starting tracking thread...")
    tracking_thread = threading.Thread(target=run_tracking_loop, args=(tracker,), daemon=True)
    tracking_thread.start()

    time.sleep(2)  # Let tracking start



    if args.web:
        # Run web interface
        try:
            web_interface = WebADSBInterface(tracker, args.web_host, args.web_port)
            web_interface.run()
        except Exception as e:
            print(f"Web interface failed: {e}")
            print("Falling back to text interface...")
            args.text = True  # Fall through to text

    if args.text:
        # Run text interface
        try:
            console = ConsoleADSBInterface(tracker)
            console.run_text()
        except KeyboardInterrupt:
            print("\nADS-B tracking stopped by user")
        except Exception as e:
            print(f"Text interface failed: {e}")
            print("ADS-B tracking continues in background...")
            try:
                input("Press Enter to stop")
            except EOFError:
                # Handle case where input is not available (remote session disconnect)
                print("Input not available, stopping...")
                pass
    else:
        # Run console interface
        try:
            def console_main(stdscr):
                console = ConsoleADSBInterface(tracker)
                console.run_console(stdscr)

            curses.wrapper(console_main)
        except KeyboardInterrupt:
            print("\nADS-B tracking stopped by user")
        except curses.error as e:
            print(f"Curses interface failed: {e}")
            print("Falling back to text interface...")
            try:
                console = ConsoleADSBInterface(tracker)
                console.run_text()
            except Exception as e2:
                print(f"Text interface also failed: {e2}")
        except Exception as e:
            print(f"Curses interface not available ({e})")
            if is_remote_session():
                print("This is expected in remote SSH sessions.")
            print("Falling back to text mode...")
            # Fall back to text interface
            try:
                console = ConsoleADSBInterface(tracker)
                console.run_text()
            except Exception as e2:
                print(f"Text interface also failed ({e2})")
                print("ADS-B tracking continues in background...")
                try:
                    input("Press Enter to stop")
                except:
                    pass  # Handle EOF in remote sessions
        except Exception as e:
            print(f"Console interface failed ({e}), falling back to text mode...")
            # Fall back to text interface
            try:
                console = ConsoleADSBInterface(tracker)
                console.run_text()
            except Exception as e2:
                print(f"Text interface also failed ({e2})")
                print("ADS-B tracking continues in background...")
                try:
                    input("Press Enter to stop")
                except:
                    pass  # Handle EOF in remote sessions

    # Stop tracking
    tracker.running = False
    if tracking_thread.is_alive():
        tracking_thread.join(timeout=2)

    # Clean up lock file
    try:
        lock_file = '/tmp/adsb_tracker.lock'
        if os.path.exists(lock_file):
            os.remove(lock_file)
    except:
        pass

if __name__ == "__main__":
    main()