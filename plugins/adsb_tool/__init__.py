"""
ADS-B Tool Module - SpectrumSnek 🐍📻
Aircraft surveillance and tracking using RTL-SDR.
"""

__version__ = "1.0.0"
__author__ = "SpectrumSnek"

def get_module_info():
    """Get information about this module."""
    return {
        "name": "✈️ ADS-B Aircraft Tracker",
        "description": "Real-time aircraft tracking and surveillance using ADS-B signals - spot planes before you see them!",
        "version": __version__,
        "author": __author__,
        "capabilities": [
            "ADS-B message decoding",
            "Aircraft position tracking",
            "Flight information display",
            "Real-time aircraft map",
            "Flight path recording",
            "Aircraft identification"
        ]
    }

def run():
    """Run the ADS-B tool module."""
    from .adsb_tracker import main
    main()