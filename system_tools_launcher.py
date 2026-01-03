#!/usr/bin/env python3
"""
System Tools Launcher - SpectrumSnek 🐍📻
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if __name__ == '__main__':
    try:
        from plugins.system_tools.system_menu import SystemMenu
        menu = SystemMenu()
        menu.run()
    except KeyboardInterrupt:
        print("\nSystem Tools exited.")
    except Exception as e:
        print(f"Error running System Tools: {e}")