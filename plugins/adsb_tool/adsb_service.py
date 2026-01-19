"""
ADS-B Service using external decoders
Provides real ADS-B aircraft tracking using readsb, dump1090-fa, or dump1090.
"""

import subprocess
import time
import signal
import os
import sys
import json
from typing import Dict, List, Optional
from datetime import datetime
import requests
import threading

class ADSBService:
    """ADS-B service using external decoder for aircraft detection."""

    def __init__(self):
        self.readsb_process = None
        self.running = False
        self.aircraft_data = {}
        self.last_update = time.time()
        self.start_time = time.time()
        self.decoder_cmd = None

    def _check_readsb(self) -> bool:
        """Check if ADS-B decoder (readsb, dump1090-mutability, dump1090-fa, dump1090) is installed."""
        try:
            # Try multiple ADS-B decoders in order of preference
            decoders = ['readsb', 'dump1090-mutability', 'dump1090-fa', 'dump1090']
            for cmd in decoders:
                result = subprocess.run(['which', cmd],
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    print(f"✓ Found ADS-B decoder: {cmd}", flush=True)
                    return True
            # Also check if dump1090-mutability installed dump1090 binary
            result = subprocess.run(['which', 'dump1090'],
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✓ Found ADS-B decoder: dump1090 (from dump1090-mutability)", flush=True)
                return True
            print("ℹ No ADS-B decoder found - aircraft detection requires external decoder", flush=True)
            print("  Available options: readsb, dump1090-mutability, dump1090-fa, dump1090", flush=True)
            return False
        except Exception as e:
            print(f"⚠ Error checking for ADS-B decoder: {e}", flush=True)
            return False

    def _stop_existing_readsb(self):
        """Stop any existing ADS-B decoder processes."""
        try:
            # Kill any existing ADS-B decoder processes
            decoders = ['readsb', 'dump1090-mutability', 'dump1090-fa', 'dump1090']
            for cmd in decoders:
                subprocess.run(['pkill', '-f', cmd],
                              capture_output=True)
            time.sleep(1)  # Wait for cleanup
        except Exception:
            pass

    def _fail_gracefully(self) -> bool:
        """Fail gracefully when no ADS-B decoder is available."""
        print("❌ ADS-B functionality unavailable - no decoder installed", flush=True)
        print("", flush=True)
        print("🚀 QUICK FIX - Run setup with sudo:", flush=True)
        print("    sudo ./setup.sh --full", flush=True)
        print("", flush=True)
        print("This will automatically install dump1090-mutability and enable ADS-B.", flush=True)
        print("", flush=True)
        print("Manual installation options:", flush=True)
        print("  sudo apt install dump1090-mutability  (recommended)", flush=True)
        print("  sudo apt install readsb", flush=True)
        print("  sudo apt install dump1090-fa", flush=True)
        print("", flush=True)
        print("Then restart the ADS-B tool to see real aircraft data!", flush=True)
        return False

    def _check_rtl_conflicts(self) -> bool:
        """Check for and resolve RTL-SDR device conflicts."""
        try:
            # Check if dump1090-mutability service is running
            import subprocess
            result = subprocess.run(['systemctl', 'is-active', '--quiet', 'dump1090-mutability'],
                                  capture_output=True)
            if result.returncode == 0:
                print("⚠ RTL-SDR Conflict: dump1090-mutability service is running", flush=True)
                print("  Attempting to stop conflicting service...", flush=True)

                stop_result = subprocess.run(['sudo', 'systemctl', 'stop', 'dump1090-mutability'],
                                           capture_output=True)
                if stop_result.returncode == 0:
                    subprocess.run(['sudo', 'systemctl', 'disable', 'dump1090-mutability'],
                                 capture_output=True)
                    print("✓ Conflicting service stopped and disabled", flush=True)
                    time.sleep(2)  # Wait for cleanup
                else:
                    print("❌ Failed to stop conflicting service - manual intervention required", flush=True)
                    print("  Run: sudo systemctl stop dump1090-mutability", flush=True)
                    return False

            # Check for other RTL-SDR processes
            result = subprocess.run(['pgrep', '-f', 'rtl|dump1090'],
                                  capture_output=True, text=True)
            if result.returncode == 0:
                processes = result.stdout.strip().split('\n')
                if processes and processes[0]:
                    print(f"⚠ Found {len(processes)} conflicting RTL-SDR process(es)", flush=True)

                    # Try to stop them
                    stop_result = subprocess.run(['sudo', 'pkill', '-f', 'rtl'],
                                               capture_output=True)
                    subprocess.run(['sudo', 'pkill', '-f', 'dump1090'],
                                 capture_output=True)

                    if stop_result.returncode == 0:
                        print("✓ Conflicting RTL-SDR processes stopped", flush=True)
                        time.sleep(1)
                    else:
                        print("❌ Failed to stop conflicting processes - manual intervention required", flush=True)
                        print("  Run: sudo pkill -f rtl && sudo pkill -f dump1090", flush=True)
                        return False

            return True

        except Exception as e:
            print(f"⚠ Error checking RTL conflicts: {e}", flush=True)
            return True  # Continue anyway

    def start_service(self) -> bool:
        """Start the ADS-B service using external decoder."""
        try:
            # Check for RTL-SDR conflicts and resolve them
            if not self._check_rtl_conflicts():
                return self._fail_gracefully()

            # Check if ADS-B decoder is available
            if not self._check_readsb():
                return self._fail_gracefully()

            # Stop any existing dump1090 processes (double-check)
            self._stop_existing_readsb()

            # Try multiple ADS-B decoders in order of preference
            dump1090_cmd = None
            decoders = ['readsb', 'dump1090-mutability', 'dump1090-fa', 'dump1090']
            for cmd in decoders:
                try:
                    result = subprocess.run(['which', cmd], capture_output=True, text=True)
                    if result.returncode == 0:
                        dump1090_cmd = cmd
                        break
                except:
                    continue

            if not dump1090_cmd:
                return self._fail_gracefully()

            self.decoder_cmd = dump1090_cmd

            # Start ADS-B decoder with RTL-SDR device and networking enabled
            cmd = [dump1090_cmd]

            # Add device and networking options based on decoder
            if dump1090_cmd == 'readsb':
                cmd.extend(['--device-type', 'rtlsdr', '--net', '--net-api-port', '8080'])
            elif dump1090_cmd == 'dump1090-fa':
                cmd.extend(['--device-type', 'rtlsdr', '--net', '--net-ro-port', '8080'])
            elif dump1090_cmd == 'dump1090-mutability':
                # dump1090-mutability automatically detects RTL-SDR and uses SBS on port 30003
                cmd.extend(['--net', '--net-sbs-port', '30003'])
            else:  # dump1090
                cmd.extend(['--device-type', 'rtlsdr', '--net', '--net-http-port', '8080'])

            cmd.extend([
                '--quiet',
                '--fix',
                '--metric',
                '--max-range', '200'
            ])

            print(f"Starting {dump1090_cmd}...", flush=True)
            self.readsb_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid
            )

            # Wait for startup
            time.sleep(5)

            if self.readsb_process.poll() is None:
                print("✓ ADS-B decoder started successfully", flush=True)
                print("📡 ADS-B receiver active on 1090 MHz", flush=True)

                # Test API
                try:
                    response = requests.get('http://localhost:8081/data.json', timeout=3)
                    if response.status_code == 200:
                        data = response.json()
                        aircraft_count = len(data.get('aircraft', []))
                        print(f"✓ JSON API responding - {aircraft_count} aircraft detected", flush=True)
                    else:
                        print(f"⚠ JSON API status {response.status_code}", flush=True)
                except Exception as api_err:
                    print(f"⚠ JSON API test failed: {api_err}", flush=True)

                self.running = True
                self.start_time = time.time()
                threading.Thread(target=self._collect_aircraft_data, daemon=True).start()
                return True
            else:
                stdout, stderr = self.readsb_process.communicate()
                print("✗ ADS-B decoder failed to start", flush=True)
                if stderr:
                    stderr_text = stderr.decode()
                    print(f"Error: {stderr_text[:300]}", flush=True)
                return self._fail_gracefully()

        except Exception as e:
            print(f"Failed to start ADS-B service: {e}", flush=True)
            return self._fail_gracefully()

    def _parse_sbs_data(self, sbs_text: str) -> Dict[str, Dict]:
        """Parse SBS (BaseStation) format data into aircraft dictionary."""
        aircraft_data = {}

        lines = sbs_text.strip().split('\n')
        for line in lines:
            if not line.strip():
                continue

            fields = line.split(',')
            if len(fields) < 10:
                continue

            # SBS format fields:
            # 0: Message type (MSG)
            # 1: Transmission type
            # 2: Session ID
            # 3: Aircraft ID
            # 4: ICAO hex
            # 5: Flight ID
            # 6: Date (YYYY/MM/DD)
            # 7: Time (HH:MM:SS.sss)
            # 8: Callsign
            # 9: Altitude
            # 10: Ground speed
            # 11: Track
            # 12: Latitude
            # 13: Longitude
            # 14: Vertical rate
            # etc.

            try:
                msg_type = fields[0]
                if msg_type != 'MSG':
                    continue

                transmission_type = fields[1] if len(fields) > 1 else ''
                icao = fields[4].upper() if len(fields) > 4 else ''
                if not icao or len(icao) != 6:
                    continue

                # Get or create aircraft entry
                if icao not in aircraft_data:
                    aircraft_data[icao] = {
                        'icao': icao,
                        'last_update': datetime.now()
                    }

                aircraft_info = aircraft_data[icao]

                # Parse based on transmission type
                if transmission_type == '1' and len(fields) > 10:  # Identification
                    callsign = fields[10].strip() if fields[10] else None
                    if callsign:
                        aircraft_info['callsign'] = callsign

                elif transmission_type == '3' and len(fields) > 16:  # Airborne position
                    # dump1090-mutability SBS format: altitude at field 12, lat at 15, lon at 16
                    if len(fields) > 12 and fields[12]:
                        try:
                            aircraft_info['alt'] = float(fields[12])
                        except ValueError:
                            pass
                    if len(fields) > 15 and fields[15]:
                        try:
                            aircraft_info['lat'] = float(fields[15])
                        except ValueError:
                            pass
                    if len(fields) > 16 and fields[16]:
                        try:
                            aircraft_info['lon'] = float(fields[16])
                        except ValueError:
                            pass

                elif transmission_type == '4' and len(fields) > 13:  # Airborne velocity
                    # dump1090-mutability SBS format: speed at field 12, heading at 13
                    if len(fields) > 12 and fields[12]:
                        try:
                            aircraft_info['speed'] = float(fields[12])
                        except ValueError:
                            pass
                    if len(fields) > 13 and fields[13]:
                        try:
                            aircraft_info['heading'] = float(fields[13])
                        except ValueError:
                            pass

                aircraft_info['last_update'] = datetime.now()

            except (IndexError, ValueError):
                # Skip malformed lines
                continue

        return aircraft_data

    def _collect_aircraft_data(self):
        """Collect aircraft data from ADS-B decoder."""
        while self.running:
            try:
                # Check if we have a real ADS-B decoder process running
                if hasattr(self, 'readsb_process') and self.readsb_process and self.readsb_process.poll() is None:
                    # Fetch real aircraft data from decoder
                    # Try multiple possible endpoints based on decoder type
                    data_retrieved = False

                    if self.decoder_cmd == 'dump1090-mutability':
                        # dump1090-mutability uses SBS format on port 30003
                        try:
                            import socket
                            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                            sock.settimeout(2)
                            sock.connect(('localhost', 30003))

                            # SBS format is text-based, read some data
                            data = sock.recv(8192).decode('utf-8', errors='ignore')
                            sock.close()

                                # Debug logging removed for cleaner output
                                # Parse SBS format messages
                                aircraft_data = self._parse_sbs_data(data)
                                aircraft_count = len(aircraft_data)

                                if aircraft_count > 0:
                                    # SBS data parsed successfully
                                else:
                                    print(f"ℹ SBS data received but no aircraft parsed (data length: {len(data)})", flush=True)

                                self.aircraft_data = aircraft_data
                                self.last_update = time.time()
                                data_retrieved = True
                            else:
                                # No SBS data received

                        except Exception as sbs_err:
                                # Connection errors are handled silently
                    else:
                        # Try JSON APIs for other decoders
                        api_urls = [
                            'http://localhost:8081/data.json',  # readsb default
                            'http://localhost:8080/data.json',  # dump1090-fa default
                        ]

                        for api_url in api_urls:
                            try:
                                response = requests.get(api_url, timeout=1)
                                if response.status_code == 200:
                                    data = response.json()
                                    aircraft_list = data.get('aircraft', [])
                                    aircraft_count = len(aircraft_list)

                                    if aircraft_count > 0:
                                        # Data retrieval success - displayed in interface

                                    # Convert decoder format to our internal format
                                    self.aircraft_data = {}
                                    for aircraft in aircraft_list:
                                        icao = aircraft.get('hex', '').upper()
                                        if icao:
                                            self.aircraft_data[icao] = {
                                                'icao': icao,
                                                'callsign': aircraft.get('flight', '').strip() or None,
                                                'lat': aircraft.get('lat'),
                                                'lon': aircraft.get('lon'),
                                                'alt': aircraft.get('alt_geom') or aircraft.get('alt_baro'),
                                                'speed': aircraft.get('gs'),
                                                'heading': aircraft.get('track'),
                                                'vertical_rate': aircraft.get('baro_rate') or aircraft.get('geom_rate'),
                                                'last_update': datetime.now()
                                            }
                                    self.last_update = time.time()
                                    data_retrieved = True
                                    break  # Success, stop trying other URLs
                                else:
                                    # Try next URL
                                    continue
                            except (requests.RequestException, json.JSONDecodeError):
                                # Try next URL
                                continue

                    if not data_retrieved:
                        # Could not retrieve data - will show no aircraft in interface
                        # Check if the decoder process is still running
                        if self.readsb_process.poll() is not None:
                            # Decoder process stopped
                        self.aircraft_data = {}
                else:
                    # No ADS-B decoder available - cannot provide real data
                    self.aircraft_data = {}
                    self.last_update = time.time()
                    # No decoder available

            except Exception as e:
                    # Error in data collection - continuing
                self.aircraft_data = {}

            time.sleep(2)  # Update every 2 seconds

    def stop_service(self):
        """Stop the ADS-B service."""
        print("Stopping ADS-B service...", flush=True)
        self.running = False

        # Stop ADS-B decoder process if running
        if hasattr(self, 'readsb_process') and self.readsb_process and self.readsb_process.poll() is None:
            try:
                os.killpg(os.getpgid(self.readsb_process.pid), signal.SIGTERM)
                self.readsb_process.wait(timeout=5)
                print("✓ ADS-B decoder process stopped", flush=True)
            except (subprocess.TimeoutExpired, ProcessLookupError, OSError) as e:
                print(f"Warning: Error stopping ADS-B decoder: {e}", flush=True)
                try:
                    self.readsb_process.kill()
                except:
                    pass

        print("✓ ADS-B service stopped", flush=True)

    def get_status(self) -> Dict:
        """Get service status and aircraft data."""
        return {
            'running': self.running,
            'aircraft_count': len(self.aircraft_data),
            'aircraft': list(self.aircraft_data.values()),  # Include actual aircraft data
            'uptime': time.time() - self.start_time if hasattr(self, 'start_time') else 0,
            'last_update': self.last_update
        }

    def get_aircraft_data(self) -> Dict[str, Dict]:
        """Get current aircraft data."""
        return self.aircraft_data.copy()


def run_text_interface(service: ADSBService):
    """Run the text-based ADS-B interface."""
    print("ADS-B Aircraft Tracker")
    print("Real-time aircraft surveillance on 1090 MHz")
    print("Press Ctrl+C or 'q' to quit")
    print()

    last_display = 0
    try:
        while service.running:
            current_time = time.time()
            status = service.get_status()

            # Update display every 2 seconds
            if current_time - last_display >= 2:
                # Clear screen and show aircraft data
                print("\033[2J\033[H", end="")  # Clear screen and move to top
                print("ADS-B Aircraft Tracker - Real-time Surveillance")
                print("=" * 50)
                print(f"Status: {'Active' if status['running'] else 'Inactive'} | Uptime: {status['uptime']:.0f}s")
                print(f"Aircraft detected: {status['aircraft_count']}")
                print()

                if status['aircraft']:
                    print("Current Aircraft:")
                    print("-" * 80)
                    print(f"{'ICAO':<6} {'Callsign':<10} {'Alt':<8} {'Lat':<10} {'Lon':<11} {'Speed':<6} {'Heading':<8}")
                    print("-" * 80)

                    for aircraft in status['aircraft']:
                        icao = aircraft.get('icao', 'N/A')[:6]
                        callsign = aircraft.get('callsign', 'N/A')[:9] or 'N/A'
                        alt = f"{aircraft.get('alt', 'N/A')}" if aircraft.get('alt') else 'N/A'
                        lat = f"{aircraft.get('lat', 'N/A'):.4f}" if aircraft.get('lat') else 'N/A'
                        lon = f"{aircraft.get('lon', 'N/A'):.4f}" if aircraft.get('lon') else 'N/A'
                        speed = f"{aircraft.get('speed', 'N/A')}" if aircraft.get('speed') else 'N/A'
                        heading = f"{aircraft.get('heading', 'N/A')}" if aircraft.get('heading') else 'N/A'

                        print(f"{icao:<6} {callsign:<10} {alt:<8} {lat:<10} {lon:<11} {speed:<6} {heading:<8}")
                else:
                    print("No aircraft currently detected.")
                    print("Make sure your RTL-SDR is connected and tuned to 1090 MHz.")

                print()
                print("Press Ctrl+C or 'q' to quit")
                last_display = current_time

            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\nStopping ADS-B interface...")
        service.stop_service()


def run_adsb_service(*args, **kwargs):
    """Run the ADS-B service."""
    service = ADSBService()

    try:
        if service.start_service():
            run_text_interface(service)
        else:
            print("Failed to start ADS-B service")
    except KeyboardInterrupt:
        print("\nADS-B service interrupted by user")
        service.stop_service()
    except Exception as e:
        print(f"ADS-B service error: {e}")
        service.stop_service()