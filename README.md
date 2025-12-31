# RTL-SDR Radio Scanner

# SpectrumSnek 🐍📻

A Python-powered radio spectrum analysis toolkit using RTL-SDR for software-defined radio operations. Because who doesn't love snakes and signals?

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

## Overview

SpectrumSnek is your friendly neighborhood python 🐍 that slithers through the radio spectrum! This toolkit provides a complete software-defined radio (SDR) experience with multiple specialized tools for radio monitoring, analysis, and scanning. Built around the affordable RTL-SDR USB dongle, SpectrumSnek offers both traditional radio scanner functionality and modern spectrum analysis capabilities.

Whether you're a ham radio enthusiast, aviation spotter, or just curious about the invisible waves around you, SpectrumSnek has the tools to help you explore the electromagnetic jungle.

## Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Tools Overview](#tools-overview)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## Features

### Core Tools 🛠️
- **🐍 RTL-SDR Spectrum Analyzer**: Real-time spectrum visualization and analysis - watch those signals dance!
- **✈️ ADS-B Aircraft Tracker**: Real-time aircraft surveillance and tracking - spot planes before you see them
- **📻 Traditional Radio Scanner**: Scan user-defined frequency lists with squelch support - classic radio monitoring
- **📝 Frequency Bank Editor**: Command-line tool for managing XML frequency databases - organize your radio favorites

### Technical Capabilities
- **Real-time Spectrum Analysis**: Terminal-based frequency spectrum visualization
- **Interactive Spectrum Browser**: Keyboard-controlled live spectrum analysis with controls
- **Frequency Scanning**: Automatically scan frequency ranges for signals
- **FM Radio Recording**: Record FM radio stations to WAV files
- **Signal Detection**: Automatically detect and save strong signals
- **CTCSS/DCS Squelch**: Tone-based squelch detection for FM channels
- **DMR Support**: Digital Mobile Radio frequency handling
- **Web Interfaces**: Optional web-based control interfaces for all tools

### System Features
- **Modular Architecture**: Extensible plugin system for easy tool addition
- **Terminal-Only Operation**: No GUI or desktop environment required
- **Boot-time Startup**: Optional systemd service for automatic startup
- **Virtual Environment**: Isolated Python environment for clean dependencies
- **Flexible Configuration**: Adjustable sample rates, gains, and frequencies
- **Cross-Platform**: Linux-focused with proper OS detection

## Prerequisites

### Hardware Requirements
- RTL-SDR USB dongle (RTL2832U-based)
- Computer with USB port
- Antenna suitable for target frequencies

### Software Requirements
- Python 3.6+
- RTL-SDR drivers installed on your system

## Installation

### Quick Setup
```bash
# Full installation with boot startup
./setup.sh --boot

# Basic installation without system dependencies
./setup.sh --no-system-deps

# Show help
./setup.sh --help
```

### What the Setup Script Does
- ✅ Creates Python virtual environment
- ✅ Installs system dependencies (RTL-SDR drivers, etc.)
- ✅ Installs Python dependencies (Flask, numpy, scipy, etc.)
- ✅ Sets up RTL-SDR device permissions
- ✅ Creates desktop shortcuts
- ✅ Optionally configures boot-time startup
- ✅ Creates uninstaller script

### Boot-Time Startup
```bash
# Enable automatic startup on boot
./setup.sh --boot

# Check service status
sudo systemctl status radio-tools-loader

# Disable boot startup
sudo systemctl disable radio-tools-loader
```

### Uninstallation
```bash
# Remove everything
./uninstall.sh

# This will:
# - Remove virtual environment
# - Disable boot service
# - Remove udev rules
# - Remove desktop shortcuts
```

## Quick Start

1. **After installation, launch the main menu:**
   ```bash
   python main.py
   ```

2. **Or run tools directly:**
   ```bash
   # RTL-SDR Scanner
   ./run_scanner.sh --interactive --freq 100

    # ADS-B Tracker
    python -m adsb_tool.adsb_tracker --freq 1090

    # Traditional Radio Scanner
    python -m radio_scanner.scanner

    # Frequency Bank Editor
    python radio_scanner/freq_editor.py list
    python radio_scanner/freq_editor.py show police.xml

    # With web interfaces
    ./run_scanner.sh --interactive --web --freq 100
    python -m adsb_tool.adsb_tracker --web --freq 1090
    ```

