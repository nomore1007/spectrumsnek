#!/usr/bin/env python3
"""
ADS-B Service using dump1090-fa
Provides real ADS-B aircraft tracking using the proven dump1090-fa decoder.
"""

import subprocess
import time
import signal
import os
import sys
import json
from typing import Dict, List, Optional
import requests
import threading

class ADSBService:
    """ADS-B service using dump1090-fa for aircraft detection."""

    def __init__(self):
        self.dump1090_process = None
        self.running = False
        self.aircraft_data = {}
        self.last_update = time.time()

    def start_service(self) -> bool:
        """Start the dump1090-fa service."""
        try:
            print("Starting dump1090-fa ADS-B service...", flush=True)

            # Check if dump1090-fa is installed
            if not self._check_dump1090():
                print("dump1090-fa not found. Please run setup.sh to install it.", flush=True)
                return False

            # Stop any existing dump1090 processes
            self._stop_existing_dump1090()

            # Start dump1090-fa with net-only mode (no web interface conflicts)
            cmd = [
                'dump1090-fa',
                '--net',           # Enable networking
                '--net-http-port', '8080',  # HTTP port for data
                '--quiet',         # Reduce console output
                '--fix',           # Enable CRC checking
                '--no-modeac',     # Disable Mode A/C
                '--metric'         # Use metric units
            ]

            print(f"Running: {' '.join(cmd)}", flush=True)
            self.dump1090_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid
            )

            # Wait a moment for startup
            time.sleep(3)

            # Check if process is still running
            if self.dump1090_process.poll() is None:
                print("✓ dump1090-fa service started successfully", flush=True)
                print("📡 ADS-B receiver active on 1090 MHz", flush=True)
                self.running = True

                # Start data collection thread
                threading.Thread(target=self._collect_aircraft_data, daemon=True).start()

                return True
            else:
                stdout, stderr = self.dump1090_process.communicate()
                print(f"✗ dump1090-fa failed to start", flush=True)
                if stderr:
                    print(f"Error: {stderr.decode()}", flush=True)
                return False

        except Exception as e:
            print(f"Failed to start ADS-B service: {e}", flush=True)
            return False

    def stop_service(self):
        """Stop the dump1090-fa service."""
        print("Stopping dump1090-fa ADS-B service...", flush=True)

        if self.dump1090_process:
            try:
                # Send SIGTERM to the process group
                os.killpg(os.getpgid(self.dump1090_process.pid), signal.SIGTERM)

                # Wait for clean shutdown
                try:
                    self.dump1090_process.wait(timeout=5)
                    print("✓ dump1090-fa service stopped cleanly", flush=True)
                except subprocess.TimeoutExpired:
                    # Force kill if it doesn't respond
                    os.killpg(os.getpgid(self.dump1090_process.pid), signal.SIGKILL)
                    print("✓ dump1090-fa service force-stopped", flush=True)

            except Exception as e:
                print(f"Warning: Error stopping dump1090-fa: {e}", flush=True)

        self.running = False
        self.dump1090_process = None

    def get_status(self) -> Dict:
        """Get service status and aircraft data."""
        status = {
            'running': self.running,
            'aircraft_count': len(self.aircraft_data),
            'aircraft': list(self.aircraft_data.values()),
            'last_update': self.last_update,
            'uptime': time.time() - self.last_update if self.running else 0
        }

        if self.dump1090_process:
            status['pid'] = self.dump1090_process.pid
            status['process_alive'] = self.dump1090_process.poll() is None

        return status

    def _check_dump1090(self) -> bool:
        """Check if dump1090-fa is installed."""
        try:
            result = subprocess.run(['which', 'dump1090-fa'],
                                  capture_output=True, text=True)
            return result.returncode == 0
        except Exception:
            return False

    def _stop_existing_dump1090(self):
        """Stop any existing dump1090 processes."""
        try:
            # Kill any existing dump1090 processes
            subprocess.run(['pkill', '-f', 'dump1090-fa'],
                         capture_output=True)
            time.sleep(1)  # Wait for cleanup
        except Exception:
            pass

    def _collect_aircraft_data(self):
        """Collect aircraft data from dump1090 HTTP interface."""
        while self.running:
            try:
                # Fetch aircraft data from dump1090's HTTP interface
                response = requests.get('http://localhost:8080/data/aircraft.json',
                                      timeout=2)

                if response.status_code == 200:
                    data = response.json()

                    # Update aircraft data
                    new_aircraft = {}
                    for aircraft in data.get('aircraft', []):
                        icao = aircraft.get('hex', '').upper()
                        if icao:
                            new_aircraft[icao] = {
                                'icao': icao,
                                'callsign': aircraft.get('flight', '').strip() or None,
                                'lat': aircraft.get('lat'),
                                'lon': aircraft.get('lon'),
                                'alt': aircraft.get('altitude'),
                                'speed': aircraft.get('speed'),
                                'heading': aircraft.get('track'),
                                'vertical_rate': aircraft.get('vert_rate'),
                                'squawk': aircraft.get('squawk'),
                                'last_seen': aircraft.get('seen', 0),
                                'messages': aircraft.get('messages', 0),
                                'rssi': aircraft.get('rssi')
                            }

                    self.aircraft_data = new_aircraft
                    self.last_update = time.time()

                    aircraft_count = len(new_aircraft)
                    if aircraft_count > 0:
                        print(f"📡 Tracking {aircraft_count} aircraft", flush=True)

                else:
                    # Service might not be ready yet
                    pass

            except requests.RequestException:
                # dump1090 HTTP interface not available
                pass
            except Exception as e:
                print(f"Error collecting aircraft data: {e}", flush=True)

            time.sleep(1)  # Update every second


