#!/usr/bin/env python3

import os
import sys
import platform


class GhosttyInstaller:
    """Clean up macOS-specific Ghostty config that can override the symlinked config.

    On macOS, Ghostty reads config from multiple locations in this priority order:
      1. $XDG_CONFIG_HOME/ghostty/config
      2. ~/.config/ghostty/config          <-- our symlinked dotfile
      3. ~/Library/Application Support/com.mitchellh.ghostty/config

    Cmd+, in Ghostty opens a file called "config.ghostty" in the macOS Application
    Support directory. If that file exists with different content, it can be confusing
    (shown via Cmd+,) even though the higher-priority symlinked config is what Ghostty
    actually uses at runtime.

    This installer removes the stale macOS override so Cmd+, reflects reality.
    """

    MACOS_CONFIG_DIR = os.path.expanduser(
        "~/Library/Application Support/com.mitchellh.ghostty"
    )
    MACOS_CONFIG_FILE = os.path.join(MACOS_CONFIG_DIR, "config.ghostty")

    def __init__(self, console=None):
        self.console = console

    def log(self, message, style=None):
        if self.console:
            self.console.print(message, style=style)
        else:
            print(message)

    def execute(self, dry_run=False):
        if platform.system() != "Darwin":
            self.log("Not on macOS, skipping Ghostty macOS config cleanup.", style="green")
            return False

        if not os.path.exists(self.MACOS_CONFIG_FILE):
            self.log("No stale macOS Ghostty config found. Nothing to clean up.", style="green")
            return False

        if dry_run:
            self.log(
                f"Dry run: Would remove stale macOS Ghostty config at {self.MACOS_CONFIG_FILE}",
                style="cyan",
            )
            return True

        try:
            os.remove(self.MACOS_CONFIG_FILE)
            self.log(
                f"Removed stale macOS Ghostty config: {self.MACOS_CONFIG_FILE}",
                style="green",
            )
            self.log(
                "Ghostty will now use ~/.config/ghostty/config (symlinked from dotfiles).",
                style="green",
            )
            return True
        except OSError as e:
            self.log(f"Error removing macOS Ghostty config: {e}", style="red")
            return False
