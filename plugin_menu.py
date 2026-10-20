#!/usr/bin/env python3
"""Discover and launch installed SpectrumSnek plugins for the Whiptail menu."""

import argparse
import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PLUGINS_DIR = ROOT / "plugins"
# These plugins already have dedicated entries in run_spectrum.sh.
BUILTIN_PLUGINS = {"rtl_scanner", "radio_scanner", "system_tools", "__pycache__"}


def _clean(value):
    """Keep plugin metadata on one line so it is safe in the menu protocol."""
    return " ".join(str(value).replace("\t", " ").replace("\r", " ").replace("\n", " ").split())


def discover_plugins():
    """Return every installed plugin that implements the SpectrumSnek plugin API."""
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    plugins = []
    if not PLUGINS_DIR.is_dir():
        return plugins

    for path in sorted(PLUGINS_DIR.iterdir(), key=lambda item: item.name.casefold()):
        if (
            not path.is_dir()
            or path.name.startswith("_")
            or path.name in BUILTIN_PLUGINS
            or not (path / "__init__.py").is_file()
        ):
            continue

        try:
            module = importlib.import_module(f"plugins.{path.name}")
            get_info = getattr(module, "get_module_info", None)
            info = get_info() if callable(get_info) else getattr(module, "MODULE_INFO", {})
            if not isinstance(info, dict):
                info = {}
            run_function = getattr(module, "run", None)
            if not callable(run_function):
                print(f"Skipping plugin {path.name}: no callable run() entry point", file=sys.stderr)
                continue

            name = _clean(info.get("name") or path.name.replace("_", " ").title())
            description = _clean(info.get("description") or f"Run {name}")
            plugins.append((path.name, name, description))
        except Exception as exc:
            print(f"Skipping plugin {path.name}: {exc}", file=sys.stderr)

    return plugins


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--list", action="store_true", help="list installed plugins for the Whiptail menu")
    group.add_argument("--run", metavar="PLUGIN_ID", help="run an installed plugin by directory name")
    args = parser.parse_args()

    if args.list:
        for plugin_id, name, description in discover_plugins():
            print(f"{plugin_id}\t{name}\t{description}")
        return 0

    available = {plugin_id for plugin_id, _, _ in discover_plugins()}
    plugin_id = args.run
    if (
        not plugin_id
        or plugin_id.startswith("_")
        or "/" in plugin_id
        or "\\" in plugin_id
        or plugin_id not in available
    ):
        print(f"Plugin is not installed or does not implement the plugin API: {plugin_id}", file=sys.stderr)
        return 2

    try:
        module = importlib.import_module(f"plugins.{plugin_id}")
        module.run()
        return 0
    except KeyboardInterrupt:
        return 130
    except Exception as exc:
        print(f"Plugin {plugin_id} failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