def run_text_interface(service: ADSBService):
    """Run the text-based ADS-B interface."""
    print("ADS-B Aircraft Tracker - dump1090-fa Service")
    print("Real-time aircraft tracking using dump1090-fa")
    print("Press Ctrl+C or 'q' to quit")
    print()

    last_display = 0
    try:
        while service.running:
            current_time = time.time()

            # Update display every 2 seconds
            if current_time - last_display >= 2:
                status = service.get_status()

                print(f"\rAircraft: {status['aircraft_count']} | Status: {'Active' if status['running'] else 'Inactive'} | Uptime: {status['uptime']:.0f}s", end='', flush=True)

                if status['aircraft']:
                    print(" | Recent aircraft:", flush=True)
                    for aircraft in status['aircraft'][:3]:  # Show first 3
                        callsign = aircraft['callsign'] or 'Unknown'
                        alt = f"{aircraft['alt']}ft" if aircraft['alt'] else '---'
                        print(f"  {aircraft['icao']} {callsign} {alt}", flush=True)
                else:
                    print(" | No aircraft detected", flush=True)

                last_display = current_time

            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\nStopping ADS-B interface...", flush=True)


def run_adsb_service(*args):
    """Main ADS-B service function."""
    service = ADSBService()

    # Parse arguments
    text_mode = '--text' in args

    try:
        # Start the service
        if not service.start_service():
            print("Failed to start ADS-B service", flush=True)
            return

        if text_mode:
            # Run text interface
            run_text_interface(service)
        else:
            # Run in background - just wait
            print("ADS-B service running in background", flush=True)
            print("Press Ctrl+C to stop", flush=True)

            try:
                while service.running:
                    time.sleep(1)
                    status = service.get_status()
                    if not status.get('process_alive', False):
                        print("dump1090-fa process died, stopping service", flush=True)
                        break
            except KeyboardInterrupt:
                print("Stopping ADS-B service...", flush=True)

    finally:
        service.stop_service()


if __name__ == "__main__":
    # Allow direct execution
    run_adsb_service(*sys.argv[1:])