# SpectrumSnek 🐍📻

**A modular radio, SDR, and wireless-observation toolkit for Raspberry Pi and Linux.**

SpectrumSnek brings radio tools together behind one terminal interface, with independently maintained plugins and shared hardware-management helpers. The core provides the launcher, device status, plugin discovery and installation, configuration utilities, and update workflow. Features can be added as plugins without folding each tool into the core repository.

> **Project status:** actively evolving. The default launcher currently uses the Textual terminal UI. The older Whiptail menu remains available as a temporary fallback.

## What you can do

- **Software-defined radio:** use supported RTL-SDR hardware with compatible tools and plugins.
- **Aircraft tracking:** the ADS-B Radar plugin uses `readsb` to decode ADS-B and displays aircraft in a terminal radar view.
- **Radio scanning:** install the separate Radio Scanner plugin for scanning workflows.
- **Spectrum analysis:** install the separate Analyzer plugin.
- **Wireless observation:** OUI-Spy can display nearby BLE advertisements and visible Wi-Fi access points, where supported by the host hardware and software.
- **LoRa-band monitoring:** the LoRa Monitor plugin surveys RF energy in LoRa bands. Energy detections are not packet decoding.
- **System utilities:** access available Wi-Fi, Bluetooth, audio, and service tools.
- **Plugin management:** install, update, change branches, or remove known plugins, and add compatible public GitHub plugins.
- **Diagnostics:** setup and runtime errors are recorded locally in `error.log`.

SpectrumSnek is a toolkit, not a guarantee that every feature works on every Linux host. Hardware, drivers, permissions, installed system services, and plugin requirements affect availability.

## Requirements

- Raspberry Pi OS or another Debian-based Linux distribution.
- Python 3 and `python3-venv`.
- Git and `apt`/APT-compatible package management for the standard setup flow.
- A terminal with keyboard input.
- RTL-SDR hardware for SDR features; compatible Wi-Fi and Bluetooth hardware for the corresponding features.
- Internet access for initial setup and for installing or updating plugins.

The setup script installs system and Python dependencies, creates the project virtual environment, attempts to install ADS-B Radar, and builds a project-local copy of `readsb` with RTL-SDR support. The build is kept conservative for lower-memory Raspberry Pi devices.

## Install

Clone the core repository and run setup:

```bash
git clone https://github.com/nomore1007/spectrumsnek.git
cd spectrumsnek
chmod +x setup.sh spectrumsnek.sh
./setup.sh
```

Setup may use `sudo` to install system packages if the current account is not root and sudo is available. Keep the project directory writable by the account that will run SpectrumSnek.

The ADS-B plugin is installed automatically as part of setup. If plugin installation fails, the launcher’s plugin manager can retry it later. Setup also builds `readsb` from upstream source and installs the resulting binary under `.local/bin/readsb`, rather than assuming the distribution's `readsb` package has RTL-SDR support.

## Start SpectrumSnek

```bash
./spectrumsnek.sh
```

Use the keyboard to navigate the terminal interface. The main screen shows a quick status for RTL-SDR, Wi-Fi, and Bluetooth detection. Press **r** to refresh hardware status and **q** to quit.

To run the Textual interface directly:

```bash
./venv/bin/python textual_menu.py
```

To temporarily use the legacy Whiptail interface:

```bash
SPECTRUMSNEK_LEGACY_MENU=1 ./spectrumsnek.sh
```

### Utilities and add-ons

Open **Utilities** for plugin management, configuration/service controls, and core updates.

The add-on manager supports these known plugins:

