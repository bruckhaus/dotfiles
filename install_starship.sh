#!/bin/bash

# This is a simple wrapper around the Python-based Starship installer
# For more options, run the Python script directly: ./install_starship.py --help

echo "Running Starship installer..."
python3 "$(dirname "$0")/install_starship.py" "$@" 