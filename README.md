# SpectrumSnek 🐍📻

A comprehensive Python-powered radio spectrum analysis toolkit with client-server architecture for flexible deployment on Raspberry Pi and other Linux systems. Features modular plugin system, web interfaces, and multiple access methods.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

## Recent Updates

- **ADS-B Tool Fix**: Resolved syntax error causing unterminated triple-quoted string literal in adsb_service.py
- **Setup Script Enhancement**: Prioritized dump1090-mutability installation for optimal RTL-SDR ADS-B compatibility
- **Raspberry Pi Optimized**: Primary deployment platform with 512MB RAM constraints in mind

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

Whether you're a ham radio enthusiast, aviation spotter, or just curious about the invisible waves around you, SpectrumSnek provides a complete software-defined radio experience with professional-grade tools and modern deployment options.

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
- **Web Client**: Browser-based interface with real-time stats
- **SSH Client**: Command-line remote access with diagnostics

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
```

### Repair & Testing Options

```bash
# 🔧 Fix corrupted .bashrc file
./setup.sh --fix-bashrc

# 🧪 Test RTL-SDR setup and permissions
./setup.sh --test-setup

# 🔄 Repair tmux installation
sudo ./setup.sh --repair-tmux
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

**Primary Launcher:**
SpectrumSnek uses `./run_spectrum.sh` as the main program launcher. It automatically activates the virtual environment and runs the interactive menu system.

```bash
# Main launcher (recommended for all modes)
./run_spectrum.sh
```

**Console Mode:**
```bash
# Reboot - menu appears automatically on HDMI
# SSH: ssh user@pi
# Then run: ~/spectrum_ssh.sh (recommended)
# Or: ./run_spectrum.sh (main program)
```

**Headless Mode:**
```bash
# Access web interface (firewall automatically configured)
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
~/spectrum_ssh.sh  # Auto-detects running service, shows web interface
./run_spectrum.sh  # Main program launcher (if service not running)
```

### Service Management

SpectrumSnek can run as a system service for reliability:

```bash
# Check service status
./service_manager.sh status

# Service control
./service_manager.sh start    # Start service
./service_manager.sh stop     # Stop service
./service_manager.sh restart  # Restart service

# Boot configuration
./service_manager.sh enable   # Start on boot
./service_manager.sh disable  # Don't start on boot

# View service logs
./service_manager.sh logs
```

**Note:** When the service is running, SSH access will connect to the existing service rather than starting a new instance.

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
# Start service in background (binds to 0.0.0.0:5000)
ssh user@pi
./run_spectrum.sh --service &

# Or specify custom settings:
./run_spectrum.sh --service --host 127.0.0.1 --port 5001

# Access web interface at http://pi-ip:5000 (firewall auto-configured)
# Or use SSH client: ./ssh_client.py --host pi-ip --port 5000
```

### Service Management

SpectrumSnek includes comprehensive service management:

```bash
# Check service status
./service_manager.sh status

# Control the service
./service_manager.sh start    # Start service
./service_manager.sh stop     # Stop service
./service_manager.sh restart  # Restart service
./service_manager.sh enable   # Start on boot
./service_manager.sh disable  # Don't start on boot

# View service logs
./service_manager.sh logs
```

### Manual Tool Execution

For advanced users running tools directly:

```bash
# Use the launcher (recommended)
./run_spectrum.sh  # Activates venv and runs main.py

# Or manually:
source venv/bin/activate
python main.py --service --host 0.0.0.0 --port 5000

# Direct tool access:
python -m rtl_scanner.scanner --freq 100
python -m adsb_tool.adsb_tracker --freq 1090
```

### Testing Setup

```bash
# Comprehensive test suite
~/spectrum_ssh.sh          # Service connectivity test
./service_manager.sh status # Service status check
./check_port.sh            # Port usage analysis

# Hardware tests
lsusb | grep RTL           # RTL-SDR detection
rtl_test -t               # RTL-SDR functionality test

# API tests
curl http://localhost:5000/api/status
curl http://localhost:5000/api/tools
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

### Quick Diagnostics

**Run the diagnostic script:**
```bash
~/spectrum_ssh.sh  # Comprehensive connectivity test
```

**Check service status:**
```bash
./service_manager.sh status
./service_manager.sh logs
```

**Port and firewall check:**
```bash
./check_port.sh
sudo ufw status        # Check firewall
curl http://localhost:5000/api/status  # Test API
```

### Common Issues

**RTL-SDR Device Not Found**
```bash
# Check device connection
lsusb | grep RTL

# Check permissions
ls -la /dev/bus/usb/

# Setup permissions (run once)
sudo ./setup.sh --full  # Includes udev rules
sudo usermod -a -G plugdev $USER
# Logout and login again
```

