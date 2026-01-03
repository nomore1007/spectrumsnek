"""
RTL-SDR Scanner Module - SpectrumSnek 🐍📻
A modular RTL-SDR radio scanner with terminal and web interfaces.
"""

__version__ = "1.0.0"
__author__ = "SpectrumSnek"

def get_module_info():
    """Get information about this module."""
    return {
        "name": "🐍 RTL-SDR Spectrum Analyzer",
        "description": "Real-time RTL-SDR radio spectrum scanner with demodulation - watch signals dance!",
        "version": __version__,
        "author": __author__,
        "capabilities": [
            "Real-time spectrum analysis",
            "Analog demodulation (AM, FM, SSB, CW)",
            "Digital demodulation (DMR)",
            "CTCSS tone detection",
            "Web control interface",
            "Terminal and dual interface modes"
        ]
    }

def run(*args, **kwargs):
    """Run the RTL-SDR scanner module."""
    from .scanner import main
    main()