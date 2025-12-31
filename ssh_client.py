#!/usr/bin/env python3
"""
SpectrumSnek SSH Client
Command-line client for remote control of SpectrumSnek service
"""

import sys
import os
import argparse
import json
import requests
from typing import Dict, Any, Optional

class SSHClient:
    """Command-line client for SpectrumSnek service."""

    def __init__(self, host: str = '127.0.0.1', port: int = 5000):
        self.base_url = f"http://{host}:{port}"
        self.session = requests.Session()

    def get_tools(self) -> Dict[str, Any]:
        """Get list of available tools."""
        try:
            response = self.session.get(f"{self.base_url}/api/tools", timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error connecting to service: {e}")
            return {}

    def get_status(self) -> Dict[str, Any]:
        """Get service status."""
        try:
            response = self.session.get(f"{self.base_url}/api/status", timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error getting status: {e}")
            return {}

    def start_tool(self, tool_name: str) -> bool:
        """Start a tool."""
        try:
            response = self.session.post(f"{self.base_url}/api/tools/{tool_name}/start", timeout=10)
            if response.status_code == 200:
                print(f"✓ Started {tool_name}")
                return True
            else:
                error_data = response.json()
                print(f"✗ Failed to start {tool_name}: {error_data.get('error', 'Unknown error')}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"✗ Error starting tool: {e}")
            return False

    def stop_tool(self, tool_name: str) -> bool:
        """Stop a tool."""
        try:
            response = self.session.post(f"{self.base_url}/api/tools/{tool_name}/stop", timeout=10)
            if response.status_code == 200:
                print(f"✓ Stopped {tool_name}")
                return True
            else:
                error_data = response.json()
                print(f"✗ Failed to stop {tool_name}: {error_data.get('error', 'Unknown error')}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"✗ Error stopping tool: {e}")
            return False

    def list_tools(self):
        """List all available tools."""
        tools_data = self.get_tools()
        if not tools_data:
            return

        print("Available Tools:")
        print("=" * 50)

        for tool_name, tool_info in tools_data.get('tools', {}).items():
            info = tool_info['info']
            status = tool_info['status']
            status_icon = "🟢" if status == "running" else "🔴"

            print(f"{status_icon} {info['name']}")
            print(f"   {info['description']}")
            print(f"   Status: {status.upper()}")
            print(f"   Version: {info.get('version', 'N/A')} | Author: {info.get('author', 'N/A')}")
            print()

    def show_status(self):
        """Show service status."""
        status_data = self.get_status()
        if not status_data:
            return

        print("Service Status:")
        print("=" * 30)
        print(f"Status: {status_data.get('status', 'unknown').upper()}")
        print(f"Tools Loaded: {status_data.get('tools_loaded', 0)}")
        print(f"Tools Running: {status_data.get('tools_running', 0)}")

    def show_tool_status(self, tool_name: str):
        """Show detailed status of a specific tool."""
        try:
            response = self.session.get(f"{self.base_url}/api/tools/{tool_name}/status", timeout=10)
            response.raise_for_status()
            tool_status = response.json()

            print(f"Tool: {tool_status['name']}")
            print("=" * 40)
            print(f"Description: {tool_status['description']}")
            print(f"Status: {tool_status['status'].upper()}")
            print(f"Is Running: {'Yes' if tool_status['is_running'] else 'No'}")

            if tool_status.get('runtime'):
                print(f"Runtime: {tool_status['runtime']:.1f} seconds")
            if tool_status.get('thread_alive') is not None:
                print(f"Thread Alive: {tool_status['thread_alive']}")

        except requests.exceptions.RequestException as e:
            print(f"Error getting tool status: {e}")

    def get_config(self) -> Dict[str, Any]:
        """Get current configuration."""
        try:
            response = self.session.get(f"{self.base_url}/api/config", timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error getting config: {e}")
            return {}

    def update_config(self, key_path: str, value: Any) -> bool:
        """Update configuration value."""
        try:
            response = self.session.post(f"{self.base_url}/api/config", json={key_path: value}, timeout=10)
            response.raise_for_status()
            print(f"✓ Updated {key_path} = {value}")
            return True
        except requests.exceptions.RequestException as e:
            print(f"✗ Error updating config: {e}")
            return False

    def show_config(self):
        """Show current configuration."""
        config = self.get_config()
        if not config:
            return

        print("Current Configuration:")
        print("=" * 50)
        print(json.dumps(config, indent=2))

def main():
    parser = argparse.ArgumentParser(description="SpectrumSnek SSH Client")
    parser.add_argument('--host', default='127.0.0.1', help='Service host (default: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=5000, help='Service port (default: 5000)')
    parser.add_argument('--list', action='store_true', help='List available tools')
    parser.add_argument('--status', action='store_true', help='Show service status')
    parser.add_argument('--start', help='Start a specific tool')
    parser.add_argument('--stop', help='Stop a specific tool')
    parser.add_argument('--tool-status', help='Show detailed status of a specific tool')
    parser.add_argument('--config', action='store_true', help='Show current configuration')
    parser.add_argument('--set-config', nargs=2, metavar=('KEY', 'VALUE'), help='Set configuration value (e.g., service.port 5001)')

    args = parser.parse_args()

    client = SSHClient(args.host, args.port)

    if args.list:
        client.list_tools()
    elif args.status:
        client.show_status()
    elif args.start:
        success = client.start_tool(args.start)
        sys.exit(0 if success else 1)
    elif args.stop:
        success = client.stop_tool(args.stop)
        sys.exit(0 if success else 1)
    elif args.tool_status:
        client.show_tool_status(args.tool_status)
    elif args.config:
        client.show_config()
    elif args.set_config:
        key, value = args.set_config
        # Try to parse value as JSON, fallback to string
        try:
            parsed_value = json.loads(value)
        except json.JSONDecodeError:
            parsed_value = value
        client.update_config(key, parsed_value)
    else:
        # Interactive mode
        print("SpectrumSnek SSH Client")
        print("Connecting to:", client.base_url)
        print()

        while True:
            print("Commands:")
            print("  list          - List available tools")
            print("  status        - Show service status")
            print("  tool <name>   - Show detailed tool status")
            print("  config        - Show current configuration")
            print("  set <key> <value> - Set configuration value")
            print("  start <tool>  - Start a tool")
            print("  stop <tool>   - Stop a tool")
            print("  quit          - Exit")
            print()

            try:
                cmd = input("ssh> ").strip().split()
                if not cmd:
                    continue

                command = cmd[0].lower()

                if command == 'quit' or command == 'q':
                    break
                elif command == 'list' or command == 'ls':
                    client.list_tools()
                elif command == 'status' or command == 'st':
                    client.show_status()
                elif command == 'start' and len(cmd) > 1:
                    client.start_tool(cmd[1])
                elif command == 'stop' and len(cmd) > 1:
                    client.stop_tool(cmd[1])
                elif command == 'tool' and len(cmd) > 1:
                    client.show_tool_status(cmd[1])
                elif command == 'config':
                    client.show_config()
                elif command == 'set' and len(cmd) > 2:
                    key = cmd[1]
                    value_str = ' '.join(cmd[2:])
                    # Try to parse value as JSON
                    try:
                        value = json.loads(value_str)
                    except json.JSONDecodeError:
                        value = value_str
                    client.update_config(key, value)
                else:
                    print("Invalid command. Type 'help' for available commands.")
                    print()

            except KeyboardInterrupt:
                print("\nExiting...")
                break
            except EOFError:
                break

if __name__ == "__main__":
    main()