#!/usr/bin/env python3
"""
SpectrumSnek Configuration Manager
Handles loading, saving, and managing application configuration
"""

import json
import os
from typing import Dict, Any, Optional

class ConfigManager:
    """Manages application configuration with persistence."""

    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.config: Dict[str, Any] = {}
        self.load_config()

    def load_config(self) -> bool:
        """Load configuration from file."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
                print(f"Loaded configuration from {self.config_file}")
                return True
            else:
                print(f"Configuration file {self.config_file} not found, using defaults")
                self._create_default_config()
                return False
        except Exception as e:
            print(f"Error loading configuration: {e}")
            self._create_default_config()
            return False

    def save_config(self) -> bool:
        """Save current configuration to file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            print(f"Saved configuration to {self.config_file}")
            return True
        except Exception as e:
            print(f"Error saving configuration: {e}")
            return False

    def _create_default_config(self):
        """Create default configuration."""
        self.config = {
            "service": {
                "host": "0.0.0.0",
                "port": 5000,
                "auto_start_tools": [],
                "max_concurrent_tools": 3
            },
            "web_interface": {
                "enabled": True,
                "theme": "dark",
                "refresh_interval": 5
            },
            "tools": {
                "rtl_scanner": {
                    "default_frequency": 100000000,
                    "default_gain": 20,
                    "sample_rate": 2048000
                },
                "adsb_tool": {
                    "default_frequency": 1090000000,
                    "gain": 40,
                    "location": {
                        "latitude": None,
                        "longitude": None
                    }
                }
            },
            "system": {
                "log_level": "INFO",
                "data_directory": "./data",
                "temp_directory": "/tmp/spectrumsnek"
            }
        }

    def get(self, key_path: str, default: Any = None) -> Any:
        """Get configuration value by dot-separated key path."""
        keys = key_path.split('.')
        value = self.config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    def set(self, key_path: str, value: Any) -> bool:
        """Set configuration value by dot-separated key path."""
        keys = key_path.split('.')
        config = self.config

        # Navigate to the parent of the final key
        for key in keys[:-1]:
            if key not in config or not isinstance(config[key], dict):
                config[key] = {}
            config = config[key]

        # Set the final value
        config[keys[-1]] = value

        # Auto-save after setting
        return self.save_config()

    def get_service_config(self) -> Dict[str, Any]:
        """Get service-specific configuration."""
        return self.config.get('service', {})

    def get_tool_config(self, tool_name: str) -> Dict[str, Any]:
        """Get configuration for a specific tool."""
        return self.config.get('tools', {}).get(tool_name, {})

    def update_tool_config(self, tool_name: str, config: Dict[str, Any]) -> bool:
        """Update configuration for a specific tool."""
        if 'tools' not in self.config:
            self.config['tools'] = {}

        self.config['tools'][tool_name] = config
        return self.save_config()

    def list_tools_config(self) -> Dict[str, Any]:
        """Get all tool configurations."""
        return self.config.get('tools', {})

# Global configuration instance
config_manager = ConfigManager()

if __name__ == "__main__":
    # Test the configuration manager
    config = ConfigManager()

    print("Current service host:", config.get('service.host'))
    print("RTL scanner frequency:", config.get('tools.rtl_scanner.default_frequency'))

    # Test setting a value
    config.set('service.port', 5001)
    print("Updated port:", config.get('service.port'))