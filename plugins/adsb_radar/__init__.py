"""ADS-B radar plugin using readsb as the only ADS-B decoder."""
import argparse
import curses
import os

from sdr_manager import SDRManager, SDRBusyError
from . import radar


def get_module_info():
    return {
        "name": "✈️ ADS-B Radar",
        "description": "Live aircraft radar using readsb and the shared RTL-SDR manager",
        "version": "2.0.0",
        "author": "SpectrumSnek",
        "category": "radio",
        "capabilities": ["readsb-backed ADS-B", "terminal radar", "shared SDR ownership"],
    }


def run(stdscr=None, *args, **kwargs):
    """Run the radar. Compatible with local menus and the service's curses wrapper."""
    # Some older menu code passes "--text" positionally rather than a curses window.
    if stdscr is not None and not hasattr(stdscr, "getch"):
        stdscr = None

    manager = SDRManager()
    json_path = os.environ.get(
        "SPECTRUMSNEK_AIRCRAFT_JSON",
        os.path.join(manager.json_dir, "aircraft.json"),
    )
    try:
        # Only start a decoder when this plugin owns the receiver. The manager
        # refuses to kill or take over a decoder started by another application.
        json_path = manager.start_readsb()
        radar_args = argparse.Namespace(file=json_path, interval=1000)
        if stdscr is None:
            curses.wrapper(radar.main, radar_args)
        else:
            radar.main(stdscr, radar_args)
    finally:
        manager.stop_readsb()


if __name__ == "__main__":
    run()