| Add-on | Repository | Purpose |
| --- | --- | --- |
| **ADS-B Radar** | [spectrumsnek-adsb](https://github.com/nomore1007/spectrumsnek-adsb) | Aircraft tracking using `readsb` and a terminal radar display |
| **OUI-Spy** | [spectrumsnek-oui-spy](https://github.com/nomore1007/spectrumsnek-oui-spy) | BLE advertisement and visible Wi-Fi access-point observation |
| **LoRa Monitor** | [spectrumsnek-lora](https://github.com/nomore1007/spectrumsnek-lora) | Passive LoRa-band RF energy survey |
| **Analyzer** | [spectrumsnek-analyzer](https://github.com/nomore1007/spectrumsnek-analyzer) | Spectrum analyzer plugin |
| **Radio Scanner** | [spectrumsnek-scanner](https://github.com/nomore1007/spectrumsnek-scanner) | Radio scanner plugin |

The manager can install, update, change the selected branch, and remove known plugins. The Textual interface also offers installation from a public GitHub URL. Third-party plugins must follow the SpectrumSnek plugin API and provide an `__init__.py` at the repository root.

Plugins are separate repositories installed under `plugins/<plugin_id>/`. The core updater intentionally preserves these ignored plugin directories when updating the core checkout. Removing a plugin deletes its local plugin directory and Git checkout.

## ADS-B and RTL-SDR notes

ADS-B Radar uses [readsb](https://github.com/wiedehopf/readsb) for decoding instead of maintaining a separate custom ADS-B decoder. The plugin and core setup use a project-local RTL-SDR-enabled build at:

```text
.local/bin/readsb
```

The plugin shares the core `sdr_manager.py` helper to coordinate access among SpectrumSnek components that use the manager. This cannot prevent unrelated programs from opening the same dongle without cooperating with the manager. Avoid running multiple independent decoders against one receiver.

The ADS-B plugin can also be configured to use an externally managed `readsb` process. See the [ADS-B plugin README](https://github.com/nomore1007/spectrumsnek-adsb) for its environment variables, setup details, and external-mode instructions.

A detected USB device does not by itself guarantee that it is accessible, supported by the driver, or available to a particular plugin.

## OUI-Spy interpretation and limitations

OUI-Spy displays nearby BLE advertisements and Wi-Fi access points using the host's supported interfaces. Its Wi-Fi view lists access points, not every client connected to them. It does not enable monitor mode or capture raw 802.11 traffic.

Device addresses may rotate, advertisements may omit manufacturer data, and manufacturer IDs or address prefixes can be shared by unrelated devices. Treat signature matches as research indicators, not proof of device identity or ownership. Review the [OUI-Spy README](https://github.com/nomore1007/spectrumsnek-oui-spy) for signature configuration and data provenance.

## Updating

Use **Utilities → Update SpectrumSnek** and choose the branch offered by the interface. The update workflow fetches from the configured `origin` and applies a fast-forward update where possible. Local modifications, branch conflicts, or uncommitted work can prevent an update; inspect Git status and back up changes before attempting a manual recovery.

Plugin updates are managed separately from core updates. Use the add-on manager to update an individual plugin or update all installed Git-based plugins.

## Logs and troubleshooting

Setup output is written to `setup.log`. Captured setup and runtime errors are appended to `error.log`, with timestamps and a source tag.

View recent errors:

```bash
tail -n 100 error.log
tail -n 100 setup.log
```

Follow runtime errors as they appear:

```bash
tail -f error.log
```

Check whether the USB receiver is visible:

```bash
lsusb
```

Check the virtual environment:

```bash
test -x venv/bin/python && echo "Virtual environment found"
```

If a feature cannot access the SDR, check that the receiver is connected and permitted, that the required driver/libraries are installed, and that another program is not already using it. SpectrumSnek's shared manager only coordinates components that use that manager.

Logs may include command output, local paths, and diagnostic details. Review them before sharing publicly. Local logs are ignored by Git and are not uploaded by core updates.

## Development

Useful core files:

| File | Role |
| --- | --- |
| `spectrumsnek.sh` | Launcher and legacy Whiptail fallback |
| `textual_menu.py` | Default Textual terminal interface |
| `spectrum_core.py` | Shared tool catalog and device-status helpers |
| `plugin_menu.py` | Discover and launch installed plugins |
| `plugin_manager.sh` | Install, update, branch-switch, list, and remove plugins |
| `sdr_manager.py` | Shared RTL-SDR access coordination |
| `setup.sh` | System dependencies, virtual environment, ADS-B setup, and `readsb` build |
| `tests/` | Core tests |

Run the available tests from the project root:

```bash
source venv/bin/activate
python -m unittest discover -s tests
```

### Plugin API

A plugin is installed in `plugins/<plugin_id>/` and must provide:

- A root-level `__init__.py`.
- A callable, no-argument `run()` entry point.
- Plugin metadata through `MODULE_INFO` and/or `get_module_info()`.

Discovery skips plugins that cannot be imported or do not provide a callable `run()`. Plugins should use the shared core helpers rather than maintaining competing copies of shared device-management code.

To register a known plugin in the managed add-on catalog, add its stable ID, repository URL, and display label in `plugin_manager.sh`, and add it to the manager's listing and UI. Test both a fresh install and an update of an already installed plugin.

## License

SpectrumSnek is distributed under the MIT License. See [LICENSE.txt](LICENSE.txt).
