#!/usr/bin/env python3
"""Discover and launch installed SpectrumSnek plugins for the whiptail menu."""

import argparse
import importlib
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PLUGINS_DIR = ROOT / "plugins"
EXCLUDED_PLUGINS = {"system_tools", "__pycache__"}


def discover_plugins():
    """Return installed plugins that implement the SpectrumSnek plugin contract."""
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    plugins = []
    if not PLUGINS_DIR.is_dir():
        return plugins

    for path in sorted(PLUGINS_DIR.iterdir(), key=lambda item: item.name.casefold()):
        if (
            not path.is_dir()
            or path.name.startswith("_")
            or path.name in EXCLUDED_PLUGINS
            or not (path / "__init__.py").is_file()
        ):
            continue

        try:
            module = importlib.import_module(f"plugins.{path.name}")
            get_info = getattr(module, "get_module_info", None)
            run = getattr(module, "run", None)
            if not callable(get_info) or not callable(run):
                continue

            info = get_info() or {}
            name = str(info.get("name") or path.name).replace("\\t", " ").replace("\\n", " ")
            plugins.append((path.name, name))
        except Exception as exc:
            print(f"Skipping plugin {path.name}: {exc}", file=sys.stderr)

    return plugins


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list", action="store_true", help="list installed plugins as tab-separated ID and name")
    parser.add_argument("--run", metavar="PLUGIN_ID", help="run an installed plugin by directory name")
    args = parser.parse_args()

    if args.list:
        for plugin_id, name in discover_plugins():
            print(f"{plugin_id}\\t{name}")
        return 0

    if args.run:
        available = dict((plugin_id, name) for plugin_id, name in discover_plugins())
        if args.run not in available:
            print(f"Plugin is not installed or does not implement the plugin API: {args.run}", file=sys.stderr)
            return 2
        try:
            module = importlib.import_module(f"plugins.{args.run}")
            module.run()
            return 0
        except KeyboardInterrupt:
            return 130
        except Exception as exc:
            print(f"Plugin {args.run} failed: {exc}", file=sys.stderr)
            return 1

    parser.error("choose --list or --run PLUGIN_ID")


if __name__ == "__main__":
    raise SystemExit(main())
