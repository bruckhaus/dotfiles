#!/usr/bin/env python3

import os
import sys
import shutil
import argparse
import time
import json
from datetime import datetime
import stat

# Add the directory containing the script to the Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

# Import required third-party modules
try:
    import humanize
    import randfacts
except ImportError as e:
    print(f"Error importing required module: {e}")
    print("Please ensure all required modules are installed in your virtual environment.")
    sys.exit(1)

# Define default values
STASH_DIR_DEFAULT = os.path.expanduser('~/.stash')
STASH_LOG = os.path.join(STASH_DIR_DEFAULT, '.stash_log.json')
VERBOSITY_DEFAULT = 'verbose'

# Ensure the stash directory exists
os.makedirs(STASH_DIR_DEFAULT, exist_ok=True)

DESCRIPTION = f"""
Stash Script: A versatile file management utility

This script provides a command-line tool for securely managing files by stashing them in a specified directory. 
It offers features such as file stashing with user confirmation, undo functionality for restoring files, 
conflict resolution for existing files, detailed reporting including file properties and fun facts, 
and dry run capabilities. The script supports various verbosity levels and uses human-readable formats 
for file sizes and timestamps. It's designed to be both user-friendly and informative, helping users 
manage their files with confidence and ease.

Defaults:
- Stash Directory: {STASH_DIR_DEFAULT}
- Verbosity Level: {VERBOSITY_DEFAULT}

Stash Log:
- Location: {STASH_LOG}
- Purpose: Keeps track of all stash operations for undo functionality and file tracking.
           This log is automatically maintained and should not be manually edited.

Undo Functionality:
The undo feature allows you to restore a previously stashed file to its original location.
To use the undo feature:
1. Use the --undo or -u flag followed by the name of the stashed file.
2. Specify the restore location using --restore_location or -r.
3. The restore location should be the directory where the file was originally located.

Example:
stash -u stashed_file.txt -r /path/to/original/directory

Note: The full undo command is provided at the end of each stash report for easy reference.
"""


def get_human_readable_permissions(mode):
    perms = stat.filemode(mode)
    return f"{perms} ({oct(mode & 0o777)[2:]})"


def get_dir_size(path):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if os.path.isfile(fp):
                total_size += os.path.getsize(fp)
    return total_size


def move_to_stash(file_path, stash_dir=STASH_DIR_DEFAULT, dry_run=False, verbosity='verbose', force=False):
    if not os.path.exists(stash_dir):
        os.makedirs(stash_dir)
        if verbosity != 'silent':
            print(f'Stash directory created at: {stash_dir}')

    if not os.path.isfile(file_path):
        print(f'Error: The file {file_path} does not exist.')
        return

    file_info = os.stat(file_path)
    original_size = file_info.st_size
    file_type = os.path.splitext(file_path)[1].lower()
    permissions = get_human_readable_permissions(file_info.st_mode)
    stash_file_path = os.path.join(stash_dir, os.path.basename(file_path))
    original_dir = os.path.dirname(os.path.abspath(file_path))

    if dry_run:
        print(f'Dry run: Would move {file_path} to {stash_file_path}.')
        if os.path.exists(stash_file_path):
            print("It already exists in the stash.")
        print(f'Original Size: {humanize.naturalsize(original_size)}')
        print(f'File Type: {file_type if original_size > 0 else "N/A"}')
        print(f'Permissions: {permissions}')
        print(f'Sample Content (Top 5 Lines):')
        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()
                print(''.join(lines[:5]))
        except UnicodeDecodeError:
            print("Unable to preview file: not a text file or uses unknown encoding.")
        return

    if not force:
        confirm = input(f'Are you sure you want to move {file_path} to {stash_dir}? (y/n): ')
        if confirm.lower() != 'y':
            print('Move operation cancelled.')
            return

    if os.path.exists(stash_file_path):
        if not force:
            choice = input(
                f"A file with the name '{os.path.basename(file_path)}' already exists in the stash. Choose an option:\n"
                "1. Overwrite existing file\n"
                "2. Save with a modified name\n"
                "3. Cancel operation\n"
                "Enter your choice (1/2/3): ")
            if choice == '1':
                pass  # We'll overwrite the file
            elif choice == '2':
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                new_filename = f"{os.path.splitext(os.path.basename(file_path))[0]}_{timestamp}{os.path.splitext(file_path)[1]}"
                stash_file_path = os.path.join(stash_dir, new_filename)
            else:
                print("Operation cancelled.")
                return
        else:
            # If force is True, we'll overwrite the existing file
            pass

    shutil.move(file_path, stash_file_path)
    log_stash_action(file_path, stash_file_path)

    if verbosity != 'silent':
        print(f'Moved: {file_path} -> {stash_file_path}')
        if verbosity == 'verbose':
            print_report(file_path, stash_file_path, original_size, file_type, permissions, original_dir)


