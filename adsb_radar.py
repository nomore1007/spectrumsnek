#!/usr/bin/env python3
"""Compatibility entry point. The actual ADS-B radar lives in the plugin."""
import argparse
import curses
from plugins.adsb_radar import run
from plugins.adsb_radar.radar import AIRCRAFT_JSON, main

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SpectrumSnek ADS-B radar plugin")
    parser.add_argument("--file", default=AIRCRAFT_JSON, help="readsb aircraft.json path")
    parser.add_argument("--interval", type=int, default=1000, help="refresh interval in ms")
    args = parser.parse_args()
    # Explicit file/interval remain supported for users of the old script.
    from plugins.adsb_radar import radar
    import os
    if os.environ.get("SPECTRUMSNEK_EXTERNAL_READSB") == "1":
        curses.wrapper(main, args)
    else:
        run()
