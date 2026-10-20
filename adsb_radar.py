#!/usr/bin/env python3
"""Compatibility entry point for the ADS-B radar plugin."""
import argparse
import curses
import os

from plugins.adsb_radar import run
from plugins.adsb_radar.radar import AIRCRAFT_JSON, main

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SpectrumSnek ADS-B radar")
    parser.add_argument("--file", default=None, help="Use an existing readsb aircraft.json file")
    parser.add_argument("--interval", type=int, default=1000, help="Refresh interval in ms")
    args = parser.parse_args()

    if args.file:
        # Legacy mode: display an externally managed decoder's JSON without
        # attempting to claim the dongle or terminate that decoder.
        curses.wrapper(main, argparse.Namespace(file=args.file, interval=args.interval))
    else:
        # Default mode delegates decoder lifecycle and SDR ownership to plugin.
        os.environ["SPECTRUMSNEK_RADAR_INTERVAL"] = str(args.interval)
        run()
