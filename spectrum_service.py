#!/usr/bin/env python3
"""
SpectrumSnek Service - Core service for radio tools management
Provides API for tool control and monitoring
"""

import sys
import os
import time
import threading
import json
import subprocess
import shlex
from typing import Dict, List, Any, Optional
from flask import Flask, request, jsonify
import psutil

# Import configuration manager
from config_manager import config_manager

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class SpectrumService:
    """Core service for managing radio tools."""

    def __init__(self):
        self.app = Flask(__name__)
        self.tools: Dict[str, Any] = {}
        self.running_tools: Dict[str, Any] = {}
        self.config = config_manager
        self.max_concurrent_tools = self.config.get('service.max_concurrent_tools', 1)
        self.start_time = time.time()  # Track service start time
        self.load_tools()

        # Setup routes
        self.setup_routes()

        # Start periodic status updates
        self.status_thread = threading.Thread(target=self._periodic_status_updates, daemon=True)
        self.status_thread.start()

    def load_tools(self):
        """Load the same built-in tools and installed plugins as other interfaces."""
        from spectrum_core import tool_catalog
        import importlib

        self.tools.clear()
        for entry in tool_catalog():
            name = entry["id"]
            info = {
                "name": entry["name"],
                "description": entry["description"],
                "version": entry.get("version", "1.0.0"),
                "author": entry.get("author", "SpectrumSnek"),
            }
            try:
                module = importlib.import_module(f"plugins.{name}") if name != "system_tools" else None
            except Exception as exc:
                print(f"Could not import tool {name}: {exc}")
                module = None
            self.tools[name] = {
                "info": info,
                "module": module,
                "status": "stopped",
                "command": entry["command"],
            }
            print(f"Loaded tool: {info['name']} ({name})")

    def add_system_tools(self):
        """Add built-in system tools."""
        # System Tools submenu
        try:
            from plugins.system_tools.system_menu import SystemMenu
            info = {
                'name': '🔧 System Tools',
                'description': 'WiFi, Bluetooth, and system utilities',
                'version': '1.0.0',
                'author': 'SpectrumSnek'
            }
            self.tools['system_tools'] = {
                'info': info,
                'module': None,
                'status': 'stopped'
            }
            print(f"Loaded system tool: {info['name']}")
        except ImportError as e:
            print(f"Failed to load system tools menu: {e}")
        except Exception as e:
            print(f"Error loading system tools: {e}")

    def setup_routes(self):
        """Setup Flask routes."""

        @self.app.route('/', methods=['GET'])
        def serve_web_client():
            """Serve the web client interface."""
            try:
                with open('web_client.html', 'r') as f:
                    return f.read(), 200, {'Content-Type': 'text/html'}
            except FileNotFoundError:
                return "Web client not found. Make sure web_client.html exists.", 404



        @self.app.route('/api/tools', methods=['GET'])
        def get_tools():
            """Get list of available tools."""
            return jsonify({
                'tools': {
                    name: {
                        'info': tool['info'],
                        'status': tool['status']
                    } for name, tool in self.tools.items()
                }
            })

        @self.app.route('/api/tools/<tool_name>/start', methods=['POST'])
        def start_tool(tool_name):
            """Start a tool."""
            if tool_name not in self.tools:
                return jsonify({'error': 'Tool not found'}), 404

            if tool_name in self.running_tools:
                return jsonify({'error': 'Tool already running'}), 400

            # Check concurrent tool limit
            if len(self.running_tools) >= self.max_concurrent_tools:
                return jsonify({
                    'error': f'Maximum concurrent tools ({self.max_concurrent_tools}) reached'
                }), 400

            try:
                tool_data = self.tools[tool_name]

                if 'run_func' in tool_data:
                    # For simple system tools, run in thread
                    def run_tool():
                        try:
                            start_time = time.time()
                            self.running_tools[tool_name] = {
                                'status': 'running',
                                'thread': threading.current_thread(),
                                'start_time': start_time,
                                'pid': os.getpid()
                            }
                            self.tools[tool_name]['status'] = 'running'
                            tool_data['run_func']()
                        except Exception as e:
                            print(f"Tool {tool_name} error: {e}")
                        finally:
                            if tool_name in self.running_tools:
                                del self.running_tools[tool_name]
                            self.tools[tool_name]['status'] = 'stopped'

                    thread = threading.Thread(target=run_tool, daemon=True)
                    thread.start()
                else:
                    # For interactive tools, start in tmux session or subprocess
                    project_root = os.path.dirname(os.path.abspath(__file__))
                    venv_activate = os.path.join(project_root, 'venv', 'bin', 'activate')
                    command = " ".join(shlex.quote(part) for part in tool_data["command"])
                    cmd = f'cd {shlex.quote(project_root)} && if [ -f {shlex.quote(venv_activate)} ]; then source {shlex.quote(venv_activate)}; fi && PYTHONPATH={shlex.quote(project_root)} {command}'

                    if self._tmux_available():
                        tmux_cmd = [
                            'tmux', 'new-session', '-d', '-s', f'spectrum-{tool_name}',
                            'bash', '-c', cmd
                        ]
                        try:
                            subprocess.run(tmux_cmd, check=True)
                            # Wait a bit and check if session exists
                            time.sleep(1)
                            result = subprocess.run(['tmux', 'has-session', '-t', f'spectrum-{tool_name}'], capture_output=True)
                            if result.returncode == 0:
                                self.running_tools[tool_name] = {
                                    'status': 'running',
                                    'tmux_session': f'spectrum-{tool_name}',
                                    'start_time': time.time()
                                }
                                self.tools[tool_name]['status'] = 'running'
                            else:
                                return jsonify({'error': 'Tool failed to start (session did not persist)'}), 500
                        except subprocess.CalledProcessError as e:
                            return jsonify({'error': f'Failed to start tool in tmux: {e}'}), 500
                        except FileNotFoundError:
                            return jsonify({'error': 'tmux not available'}), 500
                    else:
                        # Fallback: run in subprocess without tmux
                        try:
                            proc = subprocess.Popen(['bash', '-c', cmd])
                            self.running_tools[tool_name] = {
                                'status': 'running',
                                'process': proc,
                                'start_time': time.time()
                            }
                            self.tools[tool_name]['status'] = 'running'
                        except Exception as e:
                            return jsonify({'error': f'Failed to start tool: {e}'}), 500

                return jsonify({'status': 'starting'})

            except Exception as e:
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/tools/<tool_name>/stop', methods=['POST'])
        def stop_tool(tool_name):
            """Stop a tool."""
            if tool_name not in self.running_tools:
                return jsonify({'error': 'Tool not running'}), 400

            running_info = self.running_tools[tool_name]

            if 'tmux_session' in running_info:
                # Stop tmux session
                try:
                    subprocess.run(['tmux', 'kill-session', '-t', running_info['tmux_session']], check=True)
                except subprocess.CalledProcessError:
                    pass  # Session may already be dead
            elif 'process' in running_info:
                # Stop subprocess
                proc = running_info['process']
                if proc and proc.poll() is None:
                    proc.terminate()
                    try:
                        proc.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        proc.kill()
            else:
                # Stop thread
                thread = running_info.get('thread')
                if thread and thread.is_alive():
                    pass  # Let thread finish

            self.tools[tool_name]['status'] = 'stopped'
            if tool_name in self.running_tools:
                del self.running_tools[tool_name]

            return jsonify({'status': 'stopped'})

        @self.app.route('/api/tools/<tool_name>/status', methods=['GET'])
        def get_tool_status(tool_name):
            """Get detailed status of a specific tool."""
            if tool_name not in self.tools:
                return jsonify({'error': 'Tool not found'}), 404

            tool_data = self.tools[tool_name]
            status_info = {
                'name': tool_data['info']['name'],
                'status': tool_data['status'],
                'description': tool_data['info']['description'],
                'is_running': tool_name in self.running_tools
            }

            if tool_name in self.running_tools:
                running_info = self.running_tools[tool_name]
                if 'tmux_session' in running_info:
                    # Check tmux session
                    try:
                        result = subprocess.run(['tmux', 'has-session', '-t', running_info['tmux_session']],
                                              capture_output=True)
                        is_alive = result.returncode == 0
                    except:
                        is_alive = False
                    status_info.update({
                        'session_alive': is_alive,
                        'tmux_session': running_info['tmux_session'],
                        'start_time': running_info.get('start_time'),
                        'runtime': time.time() - running_info.get('start_time', time.time())
                    })
                else:
                    thread = running_info.get('thread')
                    status_info.update({
                        'thread_alive': thread.is_alive() if thread else False,
                        'start_time': running_info.get('start_time'),
                        'runtime': time.time() - running_info.get('start_time', time.time())
                    })

            return jsonify(status_info)

        # Backwards-compatible ADS-B API aliases. The plugin is now managed through
        # the same lifecycle as every other tool.
        @self.app.route('/api/adsb/start', methods=['POST'])
        def start_adsb_service():
            return start_tool('adsb_radar')

        @self.app.route('/api/adsb/stop', methods=['POST'])
        def stop_adsb_service():
            return stop_tool('adsb_radar')

        @self.app.route('/api/adsb/status', methods=['GET'])
        def get_adsb_status():
            return get_tool_status('adsb_radar')

        @self.app.route('/api/adsb/aircraft', methods=['GET'])
        def get_adsb_aircraft():
            path = os.environ.get('SPECTRUMSNEK_AIRCRAFT_JSON',
                                  '/tmp/spectrumsnek/readsb/aircraft.json')
            try:
                with open(path, 'r', encoding='utf-8') as handle:
                    data = json.load(handle)
                aircraft = data.get('aircraft', [])
                return jsonify({'aircraft_count': len(aircraft), 'aircraft': aircraft})
            except (OSError, ValueError):
                return jsonify({'aircraft_count': 0, 'aircraft': []})

        @self.app.route('/api/system/status', methods=['GET'])
        def get_system_status():
            """Get system status information."""
            try:
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')

                return jsonify({
                    'cpu_percent': cpu_percent,
                    'memory': {
                        'total': memory.total,
                        'available': memory.available,
                        'percent': memory.percent
                    },
                    'disk': {
                        'total': disk.total,
                        'free': disk.free,
                        'percent': disk.percent
                    },
                    'uptime': time.time() - self.start_time
                })
            except Exception as e:
                return jsonify({'error': str(e)}), 500

    def _periodic_status_updates(self):
        """Send periodic status updates and perform health checks."""
        last_health_check = time.time()

        while True:
            try:
                current_time = time.time()

                # Send system info update (would go to WebSocket clients)
                system_info = self._get_system_info()

                # Send service status update (would go to WebSocket clients)
                service_status = {
                    'status': 'running',
                    'tools_loaded': len(self.tools),
                    'tools_running': len(self.running_tools),
                    'timestamp': current_time
                }

                # Perform health checks every 30 seconds
                if current_time - last_health_check > 30:
                    self._perform_health_checks()
                    last_health_check = current_time

            except Exception as e:
                print(f"Error in periodic updates: {e}")

            time.sleep(5)  # Update every 5 seconds

    def _perform_health_checks(self):
        """Perform health checks on running tools and clean up dead processes."""
        tools_to_remove = []

        for tool_name, running_info in self.running_tools.items():
            try:
                is_alive = False

                if 'tmux_session' in running_info:
                    # Check tmux session
                    try:
                        result = subprocess.run(['tmux', 'has-session', '-t', running_info['tmux_session']],
                                              capture_output=True, timeout=5)
                        is_alive = result.returncode == 0
                    except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
                        is_alive = False

                    if not is_alive:
                        print(f"Tool {tool_name}: tmux session {running_info['tmux_session']} died, cleaning up")
                        tools_to_remove.append(tool_name)

                elif 'process' in running_info:
                    # Check subprocess
                    proc = running_info['process']
                    if proc.poll() is not None:
                        print(f"Tool {tool_name}: process exited with code {proc.returncode}, cleaning up")
                        tools_to_remove.append(tool_name)
                    else:
                        is_alive = True

                elif 'thread' in running_info:
                    # Check thread
                    thread = running_info['thread']
                    if thread and thread.is_alive():
                        is_alive = True
                    else:
                        print(f"Tool {tool_name}: thread died, cleaning up")
                        tools_to_remove.append(tool_name)

                # Update status if tool is still alive
                if is_alive and tool_name in self.tools:
                    self.tools[tool_name]['status'] = 'running'

            except Exception as e:
                print(f"Error checking health of tool {tool_name}: {e}")
                tools_to_remove.append(tool_name)

        # Clean up dead tools
        for tool_name in tools_to_remove:
            if tool_name in self.running_tools:
                del self.running_tools[tool_name]
            if tool_name in self.tools:
                self.tools[tool_name]['status'] = 'stopped'

    def run(self, host=None, port=None):
        """Run the service."""
        if host is None:
            host = self.config.get('service.host', '0.0.0.0')
        if port is None:
            port = self.config.get('service.port', 5000)

        print(f"Starting SpectrumSnek Service on {host}:{port}")
        print(f"Service started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")

        # Check for existing service first
        if self._check_existing_service(host, port):
            print("ERROR: SpectrumSnek service appears to already be running!")
            print("Use './service_manager.sh status' to check status")
            print("Use './service_manager.sh restart' to restart if needed")
            print("Use './service_manager.sh stop' to stop the service first")
            return

        # Set up signal handlers for graceful shutdown
        def signal_handler(signum, frame):
            print(f"\nReceived signal {signum}, shutting down gracefully...")
            self._graceful_shutdown()
            import sys
            sys.exit(0)

        import signal
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)

        try:
            print("Starting with Flask development server...")
            print("Health check available at: http://127.0.0.1:5000/api/health")
            print("API endpoints available at: http://127.0.0.1:5000/api/")
            print("Press Ctrl+C to stop the service")
            print("-" * 50)

            self.app.run(host=host, port=port, debug=False, threaded=True, use_reloader=False)
        except OSError as e:
            if e.errno == 98:  # Address already in use
                print(f"ERROR: Port {port} is already in use!")
                print("This usually means SpectrumSnek is already running.")
                print("")
                print("Use service manager to control the service:")
                print("  ./service_manager.sh status   # Check status")
                print("  ./service_manager.sh restart  # Restart service")
                print("  ./service_manager.sh stop     # Stop service")
                print("")
                print("To connect as a client:")
                print("  ~/spectrum_ssh.sh             # SSH interface")
                print("  ./run_spectrum.sh             # Console interface")
                print("  http://localhost:5000         # Web interface")
            else:
                print(f"ERROR: Failed to start service: {e}")
            raise
        except Exception as e:
            print(f"ERROR: Unexpected error starting service: {e}")
            raise

    def _graceful_shutdown(self):
        """Perform graceful shutdown of running tools."""
        print("Performing graceful shutdown...")

        # Stop all running tools
        tools_to_stop = list(self.running_tools.keys())
        for tool_name in tools_to_stop:
            try:
                print(f"Stopping tool: {tool_name}")
                self._stop_tool_internal(tool_name)
            except Exception as e:
                print(f"Error stopping tool {tool_name}: {e}")

        print("Shutdown complete")

    def _stop_tool_internal(self, tool_name):
        """Internal method to stop a tool (used during shutdown)."""
        if tool_name not in self.running_tools:
            return

        running_info = self.running_tools[tool_name]

        if 'tmux_session' in running_info:
            # Stop tmux session
            try:
                subprocess.run(['tmux', 'kill-session', '-t', running_info['tmux_session']],
                             check=True, timeout=5)
            except subprocess.CalledProcessError:
                pass  # Session may already be dead
        elif 'process' in running_info:
            # Stop subprocess
            proc = running_info['process']
            if proc and proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
        # Threads will be cleaned up automatically as daemon threads

        self.tools[tool_name]['status'] = 'stopped'
        if tool_name in self.running_tools:
            del self.running_tools[tool_name]

    def _tmux_available(self):
        """Check if tmux is available."""
        try:
            subprocess.run(['tmux', '-V'], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def _check_existing_service(self, host, port):
        """Check if service is already running on the specified host/port."""
        import socket
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0  # 0 means connection successful
        except:
            return False

if __name__ == '__main__':
    service = SpectrumService()
    service.run()