2. **Test the setup:**
   ```bash
   ./test_setup.sh
   ```

3. **Run the radio scanner:**
   ```bash
   ./run_scanner.sh --freq 100 --mode spectrum
   ```

4. **Try interactive mode:**
   ```bash
   ./run_scanner.sh --interactive --freq 100
   ```

5. **Try web interface:**
   ```bash
   ./run_scanner.sh --interactive --web --freq 100
   # Opens both terminal AND web interfaces simultaneously
   # Terminal: Interactive controls
   # Web: http://localhost:5000 in your browser
   ```

### Demo Mode (No Hardware Required)
If you don't have RTL-SDR hardware, try the demo mode:
```bash
./run_scanner.sh --demo --freq 100 --mode spectrum
./run_scanner.sh --demo --mode scan
```
   This will create the virtual environment, install dependencies, and attempt to set up device permissions.

2. **If setup.sh couldn't set permissions (sudo required):**
   ```bash
   sudo ./install_udev_rules.sh
   sudo usermod -a -G plugdev $USER
   # Then log out and back in (or reboot)
   ```

3. **Test the setup:**
   ```bash
   ./test_setup.sh
   ```

4. **Run the radio scanner:**
   ```bash
   ./run_scanner.sh --freq 100 --mode spectrum
   ```

5. **Try interactive mode:**
   ```bash
   ./run_scanner.sh --interactive --freq 100
   ```

### Demo Mode (No Hardware Required)
If you don't have RTL-SDR hardware, try the demo mode:
```bash
./run_scanner.sh --demo --freq 100 --mode spectrum
./run_scanner.sh --demo --mode scan
```

## Configuration

### Frequency Banks
Customize frequency banks by editing XML files in `radio_scanner/banks/` or using the frequency editor tool. Sample banks are included for:
- Police and emergency services
- Fire department communications
- Aviation and air traffic control

### RTL-SDR Settings
Adjust device parameters in the tool configuration:
- Sample rate (default: 2.4 MHz)
- Gain settings (auto or manual)
- Frequency ranges
- Demodulation modes

### Web Interface
All tools support optional web interfaces on different ports:
- RTL-SDR Spectrum Analyzer: Port 5000
- ADS-B Tracker: Port 5001
- Global toggle available in main menu

## Troubleshooting

### Common Issues

**RTL-SDR Device Not Found**
```bash
# Check device connection
lsusb | grep RTL

# Check permissions
ls -la /dev/bus/usb/

# Install udev rules
sudo ./install_udev_rules.sh
sudo usermod -a -G plugdev $USER
# Logout and login again
```

**Permission Denied Errors**
```bash
# Add user to plugdev group
sudo usermod -a -G plugdev $USER

# Or run with sudo (not recommended)
sudo python rtl_scanner.py --freq 100
```

**Import Errors**
```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

**Web Interface Not Working**
```bash
# Check if ports are available
netstat -tlnp | grep 5000

# Try different port
python rtl_scanner.py --web --web-port 5001
```

### Demo Mode
Test functionality without hardware:
```bash
./run_scanner.sh --demo --freq 100 --mode spectrum
```

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup
```bash
# Fork and clone the repository
git clone https://github.com/yourusername/radiotools.git
cd radiotools

# Set up development environment
./setup.sh --dev

# Run tests
python -m pytest

# Check code style
python -m flake8
```

### Adding New Tools
1. Create a new module directory under the main project
2. Implement `__init__.py` with `get_module_info()` and `run()` functions
3. Add the module to `main.py` module loader
4. Update documentation

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE.txt) file for details.

## Disclaimer

This software is for educational and research purposes only. Users are responsible for complying with local laws and regulations regarding radio frequency monitoring and recording.

## Tools Overview

### 1. 🐍 RTL-SDR Spectrum Analyzer (`rtl_scanner/`)
The head of SpectrumSnek - advanced spectrum analysis with real-time visualization!

**Features:**
- Real-time spectrum display with ASCII visualization (because terminals are cool)
- Interactive frequency and gain controls - tune like a pro
- AM/FM/SSB/CW demodulation - decode all the things
- Signal recording capabilities - save those interesting transmissions
- Optional web interface for remote control - operate from anywhere

**Usage:**
```bash
# Terminal spectrum analyzer - watch the spectrum come alive
python rtl_scanner.py --freq 100 --mode spectrum

# Interactive mode with keyboard controls - hands-on spectrum surfing
python rtl_scanner.py --interactive --freq 100

