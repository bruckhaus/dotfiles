#!/usr/bin/env python3

"""
Standalone script to install and configure Starship prompt.

This script can be run independently of the main dotfiles installer.
"""

import sys
import os

# Add the parent directory to the path so we can import the module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from installers.starship_installer import main
    
    if __name__ == "__main__":
        main()
except ImportError:
    print("Error: Could not import the starship_installer module.")
    print("Make sure the 'installers' directory exists and contains the starship_installer.py file.")
    sys.exit(1) 