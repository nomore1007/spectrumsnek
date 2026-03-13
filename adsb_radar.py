#!/usr/bin/env python3
import json
import time
import curses
import math
import os
import sys
import argparse
from datetime import datetime

# Path to aircraft.json from readsb
AIRCRAFT_JSON = "/run/readsb/aircraft.json"

def get_aircraft_data(json_path):
    try:
        if not os.path.exists(json_path):
            return None
        with open(json_path, 'r') as f:
            return json.load(f)
    except Exception:
        return None

def main(stdscr, args):
    # Setup curses
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(args.interval)
    
    # Local aircraft cache for persistence
    # Format: {icao: {data: ..., last_seen: timestamp}}
    aircraft_cache = {}
    PERSISTENCE_TIMEOUT = 60 # seconds to keep old planes
    
    # Color support
    if curses.has_colors():
        curses.start_color()
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)  # Active Planes
        curses.init_pair(2, curses.COLOR_CYAN, curses.COLOR_BLACK)   # Labels
        curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)    # Center
        curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLACK) # Stats
        curses.init_pair(5, curses.COLOR_WHITE, curses.COLOR_BLACK)  # Stale Planes (Dim)
    
    while True:
        stdscr.clear()
        height, width = stdscr.getmaxyx()
        
        if height < 10 or width < 20:
            stdscr.addstr(0, 0, "Terminal too small!")
            stdscr.refresh()
            if stdscr.getch() == ord('q'): break
            continue

        data = get_aircraft_data(args.file)
        current_time = time.time()
        
        # Update cache with new data
        if data and 'aircraft' in data:
            for a in data['aircraft']:
                if 'lat' in a and 'lon' in a:
                    icao = a.get('hex', 'unknown')
                    aircraft_cache[icao] = {
                        'data': a,
                        'last_seen': current_time
                    }
        
        # Clean up very old planes and collect planes to display
        display_aircraft = []
        for icao in list(aircraft_cache.keys()):
            entry = aircraft_cache[icao]
            age = current_time - entry['last_seen']
            if age > PERSISTENCE_TIMEOUT:
                del aircraft_cache[icao]
            else:
                display_aircraft.append(entry)

        if not display_aircraft:
            stdscr.addstr(0, 0, "Waiting for aircraft data...")
            stdscr.addstr(1, 0, f"Checking {args.file}")
            stdscr.refresh()
            if stdscr.getch() == ord('q'): break
            time.sleep(1)
            continue
            
        # Calculate center of the data based on ALL cached planes
        avg_lat = sum(e['data']['lat'] for e in display_aircraft) / len(display_aircraft)
        avg_lon = sum(e['data']['lon'] for e in display_aircraft) / len(display_aircraft)
        
        # Calculate max distance from center to determine scale
        max_d_lat = max(abs(e['data']['lat'] - avg_lat) for e in display_aircraft)
        max_d_lon = max(abs(e['data']['lon'] - avg_lon) for e in display_aircraft)
        
        # Minimum scale (approx 0.5 mile window if only one plane)
        scale_lat = max(max_d_lat, 0.005) * 1.2
        scale_lon = max(max_d_lon, 0.005) * 1.2
        
        center_y, center_x = height // 2, width // 2
        
        # Miles per degree (approximate)
        miles_per_degree = 69.0
        cos_lat = math.cos(math.radians(avg_lat))
        
        # Scale factors for display
        unified_scale = max(scale_lat, scale_lon / cos_lat if cos_lat > 0 else scale_lon)
        y_factor = (height / 2) / unified_scale
        x_factor = ((width / 2) / (unified_scale / cos_lat if cos_lat > 0 else unified_scale)) * 2.0
        
        # Draw distance rings (adaptive to zoom level)
        # Determine appropriate ring interval (1, 5, 10, 25, 50, or 100 miles)
        visible_miles = unified_scale * miles_per_degree
        if visible_miles < 2: ring_interval = 0.5
        elif visible_miles < 5: ring_interval = 1
        elif visible_miles < 20: ring_interval = 5
        elif visible_miles < 50: ring_interval = 10
        else: ring_interval = 25
        
        color_ring = curses.A_DIM
        for i in range(1, 20):
            miles = i * ring_interval
            deg_dist = miles / miles_per_degree
            if deg_dist > unified_scale * 2: break # Don't draw way outside
            
            # Draw ring dots
            num_dots = int(40 * (miles / (visible_miles + 0.1)))
            num_dots = max(20, min(num_dots, 100))
            for j in range(num_dots):
                angle = 2 * math.pi * j / num_dots
                ry = int(center_y - (deg_dist * math.cos(angle)) * y_factor)
                rx = int(center_x + (deg_dist * math.sin(angle)) * x_factor)
                
                if 0 <= ry < height and 0 <= rx < width:
                    try:
                        if j == 0 and ry > 1: # Top of ring, show distance
                            dist_str = f"{miles}mi" if miles % 1 == 0 else f"{miles:.1f}mi"
                            stdscr.addstr(ry, rx, dist_str, color_ring)
                        else:
                            stdscr.addch(ry, rx, '.', color_ring)
                    except: pass

        # Draw center point
        try:
            stdscr.addch(center_y, center_x, '+', curses.color_pair(3))
        except: pass

        # Draw planes
        for entry in display_aircraft:
            a = entry['data']
            age = current_time - entry['last_seen']
            
            y = int(center_y - (a['lat'] - avg_lat) * y_factor)
            x = int(center_x + (a['lon'] - avg_lon) * x_factor)
            
            # Clip to screen
            if 0 <= y < height and 0 <= x < width:
                # Direction arrow
                char = 'A'
                if 'track' in a:
                    t = a['track']
                    arrows = ['↑', '↗', '→', '↘', '↓', '↙', '←', '↖']
                    char = arrows[int((t + 22.5) % 360 / 45)]
                
                # Dim color if stale
                if age < 5:
                    color_plane = curses.color_pair(1) | curses.A_BOLD
                    color_label = curses.color_pair(2)
                else:
                    color_plane = curses.color_pair(5)
                    color_label = curses.color_pair(5) | curses.A_DIM
                
                try:
                    stdscr.addch(y, x, char, color_plane)
                    
                    # Enhanced label: Callsign + Alt + Speed
                    callsign = a.get('flight', a.get('hex', '????')).strip()
                    alt = f"{int(a['alt_baro'])}ft" if 'alt_baro' in a else ""
                    speed = f"{int(a['gs'])}kt" if 'gs' in a else ""
                    
                    full_label = f"{callsign}"
                    if alt or speed:
                        full_label += f" ({alt} {speed})".replace("  ", " ")
                    
                    if x + 2 + len(full_label) < width:
                        stdscr.addstr(y, x + 2, full_label, color_label)
                    elif x - len(full_label) - 1 > 0: # Try left side
                        stdscr.addstr(y, x - len(full_label) - 1, full_label, color_label)
                except: pass

        # Stats bar
        color_stats = curses.color_pair(4) | curses.A_REVERSE if curses.has_colors() else curses.A_REVERSE
        stats_str = f" Planes: {len(display_aircraft)} | Zoom: {visible_miles:.1f}mi | Persistence: {PERSISTENCE_TIMEOUT}s "
        try:
            stdscr.addstr(0, 0, stats_str[:width-1], color_stats)
            stdscr.addstr(height-1, 0, " [q] Quit | Autoscale: ON | Refresh: {}ms ".format(args.interval), curses.A_DIM)
        except: pass
        
        stdscr.refresh()
        
        # Input handling
        key = stdscr.getch()
        if key == ord('q'):
            break

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='ADS-B Radar Display for Small Terminals')
    parser.add_argument('--file', type=str, default=AIRCRAFT_JSON, help=f'Path to aircraft.json (default: {AIRCRAFT_JSON})')
    parser.add_argument('--interval', type=int, default=1000, help='Refresh interval in ms (default: 1000)')
    args = parser.parse_args()

    try:
        curses.wrapper(main, args)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Error: {e}")
