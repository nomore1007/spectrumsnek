#!/usr/bin/env python3
"""
Frequency Bank Editor

Command-line tool for creating and editing XML frequency banks
for the traditional radio scanner.
"""

import os
import sys
import argparse
import xml.etree.ElementTree as ET
from xml.dom import minidom
from typing import List, Dict, Optional

class FrequencyBankEditor:
    """Editor for frequency bank XML files."""

    def __init__(self, banks_dir: str = "radio_scanner/banks"):
        self.banks_dir = banks_dir
        os.makedirs(banks_dir, exist_ok=True)

    def create_bank(self, filename: str, name: str, description: str = "") -> bool:
        """Create a new empty frequency bank."""
        filepath = os.path.join(self.banks_dir, filename)
        if os.path.exists(filepath):
            print(f"Error: Bank file '{filename}' already exists")
            return False

        # Create root element
        root = ET.Element("frequency_bank")
        root.set("name", name)
        root.set("description", description)

        # Write to file
        tree = ET.ElementTree(root)
        self._write_xml(tree, filepath)

        print(f"Created new frequency bank: {filename}")
        return True

    def add_frequency(self, bank_filename: str, freq_mhz: float, mode: str,
                     name: str, ctcss: Optional[float] = None,
                     dcs: Optional[str] = None) -> bool:
        """Add a frequency to an existing bank."""
        filepath = os.path.join(self.banks_dir, bank_filename)
        if not os.path.exists(filepath):
            print(f"Error: Bank file '{bank_filename}' does not exist")
            return False

        try:
            tree = ET.parse(filepath)
            root = tree.getroot()

            # Create frequency element
            freq_elem = ET.SubElement(root, "frequency")
            freq_elem.set("value", str(freq_mhz * 1e6))  # Convert to Hz
            freq_elem.set("mode", mode)
            freq_elem.set("name", name)

            # Add squelch if specified
            if ctcss is not None:
                squelch_elem = ET.SubElement(freq_elem, "squelch")
                squelch_elem.set("type", "CTCSS")
                squelch_elem.set("tone", str(ctcss))
            elif dcs is not None:
                squelch_elem = ET.SubElement(freq_elem, "squelch")
                squelch_elem.set("type", "DCS")
                squelch_elem.set("code", dcs)

            # Write back to file
            self._write_xml(tree, filepath)

            print(f"Added frequency {freq_mhz:.3f} MHz to {bank_filename}")
            return True

        except Exception as e:
            print(f"Error adding frequency: {e}")
            return False

    def list_banks(self) -> List[str]:
        """List all available bank files."""
        if not os.path.exists(self.banks_dir):
            return []

        banks = []
        for file in os.listdir(self.banks_dir):
            if file.endswith('.xml'):
                banks.append(file)

        return sorted(banks)

    def show_bank(self, bank_filename: str) -> bool:
        """Display contents of a frequency bank."""
        filepath = os.path.join(self.banks_dir, bank_filename)
        if not os.path.exists(filepath):
            print(f"Error: Bank file '{bank_filename}' does not exist")
            return False

        try:
            tree = ET.parse(filepath)
            root = tree.getroot()

            print(f"Bank: {root.get('name', bank_filename)}")
            print(f"Description: {root.get('description', '')}")
            print("-" * 50)

            for freq_elem in root.findall('frequency'):
                value_mhz = float(freq_elem.get('value', 0)) / 1e6
                mode = freq_elem.get('mode', 'FM')
                name = freq_elem.get('name', 'Unknown')

                squelch_info = ""
                squelch_elem = freq_elem.find('squelch')
                if squelch_elem is not None:
                    sq_type = squelch_elem.get('type')
                    if sq_type == 'CTCSS':
                        tone = squelch_elem.get('tone', '0')
                        squelch_info = f" CTCSS:{tone}"
                    elif sq_type == 'DCS':
                        code = squelch_elem.get('code', '023')
                        squelch_info = f" DCS:{code}"

                print(".3f")

            return True

        except Exception as e:
            print(f"Error reading bank: {e}")
            return False

    def _write_xml(self, tree, filepath: str):
        """Write XML tree to file with pretty formatting."""
        # Convert to string with pretty formatting
        root = tree.getroot()
        if root is None:
            raise ValueError("Invalid XML tree: no root element")

        rough_string = ET.tostring(root, encoding='unicode')
        reparsed = minidom.parseString(rough_string)
        pretty_xml = reparsed.toprettyxml(indent="  ")

        # Remove extra newlines
        lines = pretty_xml.split('\n')
        lines = [line for line in lines if line.strip()]
        pretty_xml = '\n'.join(lines)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(pretty_xml)
            f.write('\n')

def main():
    parser = argparse.ArgumentParser(description='Frequency Bank Editor')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Create command
    create_parser = subparsers.add_parser('create', help='Create a new frequency bank')
    create_parser.add_argument('filename', help='Bank filename (e.g., police.xml)')
    create_parser.add_argument('name', help='Bank display name')
    create_parser.add_argument('--desc', help='Bank description')

    # Add command
    add_parser = subparsers.add_parser('add', help='Add frequency to bank')
    add_parser.add_argument('bank', help='Bank filename')
    add_parser.add_argument('freq', type=float, help='Frequency in MHz')
    add_parser.add_argument('mode', choices=['AM', 'FM', 'DMR'], help='Modulation mode')
    add_parser.add_argument('name', help='Frequency name')
    add_parser.add_argument('--ctcss', type=float, help='CTCSS tone')
    add_parser.add_argument('--dcs', help='DCS code')

    # List command
    list_parser = subparsers.add_parser('list', help='List available banks')

    # Show command
    show_parser = subparsers.add_parser('show', help='Show bank contents')
    show_parser.add_argument('bank', help='Bank filename')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    editor = FrequencyBankEditor()

    if args.command == 'create':
        desc = args.desc or ""
        success = editor.create_bank(args.filename, args.name, desc)
        sys.exit(0 if success else 1)

    elif args.command == 'add':
        success = editor.add_frequency(args.bank, args.freq, args.mode, args.name,
                                     args.ctcss, args.dcs)
        sys.exit(0 if success else 1)

    elif args.command == 'list':
        banks = editor.list_banks()
        if banks:
            print("Available frequency banks:")
            for bank in banks:
                print(f"  {bank}")
        else:
            print("No frequency banks found")

    elif args.command == 'show':
        success = editor.show_bank(args.bank)
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()