def print_report(original_path, stash_path, size, file_type, permissions, original_dir):
    current_time = time.ctime(os.path.getmtime(stash_path))
    creation_time = time.ctime(os.path.getctime(stash_path))
    stash_dir = os.path.dirname(stash_path)
    original_dir_size = get_dir_size(original_dir)
    stash_dir_size = get_dir_size(stash_dir)

    print('\n=== Stash Report ===')
    print(f'File: {original_path}')
    print(f'Stashed to: {stash_path}')
    print(f'Original Size: {humanize.naturalsize(size)}')
    print(f'File Type: {file_type if size > 0 else "N/A"}')
    print(f'Permissions: {permissions}')
    print(f'Created on: {creation_time}')
    print(f'Modified on: {current_time}')
    print(f'Original directory size: {humanize.naturalsize(original_dir_size)}')
    print(f'Stash directory size: {humanize.naturalsize(stash_dir_size)}')

    size_change = size
    print(f'Original directory size change: {humanize.naturalsize(size_change)}')
    if original_dir_size > 0:
        change_percentage = (size_change / original_dir_size) * 100
        print(f'Percentage change: {change_percentage:.2f}% decrease')

    size_increase = size
    print(f'Stash directory size increase: {humanize.naturalsize(size_increase)}')
    if stash_dir_size > 0:
        increase_percentage = (size_increase / stash_dir_size) * 100
        print(f'Percentage increase: {increase_percentage:.2f}%')

    if file_type.lower() in ['.txt', '.py', '.md', '.csv']:
        print('\nFile Preview:')
        try:
            with open(stash_path, 'r') as f:
                lines = f.readlines()
                print('Top 5 lines:')
                print(''.join(lines[:5]))
                print('...')
                print('Bottom 5 lines:')
                print(''.join(lines[-5:]))
        except UnicodeDecodeError:
            print("Unable to preview file: not a text file or uses unknown encoding.")

    print('\n=== Fun Fact for You: ===')
    print(randfacts.get_fact())

    print('\nTo undo this action:')
    print(f'stash -u {os.path.basename(stash_path)} -r {original_dir}')


def log_stash_action(original_path, stash_path):
    log_entry = {os.path.basename(stash_path): {'original': original_path, 'stashed': stash_path,
                                                'original_location': os.path.dirname(os.path.abspath(original_path))}}
    if os.path.exists(STASH_LOG):
        with open(STASH_LOG, 'r') as f:
            log = json.load(f)
    else:
        log = {}
    log.update(log_entry)
    with open(STASH_LOG, 'w') as f:
        json.dump(log, f, indent=2)


def undo_stash(file_name, restore_location):
    if not os.path.exists(STASH_LOG):
        print("No stash log found. Cannot undo.")
        return

    with open(STASH_LOG, 'r') as f:
        log = json.load(f)

    if file_name not in log:
        print(f"No stash record found for {file_name}")
        return

    stash_info = log[file_name]
    stashed_path = stash_info['stashed']
    original_path = os.path.join(restore_location, file_name)
    original_location = stash_info['original_location']

    if not os.path.exists(stashed_path):
        print(f"Stashed file {stashed_path} not found.")
        return

    if os.path.exists(original_path):
        choice = input(f"A file with the name '{file_name}' already exists in the restore location. Choose an option:\n"
                       "1. Overwrite existing file\n"
                       "2. Save with a modified name\n"
                       "3. Cancel operation\n"
                       "Enter your choice (1/2/3): ")
        if choice == '1':
            pass  # We'll overwrite the file
        elif choice == '2':
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            new_filename = f"{os.path.splitext(file_name)[0]}_{timestamp}{os.path.splitext(file_name)[1]}"
            original_path = os.path.join(restore_location, new_filename)
        else:
            print("Operation cancelled.")
            return

    shutil.move(stashed_path, original_path)
    print(f"Restored {file_name} to {original_path}")

    del log[file_name]
    with open(STASH_LOG, 'w') as f:
        json.dump(log, f, indent=2)


def main():
    working_dir = os.getcwd()
    
    parser = argparse.ArgumentParser(description=DESCRIPTION, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('file', type=str, help='File to stash or unstash')
    parser.add_argument('-s', '--stash_dir', type=str, default=STASH_DIR_DEFAULT, help='Directory to stash files')
    parser.add_argument('-d', '--dry_run', action='store_true', help='Perform a dry run without moving the file')
    parser.add_argument('-v', '--verbosity', choices=['silent', 'medium', 'verbose'], default=VERBOSITY_DEFAULT,
                        help='Output verbosity level')
    parser.add_argument('-u', '--undo', action='store_true', help='Undo a stash action')
    parser.add_argument('-r', '--restore_location', type=str, help='Location to restore the file when using --undo')
    parser.add_argument('-f', '--force', action='store_true', help='Force stashing without confirmation prompts')
    args = parser.parse_args()

    if args.undo:
        if not args.restore_location:
            print("Error: --restore_location is required when using --undo")
            return
        undo_stash(args.file, args.restore_location)
    else:
        file_path = os.path.join(working_dir, args.file)
        move_to_stash(file_path, args.stash_dir, args.dry_run, args.verbosity, args.force)


if __name__ == '__main__':
    main()
