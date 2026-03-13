#!/usr/bin/env python3
import json
import time
import curses
import math
import os
import sys
import argparse

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
    
    # Color support
    if curses.has_colors():
        curses.start_color()
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)  # Planes
        curses.init_pair(2, curses.COLOR_CYAN, curses.COLOR_BLACK)   # Labels
        curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)    # Center
        curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLACK) # Stats
    
    while True:
        stdscr.clear()
        height, width = stdscr.getmaxyx()
        
        if height < 10 or width < 20:
            stdscr.addstr(0, 0, "Terminal too small!")
            stdscr.refresh()
            if stdscr.getch() == ord('q'): break
            continue

        data = get_aircraft_data(args.file)
        if not data or 'aircraft' not in data:
            stdscr.addstr(0, 0, "Waiting for data...")
            stdscr.addstr(1, 0, f"Checking {args.file}")
            stdscr.refresh()
            if stdscr.getch() == ord('q'): break
            time.sleep(1)
            continue
            
        # Filter aircraft with position
        aircraft = [a for a in data['aircraft'] if 'lat' in a and 'lon' in a]
        
        if not aircraft:
            stdscr.addstr(0, 0, f"No aircraft with positions. (Total: {len(data['aircraft'])})")
            stdscr.addstr(1, 0, f"Messages: {data.get('messages', 'N/A')}")
            stdscr.refresh()
            if stdscr.getch() == ord('q'): break
            continue
            
        # Calculate center of the data
        avg_lat = sum(a['lat'] for a in aircraft) / len(aircraft)
        avg_lon = sum(a['lon'] for a in aircraft) / len(aircraft)
        
        # Calculate max distance from center to determine scale
        max_d_lat = max(abs(a['lat'] - avg_lat) for a in aircraft)
        max_d_lon = max(abs(a['lon'] - avg_lon) for a in aircraft)
        
        # Minimum scale to prevent division by zero or extreme zoom
        scale_lat = max(max_d_lat, 0.005) * 1.2
        scale_lon = max(max_d_lon, 0.005) * 1.2
        
        center_y, center_x = height // 2, width // 2
        
        # Draw center point
        try:
            color_center = curses.color_pair(3) if curses.has_colors() else curses.A_DIM
            stdscr.addch(center_y, center_x, '+', color_center)
        except: pass

        # Draw planes
        for a in aircraft:
            cos_lat = math.cos(math.radians(avg_lat))
            unified_scale = max(scale_lat, scale_lon / cos_lat if cos_lat > 0 else scale_lon)
            
            y_factor = (height / 2) / unified_scale
            x_factor = (width / 2) / (unified_scale / cos_lat if cos_lat > 0 else unified_scale)
            
            # Terminal character adjustment (chars are taller than wide)
            x_factor *= 2.0 
            
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
                
                color_plane = curses.color_pair(1) | curses.A_BOLD if curses.has_colors() else curses.A_BOLD
                color_label = curses.color_pair(2) if curses.has_colors() else curses.A_DIM
                
                try:
                    stdscr.addch(y, x, char, color_plane)
                    
                    label = a.get('flight', a['hex']).strip()
                    alt = f"{a['alt_baro']//100}k" if 'alt_baro' in a else ""
                    full_label = f"{label} {alt}".strip()
                    
                    if x + 2 + len(full_label) < width:
                        stdscr.addstr(y, x + 2, full_label, color_label)
                except: pass

        # Stats bar
        color_stats = curses.color_pair(4) | curses.A_REVERSE if curses.has_colors() else curses.A_REVERSE
        stats_str = f" Planes: {len(aircraft)} | Ctr: {avg_lat:.3f},{avg_lon:.3f} | Zoom: {unified_scale:.3f}deg "
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
