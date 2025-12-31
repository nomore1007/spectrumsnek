# SpectrumSnek 🐍📻

A comprehensive Python-powered radio spectrum analysis toolkit with client-server architecture for flexible deployment on Raspberry Pi and other Linux systems. Features modular plugin system, web interfaces, and multiple access methods.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

## Overview

SpectrumSnek is a modern, modular radio spectrum analysis toolkit with client-server architecture. It provides a complete software-defined radio (SDR) experience with multiple specialized tools for radio monitoring, analysis, and scanning. Built around the affordable RTL-SDR USB dongle, SpectrumSnek offers both traditional radio scanner functionality and modern spectrum analysis capabilities.

### Key Features

- **🔌 Modular Plugin System**: Extensible architecture for radio tools
- **🏗️ Client-Server Architecture**: Flexible deployment options
- **🌐 Web Interfaces**: Browser-based control for all tools
- **📱 Multiple Access Methods**: Console, SSH, and web interfaces
- **🐍 Python-Powered**: Modern async architecture with real-time updates
- **📻 RTL-SDR Integration**: Professional-grade spectrum analysis
- **🔧 System Tools**: WiFi, Bluetooth, and audio management
- **🎛️ Raspberry Pi Optimized**: Handheld and headless configurations

Whether you're a ham radio enthusiast, aviation spotter, or just curious about the invisible waves around you, SpectrumSnek has the tools to help you explore the electromagnetic jungle.

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Tools Overview](#tools-overview)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## Architecture

SpectrumSnek uses a modern client-server architecture for maximum flexibility:

### Service Layer
- **Background Service**: `spectrum-service` runs all radio tools
- **REST API**: HTTP endpoints for tool control and monitoring
- **WebSocket Updates**: Real-time status and data streaming
- **Plugin System**: Modular tool loading from `plugins/` directory

### Client Layer
- **Console Client**: Interactive curses menu (default mode)
- **Web Client**: Browser-based interface (future)
- **SSH Client**: Command-line remote access (future)

### Deployment Options
- **Console Mode**: Interactive menu on HDMI/console
- **Headless Mode**: Service + web interfaces only
- **Full Mode**: Complete console + headless setup

## Features

### Core Radio Tools 🛠️
- **🐍 RTL-SDR Spectrum Analyzer**: Real-time spectrum visualization with demodulation
- **✈️ ADS-B Aircraft Tracker**: Real-time aircraft surveillance and tracking
- **📻 Traditional Radio Scanner**: Frequency bank scanning with squelch support
- **🎵 FM Radio Tools**: Recording and playback capabilities

### System Management 🔧
- **📶 WiFi Network Selector**: Wireless network management
- **🔵 Bluetooth Device Connector**: Bluetooth pairing and connection
- **🔊 Audio Output Selector**: Multi-device audio routing
- **⬆️ GitHub Update Tool**: In-app software updates

### Technical Capabilities
- **Real-time Spectrum Analysis**: Live frequency visualization
- **Signal Processing**: AM/FM/SSB/CW demodulation
- **Frequency Management**: XML-based frequency banks
- **Web Interfaces**: Browser control for all tools
- **CTCSS/DCS Squelch**: Professional audio filtering
- **DMR Support**: Digital mobile radio compatibility

### System Architecture
- **Client-Server Design**: Flexible deployment options
- **Modular Plugin System**: Easy tool extension
- **RESTful API**: Programmatic access to all features
- **WebSocket Streaming**: Real-time data updates
- **Cross-Platform**: Linux optimized, Raspberry Pi ready
- **Automated Setup**: One-command installation for different architectures

## Prerequisites

### Hardware Requirements
- **RTL-SDR USB Dongle**: RTL2832U-based (recommended: RTL-SDR v3/v4)
- **Computer with USB**: Raspberry Pi 3B+ or better recommended
- **Antenna**: Appropriate for target frequencies (VHF/UHF for most use cases)
- **Optional**: Bluetooth/WiFi adapters for system tools

### Software Requirements
- **Operating System**: Raspberry Pi OS Lite (or any Debian-based Linux)
- **Python**: 3.9+ (3.11+ recommended for Raspberry Pi)
- **System Packages**: Will be installed automatically by setup script

### Network Requirements (for headless/headless modes)
- **Local Network Access**: For web interface and API
- **Optional**: Port forwarding for remote access
- **SSH Access**: For remote administration

## Installation

### Quick Setup

Choose your deployment architecture:

```bash
# 🖥️ Console Mode - Interactive menu on HDMI/console
sudo ./setup.sh --console

# 🌐 Headless Mode - Web/API access only
sudo ./setup.sh --headless

# 🔧 Full Mode - Console + headless features
sudo ./setup.sh --full

# 🤖 Automated - Uses console mode by default
sudo ./setup.sh

# 📚 Show all options
./setup.sh --help
```

### Architecture Options

#### Console Mode (`--console`)
- Interactive curses menu on HDMI/console
- Autologin on tty1 with tmux session persistence
- SSH attaches to shared tmux session
- Perfect for handheld devices with screens

#### Headless Mode (`--headless`)
- Background spectrum service with REST API
- Web interfaces for all tools on port 5000
- No console UI, remote access only
- Ideal for servers or API integration

#### Full Mode (`--full`)
- Both console and headless features
- Maximum flexibility for development/testing
- All access methods available simultaneously

### What the Setup Script Does
- ✅ **System Dependencies**: Installs RTL-SDR, Bluetooth, Audio, tmux packages
- ✅ **Python Environment**: Creates virtual environment with all dependencies
- ✅ **Device Permissions**: Configures udev rules for hardware access
- ✅ **Architecture Setup**: Configures services based on selected architecture
- ✅ **Boot Configuration**: Enables automatic startup for chosen mode
- ✅ **Service Management**: Proper systemd integration with dependencies
- ✅ Creates uninstaller script

### Service Management
```bash
# Check service status
sudo systemctl status spectrum-service   # Core service (headless/full)
sudo systemctl status spectrum-console   # Console client (console/full)

# View service logs
sudo journalctl -u spectrum-service -f
sudo journalctl -u spectrum-console -f

# Restart services
sudo systemctl restart spectrum-service
sudo systemctl restart spectrum-console

# Disable services
sudo systemctl disable spectrum-service spectrum-console
```

### Architecture Details

#### Console Mode (`--console`)
**Services Created:**
- `spectrum-console`: Autologin on tty1 with tmux session
- Interactive menu appears automatically on HDMI boot
- SSH logins attach to shared tmux session

**Access Methods:**
- HDMI/Console: Automatic interactive menu
- SSH: `ssh user@pi` (attaches to tmux session)
- Local keyboard: Full control of running tools

**Use Cases:**
- Handheld radio devices
- Touchscreen applications
- Local interactive usage

#### Headless Mode (`--headless`)
**Services Created:**
- `spectrum-service`: Background tool management service

**Access Methods:**
- Web Interface: `http://pi:5000` (local network)
- REST API: `http://pi:5000/api/` (programmatic access)
- SSH: Manual tool execution

**Use Cases:**
- Remote monitoring stations
- API integration projects
- Server deployments

#### Full Mode (`--full`)
**Services Created:**
- `spectrum-service`: Background tool management
- `spectrum-console`: Interactive console client

**Access Methods:**
- All console mode methods
- All headless mode methods
- Maximum flexibility

**Use Cases:**
- Development environments
- Multi-user systems
- Complete feature testing

### Uninstallation
```bash
# Remove everything
./uninstall.sh

# This will:
# - Remove virtual environment
# - Disable all services
# - Remove udev rules
# - Remove desktop shortcuts
# - Clean up configuration files
```

## Quick Start

### After Installation

**Console Mode:**
```bash
# Reboot - menu appears automatically on HDMI
# SSH: ssh user@pi
# Then run: ~/spectrum_ssh.sh (recommended)
# Or: ./run_spectrum.sh (direct)
```

**Headless Mode:**
```bash
# Access web interface
# Local: http://localhost:5000
# Remote: http://pi-ip:5000

# SSH access (manual):
ssh user@pi
~/spectrum_ssh.sh
```

**Full Mode:**
```bash
# All access methods available
# HDMI + SSH + Web interfaces

# SSH with tmux autologin (if enabled):
ssh user@pi  # Automatically starts tmux with SpectrumSnek

# SSH manual access:
ssh user@pi
~/spectrum_ssh.sh  # Full diagnostic interface
./run_spectrum.sh  # Direct launcher
```

### SSH Access Methods

SpectrumSnek provides multiple ways to access from SSH:

#### Recommended: Diagnostic Interface
```bash
ssh user@pi
~/spectrum_ssh.sh
```
- ✅ Handles virtual environment automatically
- ✅ Comprehensive error logging
- ✅ System diagnostics and troubleshooting
- ✅ Safe error recovery

#### Direct Launcher
```bash
ssh user@pi
./run_spectrum.sh
```
- ✅ Activates virtual environment
- ✅ Runs main interface directly
- ⚠️ May exit on errors

#### Manual Environment (Not Recommended)
```bash
ssh user@pi
source venv/bin/activate
python main.py  # ❌ Missing dependencies error
```

#### Service Mode
```bash
# Start service in background
ssh user@pi
./run_spectrum.sh --service &

# Access web interface at http://pi-ip:5000
# Or use SSH client: ./ssh_client.py --host pi-ip
```

### Manual Tool Execution

For advanced users running tools directly:

```bash
# Activate environment first
./run_spectrum.sh  # This activates venv and runs main.py

# Or manually:
source venv/bin/activate

# Then run tools:
python -m rtl_scanner.scanner --freq 100
python -m adsb_tool.adsb_tracker --freq 1090
```

### Testing Setup

```bash
# Test hardware access
./test_setup.sh

# Check service status
sudo systemctl status spectrum-service

# View service logs
sudo journalctl -u spectrum-service -f
```

### API Access (Headless/Full modes)

```bash
# Get tool list
curl http://localhost:5000/api/tools

# Start RTL-SDR scanner
curl -X POST http://localhost:5000/api/tools/rtl_scanner/start

# Check service status
curl http://localhost:5000/api/status
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

**Missing Dependencies Error**
```bash
# Symptom: "Missing dependencies: numpy, scipy"
python main.py
# ❌ Don't run python directly!

# Solution: Use the provided launchers
./run_spectrum.sh          # ✅ Direct launcher
~/spectrum_ssh.sh          # ✅ Full diagnostic interface

# Manual activation (if needed):
source venv/bin/activate
python main.py
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

### Radio Tools (Plugins)

#### 1. 🐍 RTL-SDR Spectrum Analyzer
Advanced real-time spectrum analysis with professional features.

**Capabilities:**
- Live spectrum visualization with ASCII graphics
- Interactive frequency/gain/ demodulation controls
- AM/FM/SSB/CW/DMR signal demodulation
- Signal recording and audio output
- Web interface for remote control

**Access:** Available in all architectures via menu/API

#### 2. ✈️ ADS-B Aircraft Tracker
Real-time aviation surveillance and aircraft tracking.

**Capabilities:**
- 1090 MHz ADS-B signal decoding
- Aircraft position, altitude, heading data
- Flight information and identification
- Terminal and web display formats
- Position tracking and mapping

**Access:** Available in all architectures via menu/API

#### 3. 📻 Traditional Radio Scanner
Classic frequency scanning with modern squelch features.

**Capabilities:**
- XML-based frequency bank management
- CTCSS/DCS tone squelch detection
- Sequential scanning through frequency lists
- DMR digital radio support
- Command-line frequency bank editor

**Access:** Available in all architectures via menu/API

### System Tools (Built-in)

#### 4. 📶 WiFi Network Selector
Wireless network management for connectivity.

**Capabilities:**
- Scan available WiFi networks
- Connect to WPA2/3 secured networks
- Signal strength monitoring
- Network status display

**Access:** System Tools submenu in console architectures

#### 5. 🔵 Bluetooth Device Connector
Bluetooth device pairing and audio management.

**Capabilities:**
- Discover nearby Bluetooth devices
- Pair and connect to devices
- Audio device management
- Connection status monitoring

**Access:** System Tools submenu in console architectures

#### 6. 🔊 Audio Output Selector
Multi-device audio routing and testing.

**Capabilities:**
- Enumerate available audio devices
- Test audio output on different devices
- Bluetooth audio device support
- Default device configuration

**Access:** System Tools submenu in console architectures

#### 7. ⬆️ GitHub Update Tool
In-application software updates.

**Capabilities:**
- Check for latest SpectrumSnek updates
- Automatic git pull execution
- Update status reporting
- Safe update process

**Access:** System Tools submenu in console architectures

### Service Architecture

#### Spectrum Service (`spectrum-service`)
Background daemon providing core functionality.

**Endpoints:**
- `GET /api/tools` - List available tools
- `POST /api/tools/<name>/start` - Launch tool
- `POST /api/tools/<name>/stop` - Stop tool
- `GET /api/status` - Service health
- WebSocket events for real-time updates

**Deployment:** Runs in headless and full architectures

#### Console Client (`spectrum-console`)
Interactive menu client connecting to service.

**Features:**
- Curses-based menu interface
- Tool selection and control
- Real-time status updates
- SSH session integration

**Deployment:** Runs in console and full architectures

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

### 4. 🔧 System Tools (`system_tools/`)
Essential utilities for device management and connectivity.

**Features:**
- **WiFi Network Selector**: Scan and connect to wireless networks
- **Bluetooth Device Connector**: Pair and connect to Bluetooth devices
- **Audio Output Selector**: Choose and test audio devices including Bluetooth
- **GitHub Update Tool**: Pull latest updates directly from the menu

**Usage:**
```bash
# Access through main menu
./run.sh  # Select "System Tools"

# Or run directly
python -m system_tools.system_menu
```

### 5. 🏠 Main Loader (`main.py`)
The heart of SpectrumSnek - your command center for all radio adventures!

**Features:**
- Interactive curses-based menu - navigate like a snake charmer
- Tool selection and launching - pick your poison
- Global web interface toggle - web or terminal, your choice
- Status monitoring - keep an eye on your snake
- Raspberry Pi console autostart support

**Usage:**
```bash
# Easy launcher (recommended)
./run.sh

# Manual activation
source venv/bin/activate
python main.py

# Console autostart (for handheld devices)
sudo ./setup.sh --console
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
SpectrumSnek/
├── main.py              # Main loader with menu system
├── run.sh               # Easy launcher script (activates venv)
├── rtl_scanner.py       # Direct RTL-SDR scanner launcher
├── rtl_scanner/         # RTL-SDR scanner module
│   ├── __init__.py      # Module info and entry point
│   ├── scanner.py       # Core scanner implementation
│   └── web_scanner.py   # Web control interface
├── adsb_tool/           # ADS-B aircraft tracker module
│   ├── __init__.py      # Module info and entry point
│   └── adsb_tracker.py  # ADS-B tracking implementation
├── radio_scanner/       # Traditional radio scanner module
│   ├── __init__.py      # Module info and entry point
│   ├── scanner.py       # Core scanner implementation
│   ├── freq_editor.py   # Frequency bank editor
│   └── banks/           # XML frequency banks
├── system_tools/        # System utilities module
│   ├── __init__.py      # Module info and entry point
│   ├── system_menu.py   # System tools submenu
│   ├── wifi_selector.py # WiFi network selector
│   ├── bluetooth_connector.py # Bluetooth device connector
│   └── audio_output_selector.py # Audio device selector
├── wifi_tool/           # WiFi selector module
├── bluetooth_tool/      # Bluetooth connector module
├── demo_scanner.py      # Demo spectrum analyzer
├── run_scanner.sh       # Legacy launcher script
├── setup.sh             # Installation and setup script
├── uninstall.sh         # Uninstallation script
└── requirements.txt     # Dependencies
```

### Available Modules

- **RTL-SDR Scanner**: Full-featured radio spectrum scanner with demodulation
- **ADS-B Aircraft Tracker**: Real-time aircraft surveillance and tracking
- **Traditional Radio Scanner**: Frequency bank scanning with squelch
- **System Tools**: WiFi, Bluetooth, audio, and update utilities
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
# Easy launcher
./run.sh
# Shows menu to select RTL-SDR Scanner, ADS-B Tracker, Radio Scanner, System Tools, etc.

# Manual
source venv/bin/activate
python main.py
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

## Raspberry Pi Setup

SpectrumSnek supports different Raspberry Pi configurations:

### Handheld Device (Console Mode)
For touchscreen or HDMI-connected devices:

```bash
# Install console mode
sudo ./setup.sh --console

# Features:
# - Automatic menu on HDMI boot
# - Touchscreen or keyboard control
# - SSH access to shared session
# - Perfect for portable radios
```

### Headless Server (Headless Mode)
For remote access without display:

```bash
# Install headless mode
sudo ./setup.sh --headless

# Features:
# - Web interface access
# - REST API for automation
# - SSH tool control
# - Background operation
```

### Development/Multi-User (Full Mode)
For complete access options:

```bash
# Install full mode
sudo ./setup.sh --full

# Features:
# - All console and headless features
# - Maximum flexibility
# - Multiple access methods
```

### Easy Launcher
```bash
# Automatically activates virtual environment
./run.sh

# Works in all architectures
```

### System Tools
Available in all modes:
- WiFi network management
- Bluetooth device pairing
- Audio output selection
- GitHub updates

### Power Management
For battery-powered setups:
- Use appropriate gain settings
- Configure service idle timeouts
- Disable unused peripherals
- Monitor power consumption

## Legal Notice

Please ensure you comply with local laws and regulations regarding radio monitoring and recording. Some frequencies may be restricted or require licenses for monitoring.

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

## License

This project is open source and available under the MIT License.