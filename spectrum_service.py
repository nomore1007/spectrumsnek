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
from typing import Dict, List, Any, Optional
from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
import psutil

# Import configuration manager
from config_manager import config_manager

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class SpectrumService:
    """Core service for managing radio tools."""

    def __init__(self):
        self.app = Flask(__name__)
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        self.tools: Dict[str, Any] = {}
        self.running_tools: Dict[str, Any] = {}
        self.config = config_manager
        self.max_concurrent_tools = self.config.get('service.max_concurrent_tools', 1)
        self.load_tools()

        # Setup routes
        self.setup_routes()

        # Start periodic status updates
        self.status_thread = threading.Thread(target=self._periodic_status_updates, daemon=True)
        self.status_thread.start()

    def load_tools(self):
        """Load available tools from plugins and system tools."""
        # Load plugins
        plugins_dir = "plugins"
        if os.path.exists(plugins_dir):
            for item in os.listdir(plugins_dir):
                plugin_path = os.path.join(plugins_dir, item)
                if os.path.isdir(plugin_path) and not item.startswith('__') and item != "system_tools":
                    try:
                        plugin_module = __import__(f"{plugins_dir}.{item}", fromlist=[item])
                        info = plugin_module.get_module_info()
                        self.tools[item] = {
                            'info': info,
                            'module': plugin_module,
                            'status': 'stopped'
                        }
                        print(f"Loaded plugin: {info['name']}")
                    except ImportError:
                        print(f"Failed to load plugin {item}")
                    except Exception as e:
                        print(f"Error loading plugin {item}: {e}")

        # Add system tools
        self.add_system_tools()

        # Set local run functions for interactive tools
        for name, tool in self.tools.items():
            try:
                if name in ['rtl_scanner', 'adsb_tool', 'radio_scanner']:
                    local_module = __import__(f'plugins.{name}', fromlist=['run'])
                    tool['local_run'] = local_module.run
                elif name == 'wifi_tool':
                    import wifi_tool
                    tool['local_run'] = wifi_tool.run
                elif name == 'bluetooth_tool':
                    import bluetooth_tool
                    tool['local_run'] = bluetooth_tool.run
                elif name == 'audio_tool':
                    from plugins.system_tools.audio_output_selector import AudioOutputSelector
                    tool['local_run'] = AudioOutputSelector().run
                # For other system tools, keep as is
            except ImportError:
                pass

    def add_system_tools(self):
        """Add built-in system tools."""
        # WiFi tool
        try:
            import wifi_tool
            info = wifi_tool.get_module_info()
            self.tools['wifi_tool'] = {
                'info': info,
                'module': wifi_tool,
                'status': 'stopped'
            }
            print(f"Loaded system tool: {info['name']}")
        except:
            pass

        # Bluetooth tool
        try:
            import bluetooth_tool
            info = bluetooth_tool.get_module_info()
            self.tools['bluetooth_tool'] = {
                'info': info,
                'module': bluetooth_tool,
                'status': 'stopped'
            }
            print(f"Loaded system tool: {info['name']}")
        except:
            pass

        # WiFi tool
        self.tools['wifi_tool'] = {
            'info': {
                'name': 'WiFi Network Selector',
                'description': 'Select and connect to WiFi networks',
                'version': '1.0.0',
                'author': 'SpectrumSnek'
            },
            'module': None,
            'status': 'stopped',
            'run_func': lambda: print("WiFi tool: Feature not implemented yet")
        }
        print(f"Loaded system tool: {self.tools['wifi_tool']['info']['name']}")

        # Bluetooth tool
        self.tools['bluetooth_tool'] = {
            'info': {
                'name': 'Bluetooth Device Connector',
                'description': 'Connect to Bluetooth devices',
                'version': '1.0.0',
                'author': 'SpectrumSnek'
            },
            'module': None,
            'status': 'stopped',
            'run_func': lambda: print("Bluetooth tool: Feature not implemented yet")
        }
        print(f"Loaded system tool: {self.tools['bluetooth_tool']['info']['name']}")

        # Audio tool
        try:
            from plugins.system_tools.audio_output_selector import AudioOutputSelector
            info = {
                'name': 'Audio Output Selector',
                'description': 'Select and test audio output devices',
                'version': '1.0.0',
                'author': 'SpectrumSnek'
            }
            self.tools['audio_tool'] = {
                'info': info,
                'module': None,
                'status': 'stopped',
                'run_func': lambda: AudioOutputSelector().run()
            }
            print(f"Loaded system tool: {info['name']}")
        except:
            pass

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
            # Update status of running tools
            for name in list(self.running_tools.keys()):
                running_info = self.running_tools[name]
                if 'tmux_session' in running_info:
                    try:
                        subprocess.run(['tmux', 'has-session', '-t', running_info['tmux_session']],
                                      capture_output=True, check=True, timeout=1)
                        self.tools[name]['status'] = 'running'
                    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
                        self.tools[name]['status'] = 'stopped'
                        del self.running_tools[name]
                elif 'process' in running_info:
                    if running_info['process'].poll() is not None:
                        self.tools[name]['status'] = 'stopped'
                        del self.running_tools[name]
                    else:
                        self.tools[name]['status'] = 'running'
                elif 'thread' in running_info:
                    if not running_info['thread'].is_alive():
                        self.tools[name]['status'] = 'stopped'
                        del self.running_tools[name]

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
                            self.socketio.emit('tool_update', {'tool': tool_name, 'status': 'running'})

                            tool_data['run_func']()
                        except Exception as e:
                            print(f"Tool {tool_name} error: {e}")
                        finally:
                            if tool_name in self.running_tools:
                                del self.running_tools[tool_name]
                            self.tools[tool_name]['status'] = 'stopped'
                            self.socketio.emit('tool_update', {'tool': tool_name, 'status': 'stopped'})

                    thread = threading.Thread(target=run_tool, daemon=True)
                    thread.start()
                else:
                    # For interactive tools, start in tmux session or subprocess
                    import_path = f"plugins.{tool_name}" if tool_name in ['rtl_scanner', 'adsb_tool', 'radio_scanner'] else f"system_tools.{tool_name}"
                    cmd = f'cd /home/nomore/spectrumsnek && source venv/bin/activate && env TERM=linux python -c "import curses; from {import_path} import run; curses.wrapper(run)"'

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
                                self.socketio.emit('tool_update', {'tool': tool_name, 'status': 'running'})
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
                            self.socketio.emit('tool_update', {'tool': tool_name, 'status': 'running'})
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
            self.socketio.emit('tool_update', {'tool': tool_name, 'status': 'stopped'})

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

        @self.app.route('/api/status', methods=['GET'])
        def get_status():
            """Get service status."""
            return jsonify({
                'status': 'running',
                'tools_loaded': len(self.tools),
                'tools_running': len(self.running_tools)
            })

        @self.app.route('/api/system', methods=['GET'])
        def get_system_info():
            """Get system information."""
            return jsonify(self._get_system_info())

        @self.app.route('/api/config', methods=['GET'])
        def get_config():
            """Get current configuration."""
            return jsonify(self.config.config)

        @self.app.route('/api/config', methods=['POST'])
        def update_config():
            """Update configuration."""
            try:
                updates = request.get_json()
                for key_path, value in updates.items():
                    self.config.set(key_path, value)
                return jsonify({'status': 'updated'})
            except Exception as e:
                return jsonify({'error': str(e)}), 400

    def _get_system_info(self) -> Dict[str, Any]:
        """Get current system information."""
        try:
            return {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_usage': psutil.disk_usage('/').percent,
                'network_connections': len(psutil.net_connections()),
                'uptime': time.time() - psutil.boot_time()
            }
        except:
            return {'error': 'Could not get system info'}

    def _periodic_status_updates(self):
        """Send periodic status updates via WebSocket."""
        while True:
            try:
                # Send system info update
                system_info = self._get_system_info()
                self.socketio.emit('system_update', system_info)

                # Send service status update
                service_status = {
                    'status': 'running',
                    'tools_loaded': len(self.tools),
                    'tools_running': len(self.running_tools),
                    'timestamp': time.time()
                }
                self.socketio.emit('service_status', service_status)

            except Exception as e:
                print(f"Error in periodic updates: {e}")

            time.sleep(5)  # Update every 5 seconds

    def run(self, host=None, port=None):
        """Run the service."""
        if host is None:
            host = self.config.get('service.host', '0.0.0.0')
        if port is None:
            port = self.config.get('service.port', 5000)

        print(f"Starting SpectrumSnek Service on {host}:{port}")

        # Check for existing service first
        if self._check_existing_service(host, port):
            print("ERROR: SpectrumSnek service appears to already be running!")
            print("Use './service_manager.sh status' to check status")
            print("Use './service_manager.sh restart' to restart if needed")
            print("Use './service_manager.sh stop' to stop the service first")
            return

        try:
            # Use standard Flask server for now (more reliable than eventlet)
            print("Starting with Flask development server...")
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