# Web interface mode - control from your browser
python rtl_scanner.py --web --freq 100
```

### 2. ✈️ ADS-B Aircraft Tracker (`adsb_tool/`)
Spot aircraft before they spot you! Real-time aviation surveillance.

**Features:**
- 1090 MHz ADS-B signal decoding - listen to the skies
- Aircraft position, altitude, and flight data - know where everything is
- Multiple display formats (terminal and web) - view it your way
- Position tracking and mapping - plot flight paths
- Flight information display - who's flying where?

**Usage:**
```bash
# Terminal mode - classic command-line aircraft spotting
python -m adsb_tool.adsb_tracker --freq 1090

# Web interface mode - beautiful maps and tracking
python -m adsb_tool.adsb_tracker --web --freq 1090
```

### 3. 📻 Traditional Radio Scanner (`radio_scanner/`)
Old-school radio monitoring meets modern tech - scan like the pros!

**Features:**
- XML-based frequency banks - organize your favorite frequencies
- CTCSS/DCS squelch detection - cut through the noise
- DMR frequency support - digital radio monitoring
- Sequential scanning through frequency lists - systematic monitoring
- Command-line frequency bank editor - manage your databases

#### Frequency Bank Management
```bash
# List available frequency banks
python radio_scanner/freq_editor.py list

# Show contents of a bank
python radio_scanner/freq_editor.py show police.xml

# Create a new frequency bank
python radio_scanner/freq_editor.py create ambulance "Ambulance Services"

# Add frequencies to a bank
python radio_scanner/freq_editor.py add police.xml 155.475 FM "Police Main" --ctcss 123.0
python radio_scanner/freq_editor.py add aviation.xml 118.300 AM "Tower"
```

#### Scanning Frequencies
```bash
# Run the traditional scanner
python -m radio_scanner.scanner

# Select from available banks and begin scanning
# Supports CTCSS/DCS squelch detection
# Automatically moves between frequencies
```

#### Frequency Bank Format
Banks are stored as XML files in `radio_scanner/banks/`:
```xml
<frequency_bank name="Police" description="Local police frequencies">
  <frequency value="155.475" mode="FM" name="Police Main">
    <squelch type="CTCSS" tone="123.0"/>
  </frequency>
  <frequency value="155.685" mode="FM" name="Police Tac 1">
    <squelch type="DCS" code="023"/>
  </frequency>
