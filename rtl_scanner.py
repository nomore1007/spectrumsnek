#!/usr/bin/env python3
"""
RTL-SDR Scanner Module
A modular RTL-SDR scanner that can be called directly or from the main loader.
"""

import sys
import os

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def run_scanner():
    """Run the RTL-SDR scanner module."""
    # Import and run the scanner
    try:
        import rtl_scanner
        rtl_scanner.run()
    except ImportError as e:
        print(f"Error loading RTL-SDR scanner: {e}")
        print("Make sure all dependencies are installed.")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nRTL-SDR Scanner stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"Error running RTL-SDR scanner: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_scanner()