**Port Already In Use / Service Not Accessible**
```bash
# Check what's using port 5000
./check_port.sh

# Kill conflicting processes
pkill -f spectrum_service
pkill -f "python main.py"

# Restart service
./service_manager.sh restart

# Test connectivity
curl http://localhost:5000/api/status
```

**Permission Denied Errors**
```bash
# Add user to required groups
sudo usermod -a -G plugdev,bluetooth $USER

# For USB devices (alternative)
sudo chmod 666 /dev/bus/usb/*/*
```

**Firewall Blocking Access**
```bash
# Check firewall status
sudo ufw status
sudo firewall-cmd --list-all  # (if using firewalld)

# Allow port 5000 (setup does this automatically)
sudo ufw allow 5000/tcp
sudo firewall-cmd --add-port=5000/tcp --permanent
```

**Missing Dependencies Error**
```bash
# Symptom: "Missing dependencies: numpy, scipy"
python main.py
# ❌ Don't run python directly!

# Solution: Use the provided launchers
./run_spectrum.sh          # ✅ Direct launcher
~/spectrum_ssh.sh          # ✅ Full diagnostic interface

# If dependencies are missing, reinstall:
./run_spectrum.sh --reinstall-deps

# Manual activation (if needed):
source venv/bin/activate
python main.py
```

**ModuleNotFoundError (psutil, etc.)**
```bash
# Symptom: "ModuleNotFoundError: No module named 'psutil'"
# Cause: Missing system monitoring dependencies

# Solution: Install missing packages
sudo apt-get update
sudo apt-get install -y python3-dev build-essential

# Reinstall Python dependencies
cd ~/spectrumsnek
source venv/bin/activate
pip install -r requirements.txt

# Or use the launcher to reinstall:
./run_spectrum.sh --reinstall-deps
```

**Service Not Starting on Boot**
```bash
# Symptom: Console shows "Error connecting to service" on boot
# Cause: Systemd service file missing, wrong path, or not enabled

# Solution: Re-run setup to fix service configuration
sudo ./setup.sh --full               # Recreates service with correct paths

# Enable service to start on boot:
./service_manager.sh enable

# Verify service is running:
./service_manager.sh status

# If console still can't connect, check:
./health_check.sh                    # Comprehensive diagnostics
./service_manager.sh logs           # Service startup logs
~/spectrum_startup.log              # Client connection logs

# Check service is using correct path:
sudo systemctl cat spectrum-service.service
```

**Port Already In Use Error**
```bash
# Symptom: "OSError: [Errno 98] Address already in use"
# Cause: Port 5000 is already being used (often by systemd service)

# Solution: Check service status first
./service_manager.sh status

# If service is running, connect to it instead:
~/spectrum_ssh.sh  # Will detect running service and show web interface

# If you need to restart the service:
./service_manager.sh restart

# Use different port (advanced):
python main.py --service --port 5001 --host 127.0.0.1

# Firewall issues (if remote access fails):
sudo ufw status                    # Check UFW status
sudo ufw allow 5000/tcp           # Allow port 5000
sudo firewall-cmd --add-port=5000/tcp  # Firewalld
sudo iptables -A INPUT -p tcp --dport 5000 -j ACCEPT
```

**Import Errors**
```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

**Textual Menu Fails in SSH / "Inappropriate ioctl for device"**
```bash
# Symptom: Interactive menu shows "Error in interactive menu: (25, 'Inappropriate ioctl for device')"
# Cause: Textual requires proper terminal capabilities not available in SSH

# Solution: The system automatically falls back to text-based menu
# Use number input instead of arrow keys
./run_spectrum.sh  # Shows numbered menu options
# Enter the number of the tool to launch

# For full curses support, use on Pi console/HDMI
# SSH works with text menu or web interface
```

**RTL-SDR PLL Not Locked Warning**
```bash
# Symptom: "[R82XX] PLL not locked!" during spectrum capture
# Cause: Tuner unable to lock to frequency (poor signal, antenna issues)

# Solution: Check antenna connection and positioning
# Try different frequencies or gain settings
# Use powered USB hub if power issues suspected
# Run dmesg | grep usb to check for USB errors
```

**Tools Crash on Hardware Errors (USB Overflows, Segfaults)**
```bash
# Symptom: Tools start then immediately crash or show errors
# Cause: Hardware/driver issues with RTL-SDR

# Solution: Ensure stable USB power and connection
# Check antenna and try different USB ports
# Verify RTL-SDR drivers: lsusb | grep RTL
# Test with short duration: ./run_scanner.sh --freq 100 --mode spectrum --duration 1
# Update USB configuration in /boot/cmdline.txt if needed
```

**Service Not Connecting in Local Mode**
```bash
# Symptom: Menu shows "using local mode" instead of connecting to service
# Cause: Service not running or network issues

# Solution: Start service manually
python spectrum_service.py &

# Check service logs for errors
tail -f /var/log/spectrum-service.log  # If using systemd

# Test API directly
curl http://localhost:5000/api/status
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