</frequency_bank>
```

### 4. 🏠 Main Loader (`main.py`)
The heart of SpectrumSnek - your command center for all radio adventures!

**Features:**
- Interactive curses-based menu - navigate like a snake charmer
- Tool selection and launching - pick your poison
- Global web interface toggle - web or terminal, your choice
- Status monitoring - keep an eye on your snake

**Usage:**
```bash
# Launch the main menu - where the magic begins
python main.py
```
   This will create the virtual environment, install dependencies, and check for RTL-SDR drivers.

2. **Run the radio scanner:**
   ```bash
   ./run_scanner.sh --freq 100 --mode spectrum
   ```

## Manual Installation

If you prefer manual setup:

1. **Clone or download this repository**

2. **Create and activate virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install RTL-SDR drivers (Linux):**
   ```bash
   sudo apt-get update
   sudo apt-get install rtl-sdr librtlsdr-dev
   ```

   **For other operating systems:**
   - Windows: Install Zadig and replace RTL-SDR drivers
   - macOS: Install rtl-sdr via Homebrew

## Usage

### Basic Spectrum Analysis
```bash
python radio_scanner.py --freq 100 --mode spectrum
```
This will display a real-time spectrum plot centered at 100 MHz.

### Frequency Scanning
```bash
python radio_scanner.py --start-freq 88 --end-freq 108 --mode scan
```
Scan FM radio band (88-108 MHz) for signals.

### Record FM Radio
```bash
python radio_scanner.py --freq 95.5 --mode record --duration 30 --output my_recording
```
Record 30 seconds of FM radio at 95.5 MHz.

### Command Line Options

- `--demo`: Run in demo mode (no hardware required)
- `--freq`: Center frequency in MHz (default: 100)
- `--sample-rate`: Sample rate in MHz (default: 2.4)
- `--gain`: Gain setting ('auto' or dB value, default: 'auto')
- `--mode`: Operation mode ('spectrum', 'scan', 'record')
- `--start-freq`: Start frequency for scanning (MHz)
- `--end-freq`: End frequency for scanning (MHz)
- `--duration`: Recording duration in seconds (default: 10)
- `--output`: Output filename for recordings

## Examples

### Monitor Air Traffic Control (ATC)
```bash
python radio_scanner.py --freq 118 --sample-rate 2.0 --mode spectrum
# Displays real-time spectrum in terminal with ASCII visualization
# Runs continuously until Ctrl+C is pressed
```

### Scan Police Radio Frequencies
```bash
python radio_scanner.py --start-freq 150 --end-freq 170 --mode scan
# Scans frequency range and reports signal strength
```

### Record Weather Radio
```bash
python radio_scanner.py --freq 162.55 --mode record --duration 60
# Records audio to WAV file
```

### Interactive Mode Controls

The interface is designed for **limited input devices** with arrow keys, select button, and menu button.

**Main Interface (Frequency Control):**
- `↑/↓` : Increase/decrease the selected frequency digit
- `←/→` : Move cursor to select different digits (100MHz → 10MHz → 1MHz → 100kHz → 10kHz → 1kHz → 100Hz → 10Hz → 1Hz)
- **Blinking cursor** shows which digit is currently selected on the frequency display
- `'m'` : Open settings menu
- `'q'` : Quit

**Settings Menu (Compact Design):**
- `↑/↓` : Navigate between options
- `←/→` : Cycle through values for selected option
- `SPACE/ENTER` : Close menu
- `ESC` : Close menu

**Menu Options (Compact):**
- **Gain: Auto** - Cycles: Auto → Low → Medium → High
- **Width: NORMAL** - ← toggles Narrow↔Normal, → toggles Wide↔Full
- **Demod: NONE** - Cycles: None → AM → FM → SSB → CW
- **Audio: OFF** - Toggles: ON ↔ OFF
- **PPM: +0** - Adjust frequency correction (±100 PPM)
- **Exit** - Closes menu

**Note:** All advanced settings are accessed through the menu system for simplified hardware integration.

### Demo Mode Examples (No Hardware Required)
```bash
# Demo spectrum analysis (terminal display, runs continuously)
./run_scanner.sh --demo --freq 100 --mode spectrum

# Demo frequency scan
./run_scanner.sh --demo --mode scan --start-freq 88 --end-freq 108
```

## Modular Architecture

This project uses a modular design with the following structure:

```
radio-scanner/
├── main.py              # Main loader with menu system
├── rtl_scanner.py       # Direct RTL-SDR scanner launcher
├── rtl_scanner/         # RTL-SDR scanner module
│   ├── __init__.py      # Module info and entry point
│   ├── scanner.py       # Core scanner implementation
│   └── web_scanner.py   # Web control interface
├── adsb_tool/           # ADS-B aircraft tracker module
│   ├── __init__.py      # Module info and entry point
│   └── adsb_tracker.py  # ADS-B tracking implementation
├── demo_scanner.py      # Demo spectrum analyzer
├── run_scanner.sh       # Convenience launcher script
└── requirements.txt     # Dependencies
```

### Available Modules

- **RTL-SDR Scanner**: Full-featured radio spectrum scanner with demodulation
- **ADS-B Aircraft Tracker**: Real-time aircraft surveillance and tracking
- **Spectrum Analyzer (Demo)**: Basic spectrum analysis demonstration
- **Web Portal Toggle**: Enable/disable web interfaces globally

### Module System Features

- **Main Loader** (`main.py`): Interactive menu to select and launch tools
- **Direct Access**: Each module can be run independently from command line
- **Web Portal Toggle**: Global on/off control for all web interfaces
- **Extensible**: Easy to add new radio tools as modules

### Usage Examples

**Main Menu (Interactive Selection):**
```bash
python main.py
# Shows menu to select RTL-SDR Scanner or other tools
```

**Direct RTL-SDR Scanner:**
```bash
# Terminal interface only
./run_scanner.sh --interactive --freq 100

# Dual interface mode (terminal + web control)
./run_scanner.sh --interactive --web --freq 100
# Terminal: Full scanner with spectrum display
# Web: Control interface at http://localhost:5000

# Remote control only
./run_scanner.sh --interactive --web --web-host localhost --freq 100
# Web control interface at http://localhost:5000

# Spectrum analysis mode
./run_scanner.sh --freq 440 --mode spectrum --duration 30

