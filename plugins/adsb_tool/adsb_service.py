"""
ADS-B Aircraft Tracking Service
Real-time aircraft surveillance using RTL-SDR hardware.

This module provides comprehensive ADS-B (Automatic Dependent Surveillance-Broadcast)
aircraft tracking capabilities. It supports multiple ADS-B decoders and provides
real-time aircraft position, altitude, speed, and identification data.

Features:
- Automatic decoder detection and configuration
- Real-time aircraft data collection and persistence
- Text-based interface with live aircraft display
- Multiple SDR device support (RTL-SDR, HackRF, LimeSDR)
- 5-minute aircraft data retention for stable display

Supported Decoders:
- dump1090-mutability (preferred for RTL-SDR)
- dump1090-fa (FlightAware version)
- readsb (fallback option)
- dump1090 (original version)

Usage:
    from adsb_service import ADSBService
    service = ADSBService()
    service.start_service()
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
        """Check if ADS-B decoder (dump1090-mutability, dump1090-fa, dump1090, readsb) is installed."""
        try:
            # Try multiple ADS-B decoders in order of preference
            decoders = ['dump1090-mutability', 'dump1090-fa', 'dump1090', 'readsb']
            for cmd in decoders:
                result = subprocess.run(['which', cmd],
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    print(f"✓ Found ADS-B decoder: {cmd}", flush=True)
                    return True
            print("ℹ No ADS-B decoder found - aircraft detection requires external decoder", flush=True)
            print("  Available options: dump1090-mutability, dump1090-fa, dump1090, readsb", flush=True)
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
        """Handle service startup failure gracefully."""
        print("❌ ADS-B functionality unavailable - no compatible decoder installed", flush=True)
        print("", flush=True)
        print("ADS-B requires compatible hardware or decoder software.", flush=True)
        print("For RTL-SDR users: Install dump1090-mutability or dump1090-fa", flush=True)
        print("For dedicated ADS-B receivers: Install readsb", flush=True)
        print("", flush=True)
        print("Run 'sudo apt install dump1090-mutability' for best RTL-SDR compatibility", flush=True)

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
            decoders = ['dump1090-mutability', 'dump1090-fa', 'dump1090', 'readsb']
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

            # Add device and networking options based on decoder and detected SDR
            # Try to detect SDR type for better compatibility
            sdr_type = 'rtlsdr'  # default

            # Check for HackRF
            if os.path.exists('/usr/bin/hackrf_info'):
                try:
                    import subprocess
                    result = subprocess.run(['hackrf_info'], capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        sdr_type = 'hackrf'
                except:
                    pass

            # Check for LimeSDR
            if os.path.exists('/usr/bin/LimeUtil'):
                try:
                    import subprocess
                    result = subprocess.run(['LimeUtil', '--find'], capture_output=True, text=True, timeout=5)
                    if 'LimeSDR' in result.stdout:
                        sdr_type = 'limesdr'
                except:
                    pass

            if dump1090_cmd == 'readsb':
                # readsb can work with RTL-SDR in some configurations
                cmd.extend(['--net', '--net-api-port', '8080'])
            elif dump1090_cmd == 'dump1090-fa':
                cmd.extend(['--device-type', sdr_type, '--net', '--net-ro-port', '8080'])
            elif dump1090_cmd == 'dump1090-mutability':
                # dump1090-mutability automatically detects SDR and uses SBS on port 30003
                cmd.extend(['--net', '--net-sbs-port', '30003'])
            elif dump1090_cmd == 'dump1090':
                # Original dump1090 uses different networking options
                cmd.extend(['--device-index', '0', '--net'])
            else:
                # Fallback
                cmd.extend(['--device-index', '0', '--net'])

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
        AIRCRAFT_TIMEOUT_MINUTES = 5  # Keep aircraft data for 5 minutes

        while self.running:
            try:
                # Check if we have a real ADS-B decoder process running
                if hasattr(self, 'readsb_process') and self.readsb_process and self.readsb_process.poll() is None:
                    # Fetch real aircraft data from decoder
                    # Try multiple possible endpoints based on decoder type
                    data_retrieved = False
                    new_aircraft_data = {}

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

                            if data:
                                # Debug logging removed for cleaner output
                                # Parse SBS format messages
                                parsed_data = self._parse_sbs_data(data)
                                aircraft_count = len(parsed_data)

                                if aircraft_count > 0:
                                    # SBS data parsed successfully
                                    pass
                                else:
                                    print(f"ℹ SBS data received but no aircraft parsed (data length: {len(data)})", flush=True)

                                # Merge with existing data, update timestamps for new/updated aircraft
                                current_time = datetime.now()
                                for icao, aircraft in parsed_data.items():
                                    aircraft['last_update'] = current_time
                                    new_aircraft_data[icao] = aircraft

                                data_retrieved = True
                            else:
                                # No SBS data received
                                pass
                        except Exception as sbs_err:
                            # Connection errors are handled silently
                            pass
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
                                        pass

                                    # Convert decoder format to our internal format and merge
                                    current_time = datetime.now()
                                    for aircraft in aircraft_list:
                                        icao = aircraft.get('hex', '').upper()
                                        if icao:
                                            new_aircraft_data[icao] = {
                                                'icao': icao,
                                                'callsign': aircraft.get('flight', '').strip() or None,
                                                'lat': aircraft.get('lat'),
                                                'lon': aircraft.get('lon'),
                                                'alt': aircraft.get('alt_geom') or aircraft.get('alt_baro'),
                                                'speed': aircraft.get('gs'),
                                                'heading': aircraft.get('track'),
                                                'vertical_rate': aircraft.get('baro_rate') or aircraft.get('geom_rate'),
                                                'last_update': current_time
                                            }
                                    data_retrieved = True
                                    break  # Success, stop trying other URLs
                                else:
                                    # Try next URL
                                    continue
                            except (requests.RequestException, json.JSONDecodeError):
                                # Try next URL
                                continue

                    # Update aircraft database: merge new data with existing, clean up old entries
                    if data_retrieved or not self.aircraft_data:
                        current_time = datetime.now()
                        # Start with existing aircraft data
                        updated_aircraft_data = self.aircraft_data.copy()

                        # Update/add new aircraft data
                        for icao, aircraft in new_aircraft_data.items():
                            updated_aircraft_data[icao] = aircraft

                        # Remove aircraft not seen for more than AIRCRAFT_TIMEOUT_MINUTES
                        to_remove = []
                        for icao, aircraft in updated_aircraft_data.items():
                            if 'last_update' in aircraft:
                                age_minutes = (current_time - aircraft['last_update']).total_seconds() / 60
                                if age_minutes > AIRCRAFT_TIMEOUT_MINUTES:
                                    to_remove.append(icao)

                        for icao in to_remove:
                            del updated_aircraft_data[icao]

                        self.aircraft_data = updated_aircraft_data
                        self.last_update = time.time()

                    if not data_retrieved:
                        # Could not retrieve data - will show existing aircraft data
                        # Check if the decoder process is still running
                        if self.readsb_process.poll() is not None:
                            # Decoder process stopped
                            self.aircraft_data = {}
                else:
                    # No ADS-B decoder available - cannot provide data
                    self.aircraft_data = {}
                    self.last_update = time.time()

            except Exception as e:
                # Error in data collection - continuing
                self.aircraft_data = {}

            time.sleep(2)  # Update every 2 seconds

    def stop_service(self):
        """
        Stop the ADS-B service and clean up resources.

        This method gracefully shuts down the ADS-B service:
        1. Terminates the background data collection thread
        2. Stops the ADS-B decoder process
        3. Cleans up aircraft data cache
        4. Resets service state for potential restart

        Safe to call multiple times or when service is not running.
        """
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
    """
    Run the text-based ADS-B aircraft tracking interface.

    Provides an interactive terminal interface for monitoring ADS-B aircraft.
    Displays real-time aircraft data in a table format with automatic updates.
    Supports keyboard quit ('q') and preserves last-known data values.

    Args:
        service (ADSBService): The ADS-B service instance to monitor

    Interface Features:
    - Real-time aircraft table with ICAO, callsign, position, altitude
    - 2-second refresh rate for smooth updates
    - Persistent data display (shows last known values)
    - Aircraft count and service status
    - Graceful keyboard interrupt handling

    Key Bindings:
    - 'q': Quit the interface
    - Ctrl+C: Force quit
    """
    import select
    import sys
    import termios
    import tty

    print("ADS-B Aircraft Tracker")
    print("Real-time aircraft surveillance on 1090 MHz")
    print("Press Ctrl+C or 'q' to quit")
    print()

    # Set up terminal for non-blocking input
    old_settings = termios.tcgetattr(sys.stdin)
    tty.setcbreak(sys.stdin.fileno())

    last_display = 0
    try:
        while service.running:
            current_time = time.time()
            status = service.get_status()

            # Check for 'q' key press
            if select.select([sys.stdin], [], [], 0)[0]:
                key = sys.stdin.read(1)
                if key.lower() == 'q':
                    break

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
                        icao = aircraft.get('icao', '')[:6]
                        callsign = aircraft.get('callsign', '')[:9] or ''
                        alt = f"{aircraft.get('alt', '')}" if aircraft.get('alt') is not None else ''
                        lat = f"{aircraft.get('lat', ''):.4f}" if aircraft.get('lat') is not None else ''
                        lon = f"{aircraft.get('lon', ''):.4f}" if aircraft.get('lon') is not None else ''
                        speed = f"{aircraft.get('speed', '')}" if aircraft.get('speed') is not None else ''
                        heading = f"{aircraft.get('heading', '')}" if aircraft.get('heading') is not None else ''

                        print(f"{icao:<6} {callsign:<10} {alt:<8} {lat:<10} {lon:<11} {speed:<6} {heading:<8}")
                else:
                    print("No aircraft currently detected.")
                    print("Make sure your RTL-SDR is connected and tuned to 1090 MHz.")

                print()
                print("Press Ctrl+C or 'q' to quit")
                last_display = current_time

            time.sleep(0.1)

    except KeyboardInterrupt:
        pass
    finally:
        # Restore terminal settings
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
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