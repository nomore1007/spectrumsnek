# SpectrumSnek 🐍📻

A modular radio and SDR toolkit for Raspberry Pi and Linux, with a Whiptail launcher, independently installed plugins, and shared RTL-SDR device management.

## What it includes

- **RTL-SDR scanner:** listen to and inspect supported radio signals.
- **Traditional radio scanner:** scan configurable frequency banks.
- **ADS-B Radar plugin:** receive aircraft data using an RTL-SDR and an RTL-SDR-enabled `readsb` build.
- **OUI-Spy plugin:** BLE advertisement and visible Wi-Fi access-point scanning, as supported by the plugin.
- **System tools:** Wi-Fi selection, Bluetooth connection, and audio output management.
- **Plugin manager:** install or remove known plugins without merging their code into the core repository.
- **Utilities:** update the core, manage installed plugins, and configure the optional web service.
- **Error log:** runtime errors are appended to `error.log` for later troubleshooting.

The stable main interface currently uses **Whiptail**. An experimental Textual interface is available with `./venv/bin/python textual_menu.py`; it shares device detection and plugin discovery with the web-service work and is being evaluated before replacing the default launcher.

## Requirements

- Raspberry Pi OS or another Debian-based Linux distribution.
- Python 3 and `python3-venv`.
- Git and Whiptail.
- RTL-SDR USB hardware for SDR features. Wi-Fi, Bluetooth, and audio features depend on the hardware and system configuration.
- Internet access during setup and when installing/updating plugins.

## Install

Clone the core repository and run setup:

```bash
git clone https://github.com/nomore1007/spectrumsnek.git
cd spectrumsnek
chmod +x setup.sh spectrumsnek.sh
./setup.sh
```

Setup installs system/Python dependencies, creates the `venv/` environment, and attempts to install the ADS-B Radar plugin automatically. If ADS-B installation fails, the setup output explains that it can be retried from the launcher.

If your system requires elevated privileges for package installation, run setup with `sudo` only if needed by your environment. The project directory and virtual environment must remain writable by the account that runs SpectrumSnek.

## Launch

```bash
./spectrumsnek.sh
```

Use the arrow keys and Enter to navigate. Choose **Utilities** for:

- **Check for and install updates:** fetches `origin/master`, checks for newer commits, and asks before applying updates. If local changes or untracked files block the update, you can choose to overwrite them. That option discards tracked-file changes and deletes untracked, non-ignored files.
- **Installed Plugins:** select ADS-B Radar or OUI-Spy to install it. Deselecting an installed plugin offers to remove it.
- **Configure → Configure Web Service:** install the systemd service, enable it at boot, and manage start/stop/restart/status/logs. The web service runs `spectrum_service.py` directly; the launcher does not use service-mode flags.

### Known plugins

| Display name | Repository | Install location |
| --- | --- | --- |
| ADS-B Radar | [spectrumsnek-adsb](https://github.com/nomore1007/spectrumsnek-adsb) | `plugins/adsb_radar/` |
| OUI-Spy | [spectrumsnek-oui-spy](https://github.com/nomore1007/spectrumsnek-oui-spy) | `plugins/oui_spy/` |

Plugin code is maintained in its own repository. The plugin manager only installs the known repository associated with each plugin ID and refuses to overwrite an existing non-Git directory at that plugin path.

## Error logging

Errors from the launcher and setup process are appended to:

```
error.log
```

Each captured error line is timestamped and tagged with the source. The launcher also logs errors written by tools it starts, including plugin installation failures. Setup's normal output is kept in `setup.log`; setup errors are additionally recorded in `error.log`.

View recent errors:

```bash
tail -n 100 error.log
```

Follow new errors as they appear:

```bash
tail -f error.log
```

Logs may contain command output, local paths, or diagnostic details. Review them before sharing publicly. Log files are ignored by Git and are not uploaded by core updates.

## Updating

From the launcher, select **Utilities → Check for and install updates**.

The updater targets the `master` branch. If you choose the overwrite option, it runs a hard reset to the remote branch and removes untracked, non-ignored files. Ignored files such as local logs and independently installed plugin directories are preserved. Back up local changes before confirming.

## Troubleshooting

1. Check the latest captured errors:

   ```bash
   tail -n 100 error.log
   ```

2. Check setup output:

   ```bash
   tail -n 100 setup.log
   ```

3. Confirm the virtual environment exists:

   ```bash
   test -x venv/bin/python && echo "Virtual environment found"
   ```

4. Confirm the RTL-SDR is visible:

   ```bash
   lsusb
   ```

5. Check whether a receiver service is already using the dongle. SpectrumSnek's `sdr_manager.py` coordinates SDR access among participating SpectrumSnek components, but it cannot lock out unrelated programs that do not use that manager.

If an error is not recorded, reproduce it from `./spectrumsnek.sh` in a terminal so its output can be captured.

## Development

- Core launcher: `spectrumsnek.sh`
- Plugin discovery: `plugin_menu.py`
- Known-plugin installer: `plugin_manager.sh`
- Shared RTL-SDR ownership: `sdr_manager.py`
- Setup: `setup.sh`
- Tests: `tests/`

Run the available tests from the project root:

```bash
source venv/bin/activate
python -m unittest discover -s tests
```

New plugins should live in their own repositories and expose the interface expected by `plugin_menu.py`. Add the repository and stable plugin ID to `plugin_manager.sh` before listing it as a known plugin.

## License

SpectrumSnek is distributed under the MIT License. See [LICENSE.txt](LICENSE.txt).