# FM radio recording
./run_scanner.sh --freq 95.5 --mode record --duration 60
```

**Direct Module Access:**
```bash
# Run RTL-SDR scanner directly
python rtl_scanner.py --interactive --freq 100

# Run ADS-B tracker directly
python -m adsb_tool.adsb_tracker --freq 1090

# Run from main loader
python main.py rtl_scanner
python main.py adsb_tool
```

**Web Portal Control:**
```bash
# Toggle web portals on/off globally
python main.py  # Select "Web Portal: ON/OFF" from menu

# Run with web interfaces
python rtl_scanner.py --interactive --web --freq 100
python -m adsb_tool.adsb_tracker --web --freq 1090
```

### Web Control Interface Features

The web control interface provides:
- **Remote control** of the running RTL-SDR scanner
- **Frequency adjustment** via input field and arrow buttons
- **Dropdown menus** for gain and mode settings
- **Real-time status updates** from the scanner
- **Responsive design** for mobile/tablet control
- **Control-only interface** - no spectrum display, assumes scanner is running

**Web Interface Controls:**
- **Frequency input**: Direct frequency entry with validation
- **Arrow buttons**: Fine frequency adjustment and digit selection
- **Dropdowns**: Easy selection of gain, mode, and spectrum width
- **Start/Stop buttons**: Control scanner operation
- **Live spectrum**: Real-time waterfall-style display

### Troubleshooting Interactive Mode

**Arrow keys not working?**
- The interface is designed for arrow keys as primary input
- Try the debug script: `python debug_keys.py`
- Some terminals may need special configuration for arrow keys
- The scanner supports both curses key codes and escape sequences

**Other issues:**
- Make sure your terminal supports curses
- Try different terminal emulators (xterm, gnome-terminal, etc.)
- Check that the RTL-SDR device is properly connected

### Demodulation Modes

The interactive scanner supports several demodulation modes:

- **None**: Raw spectrum display only
- **AM**: Amplitude Modulation (envelope detection)
- **FM**: Frequency Modulation (phase differentiation)
- **SSB**: Single Side Band (simplified implementation)
- **CW**: Continuous Wave/Morse code (envelope detection)

Use the `d` key to cycle through modes, and `Space` to toggle audio output when demodulation is active.

## Troubleshooting

### Testing Setup
Run the setup test to diagnose issues:
```bash
./test_setup.sh
```

### Common Issues

1. **Permission denied / Access denied errors**
   - **Solution**: Install udev rules and fix permissions:
     ```bash
     sudo ./install_udev_rules.sh
     sudo usermod -a -G plugdev $USER
     ```
   - Reboot or unplug/re-plug the RTL-SDR device
   - Verify with: `./test_setup.sh`

2. **"No RTL-SDR device found"**
   - Ensure RTL-SDR dongle is properly connected
   - Check USB permissions (Linux: add user to plugdev group)
   - Verify drivers are installed correctly

3. **Poor signal quality**
   - Try different gain settings (`--gain auto` or `--gain 20`)
   - Use a better antenna
   - Reduce sample rate for better sensitivity

4. **High CPU usage**
   - Reduce sample rate (`--sample-rate 1.0`)
   - Increase FFT buffer size in spectrum mode

5. **Import errors / missing dependencies**
   - Run `./setup.sh` to reinstall dependencies
   - Check that virtual environment is activated

### Driver Installation

**Linux:**
```bash
# Ubuntu/Debian
sudo apt-get install rtl-sdr

# Fedora/CentOS
sudo dnf install rtl-sdr
```

**macOS:**
```bash
brew install rtl-sdr
```

**Windows:**
1. Download Zadig from https://zadig.akeo.ie/
2. Run Zadig as administrator
3. Select RTL-SDR device
4. Install WinUSB driver

## Frequency Bands

Common frequency bands you can monitor:

- **AM Radio**: 540-1700 kHz
- **FM Radio**: 88-108 MHz
- **Air Traffic Control**: 118-137 MHz
- **Police/Fire**: Varies by location (typically 150-170 MHz, 450-470 MHz)
- **Weather Radio**: 162.40-162.55 MHz
- **Satellite**: 137-138 MHz (NOAA weather satellites)

## Legal Notice

Please ensure you comply with local laws and regulations regarding radio monitoring and recording. Some frequencies may be restricted or require licenses for monitoring.

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

## License

This project is open source and available under the MIT License.