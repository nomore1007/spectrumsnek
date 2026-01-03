#!/usr/bin/env python3
"""
System Tools Menu - SpectrumSnek 🐍📻

Submenu for system utilities including connectivity and updates.
"""

import curses
import subprocess
import time
import os
from typing import List, Dict, Any, Optional

class SystemTool:
    """Represents a system tool."""
    def __init__(self, name: str, description: str, action):
        self.name = name
        self.description = description
        self.action = action

class SystemMenu:
    """System tools submenu with curses interface."""

    def __init__(self):
        self.tools: List[SystemTool] = []
        self.selected_index = 0
        self.load_tools()

    def load_tools(self):
        """Load available system tools."""
        # WiFi Selector
        self.tools.append(SystemTool(
            "📶 WiFi Network Selector",
            "Scan and connect to WiFi networks",
            self.run_wifi_selector
        ))

        # Bluetooth Connector
        self.tools.append(SystemTool(
            "🔵 Bluetooth Device Connector",
            "Pair and connect to Bluetooth devices",
            self.run_bluetooth_connector
        ))

        # Audio Output Selector
        self.tools.append(SystemTool(
            "🔊 Audio Output Selector",
            "Select and test audio output devices including Bluetooth",
            self.run_audio_selector
        ))

        # TTY Display Settings
        self.tools.append(SystemTool(
            "🖥️ TTY Display Control",
            "Adjust font, resolution, and settings for TFT screens",
            self.show_display_control
        ))

        # Web portal status
        self.tools.append(SystemTool(
            "🌐 Web Portal Status",
            "Check web interface status (always enabled)",
            self.show_web_portal_status
        ))

        # Update from GitHub
        self.tools.append(SystemTool(
            "⬆️ Update from GitHub",
            "Pull latest updates from repository",
            self.update_from_github
        ))

    def run_wifi_selector(self):
        """Launch WiFi selector."""
        try:
            # Clean up current curses session before launching sub-tool
            curses.endwin()
            import wifi_tool
            wifi_tool.run()
        except ImportError:
            print("WiFi tool not available")
        except Exception as e:
            print(f"WiFi tool error: {e}")
        finally:
            input("Press Enter to continue...")

    def run_bluetooth_connector(self):
        """Launch Bluetooth connector."""
        try:
            # Clean up current curses session before launching sub-tool
            curses.endwin()
            import bluetooth_tool
            bluetooth_tool.run()
        except ImportError:
            print("Bluetooth tool not available")
        except Exception as e:
            print(f"Bluetooth tool error: {e}")
        finally:
            input("Press Enter to continue...")

    def run_audio_selector(self):
        """Launch Audio output selector."""
        try:
            # Clean up current curses session before launching sub-tool
            curses.endwin()
            from .audio_output_selector import AudioOutputSelector
            selector = AudioOutputSelector()
            selector.run()
        except ImportError:
            print("Audio selector not available")
        except Exception as e:
            print(f"Audio selector error: {e}")
        finally:
            input("Press Enter to continue...")

    def show_display_control(self):
        """TTY Display Control for TFT screens."""
        import logging

        # Set up logging with more detailed format
        logging.basicConfig(filename='/tmp/spectrumsnek_display.log',
                          level=logging.DEBUG,
                          format='%(asctime)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s')

        logging.info("=== TTY Display Control: Tool started ===")
        logging.debug(f"Python version: {__import__('sys').version}")
        logging.debug(f"Current working directory: {__import__('os').getcwd()}")

        try:
            # Clean up curses before showing text output (only if initialized)
            logging.debug("Attempting curses cleanup...")
            try:
                curses.endwin()
                logging.debug("Curses cleanup successful")
            except Exception as e:
                logging.debug(f"Curses cleanup skipped: {e}")

            print("TTY Display Control - TFT Screen Configuration")
            print("=" * 50)
            print("Configure display resolution for common Tinker board screens")
            print()
            logging.info("TTY Display Control header displayed")

            # Interactive screen size selection and configuration
            self._configure_display_resolution()

            logging.info("=== TTY Display Control: Tool completed successfully ===")

        except Exception as e:
            error_msg = f"Critical error in display control: {e}"
            print(f"ERROR: {error_msg}")
            logging.critical(error_msg)
            logging.exception("Full critical traceback:")
        finally:
            print("\nPress Enter to continue...")
            try:
                input()
                logging.debug("User pressed Enter to continue")
            except EOFError:
                logging.warning("EOF encountered, skipping input prompt")

    def _configure_display_resolution(self):
        """Interactive display resolution configuration for TFT screens with navigation."""
        import curses
        import logging

        # Common Tinker board TFT screen configurations
        screen_configs = [
            {
                'name': '1.5" TFT (320x240)',
                'resolution': '320x240',
                'hdmi_cvt': 'hdmi_cvt=320 240 60 1 0 0 0',
                'font': '8x8.psf'
            },
            {
                'name': '2.2" TFT (320x240)',
                'resolution': '320x240',
                'hdmi_cvt': 'hdmi_cvt=320 240 60 1 0 0 0',
                'font': 'VGA8x8.psf'
            },
            {
                'name': '2.4" TFT (320x240)',
                'resolution': '320x240',
                'hdmi_cvt': 'hdmi_cvt=320 240 60 1 0 0 0',
                'font': 'VGA8x8.psf'
            },
            {
                'name': '2.8" TFT (320x240)',
                'resolution': '320x240',
                'hdmi_cvt': 'hdmi_cvt=320 240 60 1 0 0 0',
                'font': 'VGA8x8.psf'
            },
            {
                'name': '3.2" TFT (320x240)',
                'resolution': '320x240',
                'hdmi_cvt': 'hdmi_cvt=320 240 60 1 0 0 0',
                'font': 'VGA8x8.psf'
            },
            {
                'name': '3.5" TFT (480x320)',
                'resolution': '480x320',
                'hdmi_cvt': 'hdmi_cvt=480 320 60 1 0 0 0',
                'font': 'VGA8x8.psf'
            },
            {
                'name': '4.0" TFT (480x320)',
                'resolution': '480x320',
                'hdmi_cvt': 'hdmi_cvt=480 320 60 1 0 0 0',
                'font': 'VGA8x8.psf'
            },
            {
                'name': '5.0" TFT (800x480)',
                'resolution': '800x480',
                'hdmi_cvt': 'hdmi_cvt=800 480 60 1 0 0 0',
                'font': 'VGA8x16.psf'
            },
            {
                'name': '7.0" TFT (1024x600)',
                'resolution': '1024x600',
                'hdmi_cvt': 'hdmi_cvt=1024 600 60 1 0 0 0',
                'font': 'VGA8x16.psf'
            }
        ]

        # Add cancel option
        cancel_option = {'name': 'Cancel / Back', 'cancel': True}

        # Create screen selection menu
        class ScreenMenu:
            def __init__(self, parent, screens):
                self.parent = parent
                self.screens = screens
                self.selected_index = 0

            def draw_menu(self, stdscr):
                """Draw the screen selection menu."""
                stdscr.clear()
                height, width = stdscr.getmaxyx()

                # Title
                title = "🖥️ TFT SCREEN CONFIGURATION"
                stdscr.addstr(0, (width - len(title)) // 2, title, curses.A_BOLD)

                # Subtitle
                subtitle = "↑↓ navigate, Enter select, 'q' quit"
                stdscr.addstr(2, (width - len(subtitle)) // 2, subtitle, curses.A_DIM)

                # Screen options
                start_y = 4
                for i, screen in enumerate(self.screens):
                    y = start_y + i
                    if y >= height:
                        break

                    if i == self.selected_index:
                        stdscr.addstr(y, 4, f"> {screen['name']}", curses.A_REVERSE | curses.A_BOLD)
                    else:
                        stdscr.addstr(y, 4, f"  {screen['name']}")

                stdscr.refresh()

            def run_menu(self, stdscr):
                """Run the screen selection menu."""
                curses.curs_set(0)

                while True:
                    self.draw_menu(stdscr)

                    try:
                        key = stdscr.getch()

                        if key == ord('q') or key == ord('Q'):
                            return None  # Cancel
                        elif key == curses.KEY_UP:
                            self.selected_index = max(0, self.selected_index - 1)
                        elif key == curses.KEY_DOWN:
                            self.selected_index = min(len(self.screens) - 1, self.selected_index + 1)
                        elif key == ord('\n') or key == ord('\r') or key == curses.KEY_ENTER:
                            selected_screen = self.screens[self.selected_index]
                            if 'cancel' in selected_screen:
                                return None  # Cancel
                            else:
                                return selected_screen  # Return selected config

                        time.sleep(0.05)

                    except KeyboardInterrupt:
                        return None

        # Run the screen selection menu
        screen_menu = ScreenMenu(self, screen_configs + [cancel_option])

        try:
            curses.wrapper(lambda stdscr: setattr(screen_menu, 'result', screen_menu.run_menu(stdscr)))
            selected_config = getattr(screen_menu, 'result', None)
        except (curses.error, Exception) as e:
            # Fallback to text selection
            print(f"Curses interface failed ({e}), using text selection...")
            selected_config = self._text_screen_selection(screen_configs)

        if selected_config:
            print(f"\nSelected: {selected_config['name']}")
            print("=" * (len(selected_config['name']) + 11))

            # Apply the configuration
            self._apply_screen_configuration(selected_config)

    def _text_screen_selection(self, screen_configs):
        """Fallback text-based screen selection."""
        print("Available TFT Screen Configurations:")
        print("====================================")

        for i, config in enumerate(screen_configs, 1):
            print(f"  {i}. {config['name']}")

        print("  0. Cancel / Back")
        print()

        while True:
            try:
                choice = input("Select your TFT screen size (0-9): ").strip()

                if choice == '0':
                    return None

                try:
                    index = int(choice) - 1
                    if 0 <= index < len(screen_configs):
                        return screen_configs[index]
                except ValueError:
                    pass

                print("Invalid choice. Please select 0-9.")

            except (KeyboardInterrupt, EOFError):
                return None

    def _apply_screen_configuration(self, config):
        """Apply the selected screen configuration."""
        import subprocess
        import logging

        print("Applying TFT Screen Configuration...")
        print(f"  Resolution: {config['resolution']}")
        print(f"  HDMI CVT: {config['hdmi_cvt']}")
        print(f"  Font: {config['font']}")
        print()

        success_count = 0
        total_steps = 4

        # Step 1: Configure HDMI output
        print("1. Configuring HDMI output...")
        try:
            # Update /boot/config.txt for Raspberry Pi
            config_lines = [
                f"{config['hdmi_cvt']}",
                "hdmi_group=2",
                "hdmi_mode=87",
                "disable_overscan=1"
            ]

            # Read existing config
            config_path = "/boot/config.txt"
            existing_config = ""
            try:
                with open(config_path, 'r') as f:
                    existing_config = f.read()
            except FileNotFoundError:
                print("   Note: /boot/config.txt not found (not a Raspberry Pi?)")
                existing_config = ""

            # Remove existing HDMI CVT lines
            lines = existing_config.split('\n')
            lines = [line for line in lines if not line.startswith('hdmi_cvt=')]

            # Add new configuration
            if "# TFT Display Settings" not in existing_config:
                lines.append("")
                lines.append("# TFT Display Settings")

            for line in config_lines:
                if line not in existing_config:
                    lines.append(line)

            # Write back
            with open(config_path, 'w') as f:
                f.write('\n'.join(lines))

            print("   ✅ HDMI configuration updated in /boot/config.txt")
            logging.info(f"HDMI config updated: {config['hdmi_cvt']}")
            success_count += 1

        except Exception as e:
            print(f"   ❌ Failed to update HDMI config: {e}")
            logging.error(f"HDMI config update failed: {e}")

        # Step 2: Set console font
        print("2. Setting console font...")
        try:
            font_path = f"/usr/share/consolefonts/{config['font']}"
            result = subprocess.run(['setfont', font_path],
                                  capture_output=True, text=True, timeout=10)

            if result.returncode == 0:
                print(f"   ✅ Console font set to {config['font']}")
                logging.info(f"Console font set: {config['font']}")
                success_count += 1
            else:
                print(f"   ❌ Failed to set font: {result.stderr}")
                logging.warning(f"Font setting failed: {result.stderr}")

        except Exception as e:
            print(f"   ❌ Font setting error: {e}")
            logging.error(f"Font setting error: {e}")

        # Step 3: Configure framebuffer
        print("3. Configuring framebuffer...")
        try:
            width, height = config['resolution'].split('x')
            result = subprocess.run(['fbset', '-fb', '/dev/fb0', '-xres', width, '-yres', height],
                                  capture_output=True, text=True, timeout=10)

            if result.returncode == 0:
                print(f"   ✅ Framebuffer set to {config['resolution']}")
                logging.info(f"Framebuffer set: {config['resolution']}")
                success_count += 1
            else:
                print(f"   ⚠️  Framebuffer setting may have failed: {result.stderr}")
                logging.warning(f"Framebuffer setting issue: {result.stderr}")
                # Don't count as failure since fbset might not be available

        except Exception as e:
            print(f"   ❌ Framebuffer configuration error: {e}")
            logging.error(f"Framebuffer config error: {e}")

        # Step 4: Disable screen blanking
        print("4. Disabling screen blanking...")
        try:
            result = subprocess.run(['setterm', '-blank', '0'],
                                  capture_output=True, text=True, timeout=5)

            if result.returncode == 0:
                print("   ✅ Screen blanking disabled")
                logging.info("Screen blanking disabled")
                success_count += 1
            else:
                print(f"   ❌ Failed to disable blanking: {result.stderr}")
                logging.warning(f"Blanking disable failed: {result.stderr}")

        except Exception as e:
            print(f"   ❌ Blanking disable error: {e}")
            logging.error(f"Blanking disable error: {e}")

        # Summary
        print()
        print("Configuration Summary:")
        print("======================")
        print(f"  Screen: {config['name']}")
        print(f"  Resolution: {config['resolution']}")
        print(f"  Steps completed: {success_count}/{total_steps}")
        print()

        if success_count >= 2:  # At least HDMI config and font worked
            print("✅ Configuration applied successfully!")
            print("📝 Note: Reboot required for HDMI changes to take effect.")
            print("🔄 Run 'sudo reboot' to apply display resolution changes.")
        else:
            print("⚠️  Configuration partially applied.")
            print("   Check system logs for details.")

        logging.info(f"Configuration completed: {success_count}/{total_steps} steps successful")

    def _show_current_display_info(self):
        """Show current display information."""
        import os
        import logging

        logging.info("=== Starting display info collection ===")

        print("Current Display Settings:")

        try:
            # Get terminal info
            logging.debug("Attempting to get terminal size...")
            rows, cols = os.get_terminal_size()
            print(f"  Terminal size: {cols} x {rows}")
            logging.info(f"Terminal size detected: {cols}x{rows}")
        except Exception as e:
            print(f"  Terminal size: (unable to detect - {e})")
            logging.warning(f"Terminal size detection failed: {e}")

        try:
            logging.debug("Getting terminal type from environment...")
            term = os.environ.get('TERM', 'unknown')
            print(f"  Terminal type: {term}")
            logging.info(f"Terminal type: {term}")
        except Exception as e:
            print("  Terminal type: (unable to detect)")
            logging.warning(f"Terminal type detection failed: {e}")

        # Check color support - avoid calling curses functions that require initscr()
        try:
            logging.debug("Checking color support...")
            # Just check if curses module is available, don't call functions that require initialization
            import curses as curses_module
            logging.debug("Curses module imported successfully")

            # We can't call has_colors() or access COLORS without initscr(), so just report availability
            print("  Color support: (requires curses initialization to detect)")
            print("  Curses module: Available")
            logging.info("Curses module available for color support detection")
        except ImportError as e:
            print("  Color support: (curses module not available)")
            logging.warning(f"Curses module not available: {e}")
        except Exception as e:
            print("  Color support: (unable to detect)")
            logging.error(f"Color support detection failed: {e}")
            logging.exception("Color support detection traceback:")

        # Check current font
        try:
            logging.debug("Attempting to read console font...")
            with open('/sys/devices/virtual/tty/tty0/console/font', 'r') as f:
                font_info = f.read().strip()
                print(f"  Console font: {font_info[:50]}...")
            logging.info(f"Console font read successfully: {font_info[:50]}...")
        except Exception as e:
            print("  Console font: (unable to read)")
            logging.warning(f"Console font read failed: {e}")

        print()
        logging.info("=== Display info collection completed ===")
        logging.info("=== Display info collection completed ===")

    def _show_screen_size_options(self):
        """Show recommended settings for different screen sizes."""
        print("Recommended Settings by Screen Size:")
        print("  1.5\" TFT (160x128 to 320x240):")
        print("    - Font: VGA8x8 or VGA8x16")
        print("    - Resolution: 320x240")
        print("    - Terminal: 40x15 to 53x15")
        print()
        print("  2.2\" TFT (176x132 to 320x240):")
        print("    - Font: VGA8x8 or VGA8x16")
        print("    - Resolution: 320x240")
        print("    - Terminal: 40x15 to 53x15")
        print()
        print("  2.4\" TFT (176x132 to 320x240):")
        print("    - Font: VGA8x8 or VGA8x16")
        print("    - Resolution: 320x240")
        print("    - Terminal: 40x15 to 53x15")
        print()
        print("  2.8\" TFT (176x132 to 320x240):")
        print("    - Font: VGA8x8 or VGA8x16")
        print("    - Resolution: 320x240")
        print("    - Terminal: 40x15 to 53x15")
        print()
        print("  3.2\" TFT (320x240):")
        print("    - Font: VGA8x8, VGA8x16, or 8x8")
        print("    - Resolution: 320x240")
        print("    - Terminal: 40x15 to 53x15")
        print()
        print("  3.5\" TFT (320x240 to 480x320):")
        print("    - Font: 8x8, VGA8x8, VGA8x16")
        print("    - Resolution: 480x320")
        print("    - Terminal: 60x20 to 80x24")
        print()
        print("  4.0\" TFT (480x320):")
        print("    - Font: 8x8, VGA8x8, VGA8x16")
        print("    - Resolution: 480x320")
        print("    - Terminal: 60x20 to 80x24")
        print()
        print("  5.0\" TFT (480x272 to 800x480):")
        print("    - Font: 8x8, VGA8x8, VGA8x16")
        print("    - Resolution: 800x480")
        print("    - Terminal: 100x30 to 133x30")
        print()
        print("  7.0\" TFT (800x480 to 1024x600):")
        print("    - Font: 8x8, VGA8x8, VGA8x16")
        print("    - Resolution: 1024x600")
        print("    - Terminal: 128x37 to 170x37")
        print()

    def _show_display_actions(self):
        """Show available display control actions."""
        print("Available Actions:")
        print("  1. Change console font")
        print("     setfont /usr/share/consolefonts/8x8.psf")
        print("     setfont /usr/share/consolefonts/VGA8x8.psf")
        print("     setfont /usr/share/consolefonts/VGA8x16.psf")
        print()
        print("  2. Adjust framebuffer resolution")
        print("     fbset -fb /dev/fb0 -xres 320 -yres 240")
        print("     fbset -fb /dev/fb0 -xres 480 -yres 320")
        print("     fbset -fb /dev/fb0 -xres 800 -yres 480")
        print()
        print("  3. Set display rotation (if supported)")
        print("     echo 0 | sudo tee /sys/class/graphics/fbcon/rotate")  # Normal
        print("     echo 1 | sudo tee /sys/class/graphics/fbcon/rotate")  # 90 degrees
        print("     echo 2 | sudo tee /sys/class/graphics/fbcon/rotate")  # 180 degrees
        print("     echo 3 | sudo tee /sys/class/graphics/fbcon/rotate")  # 270 degrees
        print()
        print("  4. Disable screen blanking")
        print("     setterm -blank 0")
        print()
        print("  5. Raspberry Pi display settings (/boot/config.txt)")
        print("     hdmi_group=2")
        print("     hdmi_mode=87")  # Custom CVT mode
        print("     hdmi_cvt=320 240 60 1 0 0 0")  # 320x240 @ 60Hz
        print("     hdmi_cvt=480 320 60 1 0 0 0")  # 480x320 @ 60Hz
        print("     hdmi_cvt=800 480 60 1 0 0 0")  # 800x480 @ 60Hz
        print()
        print("  6. Apply settings permanently")
        print("     - Add setfont commands to ~/.bashrc")
        print("     - Update /boot/config.txt for Pi")
        print("     - Create systemd service for auto-apply")
        print()

        # Interactive font selection
        self._interactive_font_selection()

    def _interactive_font_selection(self):
        """Provide interactive font selection."""
        print("Quick Font Setup:")
        print("=================")

        fonts = {
            '1': ('8x8', 'Small screens (1.5"-3.2")'),
            '2': ('VGA8x8', 'Standard VGA (2.4"-4.0")'),
            '3': ('VGA8x16', 'Large VGA (4.0"-7.0")'),
            '4': ('Uni2-Terminus16', 'Unicode support'),
            '5': ('Lat15-Terminus16', 'Latin extended')
        }

        for key, (font, desc) in fonts.items():
            print(f"  {key}. {font} - {desc}")

        print()
        print("To apply a font: setfont /usr/share/consolefonts/{font}.psf")
        print("Example: setfont /usr/share/consolefonts/8x8.psf")
        print()
        print("Note: Changes are temporary. Add to startup scripts for permanence.")

        # Show apply commands
        self._show_apply_commands()

    def _show_apply_commands(self):
        """Show commands to apply and save display settings."""
        print("Apply & Save Settings:")
        print("======================")

        print("1. Apply font immediately:")
        print("   sudo setfont /usr/share/consolefonts/VGA8x8.psf")
        print()

        print("2. Make font permanent (add to ~/.bashrc):")
        print("   echo 'sudo setfont /usr/share/consolefonts/VGA8x8.psf' >> ~/.bashrc")
        print()

        print("3. Apply framebuffer resolution:")
        print("   sudo fbset -fb /dev/fb0 -xres 480 -yres 320")
        print()

        print("4. Disable screen blanking:")
        print("   sudo setterm -blank 0")
        print()

        print("5. Raspberry Pi permanent settings (/boot/config.txt):")
        print("   sudo nano /boot/config.txt")
        print("   Add these lines:")
        print("   # TFT Display Settings")
        print("   hdmi_group=2")
        print("   hdmi_mode=87")
        print("   hdmi_cvt=480 320 60 1 0 0 0")
        print("   disable_overscan=1")
        print()

        print("6. Create display setup script:")
        print("   sudo nano /usr/local/bin/setup_display.sh")
        print("   Add these contents:")
        print("   #!/bin/bash")
        print("   setfont /usr/share/consolefonts/VGA8x8.psf")
        print("   setterm -blank 0")
        print("   fbset -fb /dev/fb0 -xres 480 -yres 320")
        print("   ")
        print("   sudo chmod +x /usr/local/bin/setup_display.sh")
        print()

        print("7. Auto-start display setup (systemd service):")
        print("   sudo nano /etc/systemd/system/display-setup.service")
        print("   Add these contents:")
        print("   [Unit]")
        print("   Description=Setup TFT Display")
        print("   After=getty.target")
        print("   ")
        print("   [Service]")
        print("   Type=oneshot")
        print("   ExecStart=/usr/local/bin/setup_display.sh")
        print("   RemainAfterExit=yes")
        print("   ")
        print("   [Install]")
        print("   WantedBy=multi-user.target")
        print("   ")
        print("   sudo systemctl enable display-setup.service")
        print()

    def run_text_menu(self):
        """Run a text-based menu for environments without curses support."""
        import logging

        # Set up logging
        logging.basicConfig(filename='/tmp/spectrumsnek_display.log',
                          level=logging.DEBUG,
                          format='%(asctime)s - %(levelname)s - %(message)s')

        logging.info("=== Starting System Tools Text Menu ===")

        print("\nSystem Tools - Text Menu")
        print("========================")

        while True:
            print("\nAvailable Tools:")
            for i, tool in enumerate(self.tools, 1):
                print(f"  {i}. {tool.name}")
                logging.debug(f"Tool {i}: {tool.name}")

            print("  0. Exit")
            print()

            try:
                choice = input("Select tool (0-6): ").strip()
                logging.info(f"User selected option: {choice}")

                if choice == '0':
                    logging.info("User exited text menu")
                    break
                elif choice.isdigit() and 1 <= int(choice) <= len(self.tools):
                    tool = self.tools[int(choice) - 1]
                    print(f"\nRunning: {tool.name}")
                    print("-" * (len(tool.name) + 9))
                    logging.info(f"Running tool: {tool.name}")

                    # Run the tool
                    try:
                        tool.action()
                        logging.info(f"Tool {tool.name} completed successfully")
                    except Exception as e:
                        error_msg = f"Error running {tool.name}: {e}"
                        print(error_msg)
                        logging.error(error_msg)
                        try:
                            input("Press Enter to continue...")
                        except EOFError:
                            logging.warning("EOF encountered during error handling")
                else:
                    error_msg = f"Invalid choice: {choice}. Please select 0-6."
                    print(error_msg)
                    logging.warning(error_msg)
            except (KeyboardInterrupt, EOFError) as e:
                exit_msg = f"Menu interrupted/exited: {type(e).__name__}"
                print("\nExiting...")
                logging.info(exit_msg)
                break
            except Exception as e:
                error_msg = f"Unexpected error in text menu: {e}"
                print(f"Error: {e}")
                logging.error(error_msg)
                break

        logging.info("=== System Tools Text Menu ended ===")

    def _show_screen_presets(self):
        """Show preset configurations for different screen sizes."""
        print("Screen Size Presets:")
        print("====================")

        presets = {
            "1.5-3.2inch": {
                "font": "8x8.psf",
                "resolution": "320x240",
                "terminal": "40x15",
                "cvt": "hdmi_cvt=320 240 60 1 0 0 0"
            },
            "3.2-4.0inch": {
                "font": "VGA8x8.psf",
                "resolution": "480x320",
                "terminal": "60x20",
                "cvt": "hdmi_cvt=480 320 60 1 0 0 0"
            },
            "5.0-7.0inch": {
                "font": "VGA8x16.psf",
                "resolution": "800x480",
                "terminal": "100x30",
                "cvt": "hdmi_cvt=800 480 60 1 0 0 0"
            }
        }

        for size, config in presets.items():
            print(f"{size.upper()} TFT:")
            print(f"  Font: {config['font']}")
            print(f"  Resolution: {config['resolution']}")
            print(f"  Terminal: ~{config['terminal']}")
            print(f"  Pi CVT: {config['cvt']}")
            print()

        print("To apply a preset:")
        print("1. Update /boot/config.txt with the CVT line")
        print("2. Reboot Raspberry Pi")
        print("3. Run: setfont /usr/share/consolefonts/{font}")
        print("4. Test: fbset -fb /dev/fb0 -xres {width} -yres {height}")
        print()

        # Offer to create an auto-setup script
        self._create_auto_setup_script()

    def _create_auto_setup_script(self):
        """Create an automatic display setup script."""
        print("Create Auto-Setup Script:")
        print("==========================")

        script_content = '''#!/bin/bash
# SpectrumSnek TFT Display Auto-Setup
# This script automatically configures display settings for TFT screens

echo "SpectrumSnek TFT Display Setup"
echo "=============================="

# Detect terminal size
TERMINAL_SIZE=$(stty size 2>/dev/null)
if [ $? -eq 0 ]; then
    ROWS=$(echo $TERMINAL_SIZE | cut -d" " -f1)
    COLS=$(echo $TERMINAL_SIZE | cut -d" " -f2)
    echo "Detected terminal size: ${COLS}x${ROWS}"
else
    echo "Could not detect terminal size, using defaults"
    COLS=80
    ROWS=24
fi

# Auto-detect screen size and apply settings
if [ $COLS -le 53 ] && [ $ROWS -le 20 ]; then
    echo "Detected: Small TFT screen (1.5-3.2 inch)"
    FONT="8x8.psf"
    XRES=320
    YRES=240
elif [ $COLS -le 80 ] && [ $ROWS -le 24 ]; then
    echo "Detected: Medium TFT screen (3.2-4.0 inch)"
    FONT="VGA8x8.psf"
    XRES=480
    YRES=320
elif [ $COLS -le 133 ] && [ $ROWS -le 37 ]; then
    echo "Detected: Large TFT screen (5.0-7.0 inch)"
    FONT="VGA8x16.psf"
    XRES=800
    YRES=480
else
    echo "Detected: Full-size display"
    FONT="Uni2-Terminus16.psf"
    # Keep current resolution
    exit 0
fi

echo "Applying settings..."
echo "- Font: $FONT"
echo "- Resolution: ${XRES}x${YRES}"

# Apply font (if available)
if [ -f "/usr/share/consolefonts/$FONT" ]; then
    setfont "/usr/share/consolefonts/$FONT" 2>/dev/null && echo "✓ Font applied" || echo "! Font application failed"
else
    echo "! Font file not found: /usr/share/consolefonts/$FONT"
fi

# Apply framebuffer resolution (if fbset available)
if command -v fbset >/dev/null 2>&1; then
    fbset -fb /dev/fb0 -xres $XRES -yres $YRES 2>/dev/null && echo "✓ Resolution applied" || echo "! Resolution application failed"
else
    echo "! fbset not available"
fi

# Disable screen blanking
setterm -blank 0 2>/dev/null && echo "✓ Screen blanking disabled" || echo "! Could not disable blanking"

echo "Display setup complete!"
'''

        print("Run this command to create the auto-setup script:")
        print("sudo tee /usr/local/bin/spectrum_display_setup.sh > /dev/null << 'EOF'")
        print(script_content)
        print("EOF")
        print()
        print("Then make it executable:")
        print("sudo chmod +x /usr/local/bin/spectrum_display_setup.sh")
        print()
        print("To run manually:")
        print("sudo /usr/local/bin/spectrum_display_setup.sh")
        print()
        print("To run at startup, add to /etc/rc.local or create a systemd service.")

        # Try to auto-detect appropriate font for current screen
        self._auto_detect_font()

    def _auto_detect_font(self):
        """Try to auto-detect appropriate font based on screen size."""
        try:
            import os
            rows, cols = os.get_terminal_size()

            print(f"\nAuto-Detection for {cols}x{rows} terminal:")
            print("-" * 40)

            # Determine screen category based on terminal size
            if cols <= 53 and rows <= 20:
                print("Detected: Small TFT screen (1.5\"-3.2\")")
                print("Recommended: setfont /usr/share/consolefonts/8x8.psf")
                print("Alternative: setfont /usr/share/consolefonts/VGA8x8.psf")
            elif cols <= 80 and rows <= 24:
                print("Detected: Medium TFT screen (3.2\"-4.0\")")
                print("Recommended: setfont /usr/share/consolefonts/VGA8x8.psf")
                print("Alternative: setfont /usr/share/consolefonts/VGA8x16.psf")
            elif cols <= 133 and rows <= 37:
                print("Detected: Large TFT screen (5.0\"-7.0\")")
                print("Recommended: setfont /usr/share/consolefonts/VGA8x16.psf")
                print("Alternative: setfont /usr/share/consolefonts/8x8.psf")
            else:
                print("Detected: Full-size display or high-resolution TFT")
                print("Recommended: setfont /usr/share/consolefonts/Uni2-Terminus16.psf")
                print("Alternative: Use default system font")

        except Exception as e:
            print(f"Could not auto-detect screen size: {e}")
            print("Manual font selection recommended.")

        print()

        # Show common resolution commands for the detected size
        self._show_resolution_commands()

    def _show_resolution_commands(self):
        """Show resolution adjustment commands."""
        print("Common Resolution Commands:")
        print("===========================")

        resolutions = [
            ("320x240", "Small TFT (1.5\"-3.5\")", "fbset -fb /dev/fb0 -xres 320 -yres 240"),
            ("480x320", "Medium TFT (3.5\"-4.0\")", "fbset -fb /dev/fb0 -xres 480 -yres 320"),
            ("800x480", "Large TFT (5.0\"-7.0\")", "fbset -fb /dev/fb0 -xres 800 -yres 480"),
            ("1024x600", "Extra Large TFT (7.0+\")", "fbset -fb /dev/fb0 -xres 1024 -yres 600")
        ]

        for res, desc, cmd in resolutions:
            print(f"  {res} ({desc}):")
            print(f"    {cmd}")
            print()

        print("Raspberry Pi /boot/config.txt examples:")
        print("  # For 3.5\" TFT")
        print("  hdmi_group=2")
        print("  hdmi_mode=87")
        print("  hdmi_cvt=480 320 60 1 0 0 0")
        print()
        print("  # For 5.0\" TFT")
        print("  hdmi_group=2")
        print("  hdmi_mode=87")
        print("  hdmi_cvt=800 480 60 1 0 0 0")
        print()

        # Show current framebuffer info if available
        self._show_framebuffer_info()

    def _show_framebuffer_info(self):
        """Show current framebuffer information."""
        print("Current Framebuffer Status:")
        print("-" * 30)

        import subprocess
        try:
            # Try to get framebuffer info
            result = subprocess.run(['fbset', '-fb', '/dev/fb0'],
                                  capture_output=True, text=True, timeout=5)

            if result.returncode == 0:
                # Parse fbset output for key info
                lines = result.stdout.split('\n')
                for line in lines:
                    if any(keyword in line.lower() for keyword in ['geometry', 'timings', 'rgba']):
                        print(f"  {line.strip()}")
            else:
                print("  Could not read framebuffer info (fbset failed)")

        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
            print("  fbset not available or no framebuffer device")
        except Exception as e:
            print(f"  Error reading framebuffer: {e}")

        print()

    def show_web_portal_status(self):
        """Show web portal status."""
        try:
            # Clean up curses before showing text output (only if initialized)
            try:
                curses.endwin()
            except:
                pass  # Curses not initialized, that's fine

            print("Web Portal Status")
            print("=================")
            print("The web interface is always enabled and running.")
            print("Access it at: http://localhost:5000")
            print("")
            print("Available tools:")
            print("- ADS-B Aircraft Tracker")
            print("- Traditional Radio Scanner")
            print("- RTL-SDR Spectrum Analyzer")
            print("- Demo Spectrum Analyzer")
            print("- System Tools (this menu)")
            print("")
            print("The web interface provides:")
            print("- Real-time tool control")
            print("- Status monitoring")
            print("- Remote access capabilities")

        except Exception as e:
            print(f"Error showing web portal status: {e}")
        finally:
            print("\nPress Enter to continue...")
            input()

    def update_from_github(self):
        """Update from GitHub repository."""
        try:
            # Clean up curses before showing text output (only if initialized)
            try:
                curses.endwin()
            except:
                pass  # Curses not initialized, that's fine

            print("Updating from GitHub...")
            print("Running: git pull")

            # Change to repo directory if needed
            repo_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            os.chdir(repo_dir)

            result = subprocess.run(
                ["git", "pull"],
                capture_output=True, text=True, timeout=60
            )

            if result.returncode == 0:
                print("✅ Update successful!")
                print(result.stdout.strip())
                if "Already up to date" in result.stdout:
                    print("Your SpectrumSnek is already up to date.")
                else:
                    print("New updates installed successfully.")
                    print("The program will now exit. Please run ./run.sh to restart with the updates.")
                    import sys
                    sys.exit(0)
            else:
                print("❌ Update failed!")
                print("Error:", result.stderr.strip())

        except subprocess.TimeoutExpired:
            print("❌ Update timeout")
        except Exception as e:
            print(f"❌ Update error: {e}")
        finally:
            print("\nPress Enter to continue...")
            input()

    def draw_menu(self, stdscr):
        """Draw the system tools menu."""
        stdscr.clear()
        height, width = stdscr.getmaxyx()

        # Fallback for narrow terminals
        if width < 40:
            try:
                term_size = os.get_terminal_size()
                width = term_size.columns
                height = min(height, term_size.lines)
            except:
                width = 80  # Default fallback

        # Title
        title = "System Tools 🐍📻"
        stdscr.addstr(0, (width - len(title)) // 2, title, curses.A_BOLD)

        # Subtitle
        subtitle = "Connectivity and maintenance utilities"
        stdscr.addstr(2, (width - len(subtitle)) // 2, subtitle)

        # Tools
        start_y = 4
        for i, tool in enumerate(self.tools):
            y = start_y + i
            if y >= height:
                break

            # Tool name with selection indicator
            if i == self.selected_index:
                stdscr.addstr(y, 2, f"> {tool.name}", curses.A_REVERSE | curses.A_BOLD)
            else:
                stdscr.addstr(y, 2, f"  {tool.name}")

        # Instructions
        instructions = "↑↓ navigate, Enter select, 'b' back, 'q' quit all"
        stdscr.addstr(height - 1, (width - len(instructions)) // 2, instructions, curses.A_DIM)

        stdscr.refresh()

    def run_menu(self, stdscr):
        """Run the system tools menu."""
        curses.curs_set(0)

        while True:
            self.draw_menu(stdscr)

            try:
                key = stdscr.getch()

                if key == ord('q') or key == ord('Q'):
                    import sys
                    sys.exit(0)  # Quit completely
                elif key == ord('b') or key == ord('B'):
                    return True  # Back to main menu
                elif key == curses.KEY_UP:
                    self.selected_index = max(0, self.selected_index - 1)
                elif key == curses.KEY_DOWN:
                    self.selected_index = min(len(self.tools) - 1, self.selected_index + 1)
                elif key == ord('\n') or key == ord('\r') or key == curses.KEY_ENTER:
                    tool = self.tools[self.selected_index]
                    # Run the tool - it will handle curses cleanup
                    tool.action()
                    # After tool finishes, return to exit the submenu
                    return False
                elif key == 27:  # ESC
                    return True  # Back

                time.sleep(0.05)

            except KeyboardInterrupt:
                return False

    def run(self):
        """Main run method."""
        print("System Tools")
        print("============")

        try:
            # SystemMenu always uses text mode for compatibility with parent menus
            # and remote sessions
            import os
            is_remote = any(os.environ.get(var) for var in ['SSH_CLIENT', 'SSH_TTY', 'SSH_CONNECTION'])

            if is_remote:
                print("Remote session detected, using text menu...")
            else:
                print("Using text menu for compatibility...")

            self.run_text_menu()
            back_to_main = False

        except KeyboardInterrupt:
            print("\nSystem tools stopped by user")
        except Exception as e:
            print(f"Error in system tools menu: {e}")

if __name__ == "__main__":
    menu = SystemMenu()
    menu.run()