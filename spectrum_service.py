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
from typing import Dict, List, Any, Optional
from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class SpectrumService:
    """Core service for managing radio tools."""

    def __init__(self):
        self.app = Flask(__name__)
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        self.tools: Dict[str, Any] = {}
        self.running_tools: Dict[str, Any] = {}
        self.load_tools()

        # Setup routes
        self.setup_routes()

    def load_tools(self):
        """Load available tools from plugins and system tools."""
        # Load plugins
        plugins_dir = "plugins"
        if os.path.exists(plugins_dir):
            for item in os.listdir(plugins_dir):
                plugin_path = os.path.join(plugins_dir, item)
                if os.path.isdir(plugin_path) and not item.startswith('__'):
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

        # Audio tool
        try:
            from system_tools.audio_output_selector import AudioOutputSelector
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

            try:
                # Start tool in background thread
                def run_tool():
                    try:
                        self.running_tools[tool_name] = {'status': 'running', 'thread': threading.current_thread()}
                        self.tools[tool_name]['status'] = 'running'
                        self.socketio.emit('tool_update', {'tool': tool_name, 'status': 'running'})

                        # Run the tool
                        tool_data = self.tools[tool_name]
                        if 'run_func' in tool_data:
                            tool_data['run_func']()
                        else:
                            tool_data['module'].run()

                    except Exception as e:
                        print(f"Tool {tool_name} error: {e}")
                    finally:
                        if tool_name in self.running_tools:
                            del self.running_tools[tool_name]
                        self.tools[tool_name]['status'] = 'stopped'
                        self.socketio.emit('tool_update', {'tool': tool_name, 'status': 'stopped'})

                thread = threading.Thread(target=run_tool, daemon=True)
                thread.start()

                return jsonify({'status': 'starting'})

            except Exception as e:
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/tools/<tool_name>/stop', methods=['POST'])
        def stop_tool(tool_name):
            """Stop a tool."""
            if tool_name not in self.running_tools:
                return jsonify({'error': 'Tool not running'}), 400

            # Note: Stopping threads is complex, for now just mark as stopped
            # In real implementation, need proper shutdown mechanism
            self.tools[tool_name]['status'] = 'stopped'
            if tool_name in self.running_tools:
                del self.running_tools[tool_name]
            self.socketio.emit('tool_update', {'tool': tool_name, 'status': 'stopped'})

            return jsonify({'status': 'stopped'})

        @self.app.route('/api/status', methods=['GET'])
        def get_status():
            """Get service status."""
            return jsonify({
                'status': 'running',
                'tools_loaded': len(self.tools),
                'tools_running': len(self.running_tools)
            })

    def run(self, host='127.0.0.1', port=5000):
        """Run the service."""
        print(f"Starting SpectrumSnek Service on {host}:{port}")
        self.socketio.run(self.app, host=host, port=port, debug=False)

if __name__ == '__main__':
    service = SpectrumService()
    service.run()