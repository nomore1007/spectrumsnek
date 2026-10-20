# OUI-Spy for SpectrumSnek

A Linux-native first implementation inspired by the documented ideas in the OUI-SPY project family. This is not ESP32 firmware and does not copy upstream source code or curated OUI lists.

## What it does

- Scans BLE advertisements through BlueZ using the optional Python package `bleak`.
- Lists nearby Wi-Fi access points visible to NetworkManager via `nmcli`.
- Matches configurable BLE manufacturer company IDs and MAC address prefixes against a local JSON file.
- Shows indicator confidence and keeps detections framed as clues, not proof of device identity.

## Run

From the repository root:

```bash
python3 -m plugins.oui_spy
```

Install the optional BLE dependency in the same Python environment used by SpectrumSnek:

```bash
python3 -m pip install bleak
```

On Debian/Raspberry Pi OS, ensure Bluetooth is enabled and BlueZ is installed. Wi-Fi AP scanning requires NetworkManager's `nmcli`; it does not change your active Wi-Fi connection or enable monitor mode. Hardware, drivers, adapter permissions, and OS policy affect what is visible.

Set `SPECTRUMSNEK_OUI_SPY_SIGNATURES=/path/to/signatures.json` to use a custom signature file.

## Signature format

- `ble_company_ids`: keys such as `0x09C8`, values with `label`, `confidence`, and source notes.
- `mac_prefixes`: MAC prefixes with or without separators, mapped to the same kind of metadata.

The included XUNTONG company-ID entry is a **low-confidence research indicator**, not a verified Flock Safety identifier. The source credit and reuse status are documented in the repository's `THIRD_PARTY_NOTICES.md`. The upstream curated lists are not included because their reuse terms were not established.

## Limitations

- This initial version does not perform Wi-Fi monitor-mode/promiscuous packet capture, raw 802.11 address-field analysis, or active probing.
- BLE advertisements may rotate addresses or omit manufacturer data.
- NetworkManager scan results are access points, not every Wi-Fi client device.
- A matching prefix/company ID can be shared by unrelated devices; validate findings independently.

## Credits and licensing

See the repository-level `THIRD_PARTY_NOTICES.md` for upstream project links, research credits, license review, and data provenance policy. Preserve these notices when modifying or redistributing this plugin.
