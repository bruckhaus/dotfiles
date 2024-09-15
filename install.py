#!/usr/bin/env python3

import os
import argparse
import shutil
import subprocess


def supports_color():
    return os.isatty(1)


def colored_output(message, color, bold=False):
    if supports_color():
        colors = {'green': '\033[92m', 'red': '\033[91m', 'reset': '\033[0m'}
        bold_code = '\033[1m' if bold else ''
        return f"{bold_code}{colors[color]}{message}{colors['reset']}"
    else:
        return message


def generate_wrapper_script(install_dir, script_dir):
    wrapper_content = f"""#!/bin/bash
{script_dir}/venv/bin/python {script_dir}/stash.py "$@"
"""
    wrapper_path = os.path.join(install_dir, "stash_wrapper.sh")
    with open(wrapper_path, 'w') as f:
        f.write(wrapper_content)
    os.chmod(wrapper_path, 0o755)  # Make the wrapper executable
    return wrapper_path


def install_files(specific_file=None, dry_run=False):
    here = os.path.dirname(os.path.realpath(__file__))
    files = ['.bash_profile', '.bashrc', '.emacs', '.gitconfig', '.zshrc', '.config/wezterm', '.config/starship.toml']
    install_dir = os.path.expanduser("~/.local/bin")

    # Ensure the installation directory exists
    os.makedirs(install_dir, exist_ok=True)

    # Install the main files
    for i in files:
        if specific_file and i != specific_file:
            continue
        source_path = os.path.join(here, i)
        target_path = os.path.join(os.path.expanduser('~'), i)

        print(f"\nProcessing file: {i}")
        print(f"Source path: {source_path}")
        print(f"Target path: {target_path}")

        if os.path.exists(target_path) or os.path.islink(target_path):
            if os.path.islink(target_path) and os.readlink(target_path) == source_path:
                print(colored_output('✓ Already set up correctly.', 'green', bold=True))
                continue
            else:
                print(colored_output('❗ Change needed.', 'red'))
                if os.path.islink(target_path):
                    print(f'Existing symlink points to: {os.readlink(target_path)}')
                else:
                    print('Existing file is not a symlink.')

            if dry_run:
                print(f'Dry run: Would replace {target_path} with symlink to {source_path}')
                continue

            print('Options:')
            print('1. Keep existing')
            print('2. Replace with new symlink (with backup)')
            print('3. Replace with new symlink (without backup)')
            choice = input('Choose an option (1/2/3): ')

            if choice == '2':
                os.rename(target_path, target_path + '.bak')
                os.symlink(source_path, target_path)
                print(colored_output(f'Backed up {target_path} and created new symlink.', 'green'))
            elif choice == '3':
                if os.path.islink(target_path):
                    os.unlink(target_path)
                else:
                    os.remove(target_path)
                os.symlink(source_path, target_path)
                print(colored_output(f'Replaced {target_path} with a new symlink.', 'green'))
            else:
                print('Keeping existing file/symlink.')
        else:
            print(colored_output('❗ File does not exist.', 'red'))
            if dry_run:
                print(f'Dry run: Would create symlink {target_path} -> {source_path}')
            else:
                os.symlink(source_path, target_path)
                print(colored_output(f'Created symlink for {target_path}.', 'green'))

    # Generate and install the wrapper script
    wrapper_path = generate_wrapper_script(install_dir, here)
    print(f"\nGenerated wrapper script: {wrapper_path}")

    if dry_run:
        print('\nDry run complete. No changes were made.')
    else:
        print('\nInstallation complete.')
        print("Please restart your terminal or run 'source ~/.zshrc' to use the stash command.")


def main():
    parser = argparse.ArgumentParser(description='Install dotfiles')
    parser.add_argument('--dry-run', action='store_true', help='Display actions without making any changes')
    parser.add_argument('--file', type=str, help='Specify a file to install')
    args = parser.parse_args()

    if args.dry_run:
        print('Dry run mode activated. No changes will be made.')

    install_files(args.file, args.dry_run)


if __name__ == '__main__':
    main()
