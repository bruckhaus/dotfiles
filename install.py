#!/usr/bin/env python3

import os
import argparse
import shutil
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table

# Constants
DOTFILES = [
    '.bash_profile',
    '.bashrc',
    '.emacs',
    '.gitconfig',
    '.zshrc',
    '.config/wezterm',
    '.config/starship.toml'
]

SCRIPTS = [
    'stash.py',
    'unzippy.py'
]

console = Console()

def generate_wrapper_content(script_dir, script):
    return f"""#!/bin/bash
{script_dir}/venv/bin/python {script_dir}/{script} "$@"
"""

def get_wrapper_status(wrapper_path, wrapper_content):
    if os.path.exists(wrapper_path):
        with open(wrapper_path, 'r') as f:
            existing_content = f.read()
        return "Up to date" if existing_content.strip() == wrapper_content.strip() else "Needs update"
    return "New"

def create_wrapper_table(install_dir, script_dir, scripts):
    wrapper_table = Table(title="Wrapper Scripts")
    wrapper_table.add_column("Script", style="cyan", no_wrap=True)
    wrapper_table.add_column("Wrapper Path", style="magenta")
    wrapper_table.add_column("Status", style="green")

    for script in scripts:
        wrapper_name = script.replace('.py', '_wrapper.sh')
        wrapper_path = os.path.join(install_dir, wrapper_name)
        wrapper_content = generate_wrapper_content(script_dir, script)
        status = get_wrapper_status(wrapper_path, wrapper_content)
        wrapper_table.add_row(script, wrapper_path, status)

    return wrapper_table

def process_wrapper_script(install_dir, script_dir, script, dry_run):
    wrapper_name = script.replace('.py', '_wrapper.sh')
    wrapper_path = os.path.join(install_dir, wrapper_name)
    wrapper_content = generate_wrapper_content(script_dir, script)

    console.print(f"\n[bold]Processing wrapper script:[/bold] {wrapper_name}")
    console.print(f"[bold]Target path:[/bold] {wrapper_path}")

    if os.path.exists(wrapper_path):
        with open(wrapper_path, 'r') as f:
            existing_content = f.read()
        if existing_content.strip() == wrapper_content.strip():
            console.print("[green]✓ Wrapper script already up to date.[/green]")
            return
        console.print("[yellow]❗ Wrapper script needs updating.[/yellow]")

        if dry_run:
            console.print(f"[cyan]Dry run: Would update {wrapper_path}[/cyan]")
            return

        choice = console.input("Choose an option (1: Keep existing, 2: Replace with backup, 3: Replace without backup): ")

        if choice == '2':
            os.rename(wrapper_path, wrapper_path + '.bak')
            console.print("[green]Backed up existing wrapper.[/green]")
        elif choice == '3':
            console.print("[yellow]Replacing without backup.[/yellow]")
        else:
            console.print("[yellow]Keeping existing wrapper script.[/yellow]")
            return

    else:
        console.print("[yellow]❗ Wrapper script does not exist.[/yellow]")
        if dry_run:
            console.print(f"[cyan]Dry run: Would create wrapper script {wrapper_path}[/cyan]")
            return

    with open(wrapper_path, 'w') as f:
        f.write(wrapper_content)
    os.chmod(wrapper_path, 0o755)
    console.print("[green]Created/Updated wrapper script.[/green]")

def generate_wrapper_scripts(install_dir, script_dir, dry_run=False):
    console.print(create_wrapper_table(install_dir, script_dir, SCRIPTS))

    for script in SCRIPTS:
        process_wrapper_script(install_dir, script_dir, script, dry_run)
    
    return [os.path.join(install_dir, script.replace('.py', '_wrapper.sh')) for script in SCRIPTS]

def generate_aliases_table(content, aliases):
    table = Table(title="Aliases to be added/updated in .zshrc")
    table.add_column("Alias", style="cyan", no_wrap=True)
    table.add_column("Command", style="magenta")
    table.add_column("Status", style="green")

    for alias, command in aliases:
        status = "Update" if f"alias {alias}=" in content else "New"
        table.add_row(alias, command, status)

    return table

def update_zshrc_aliases(dry_run=False):
    here = os.path.dirname(os.path.realpath(__file__))
    zshrc_path = os.path.join(here, '.zshrc')
    temp_path = zshrc_path + '.temp'

    console.print(f"[bold]Updating aliases in {zshrc_path}[/bold]")

    start_marker = "# START dotfiles utilities"
    end_marker = "# END dotfiles utilities"
    other_aliases_marker = "# other aliases"
    aliases = [
        ('stash', '$HOME/.local/bin/stash_wrapper.sh $(pwd)'),
        ('unzippy', '$HOME/.local/bin/unzippy_wrapper.sh $(pwd)')
    ]

    try:
        with open(zshrc_path, 'r') as file:
            content = file.read()

        changes_needed = start_marker not in content or any(f"alias {alias}=" not in content for alias, _ in aliases)

        if changes_needed and not dry_run:
            backup_choice = console.input("Changes will be made to .zshrc. Create a backup? (y/n): ").lower()
            if backup_choice == 'y':
                if not create_backup(zshrc_path):
                    return

        console.print("[yellow]Existing dotfiles utilities section found. It will be updated.[/yellow]" if start_marker in content and end_marker in content else "[yellow]No existing dotfiles utilities section found. A new one will be added.[/yellow]")

        console.print(generate_aliases_table(content, aliases))

        if not dry_run and changes_needed:
            new_content = update_zshrc_content(content, aliases, start_marker, end_marker, other_aliases_marker)

            with open(temp_path, 'w') as outfile:
                outfile.write(new_content)

            # Atomic rename
            os.rename(temp_path, zshrc_path)
            console.print("[green]Updated .zshrc with new aliases.[/green]")
        elif dry_run:
            console.print("[cyan]Dry run: .zshrc would be updated with the above changes.[/cyan]")
        else:
            console.print("[green].zshrc is already up to date.[/green]")

    except IOError as e:
        console.print(f"[red]Error updating .zshrc: {e}[/red]")
        return

    if not dry_run and changes_needed:
        console.print("[green]Update complete.[/green]")
        console.print("[cyan]Please run 'source ~/.zshrc' to apply the changes to your current session.[/cyan]")

def create_backup(file_path):
    backup_path = file_path + '.bak'
    try:
        shutil.copy2(file_path, backup_path)
        console.print(f"[green]Backup created at {backup_path}[/green]")
    except IOError as e:
        console.print(f"[red]Error creating backup: {e}[/red]")
        return False
    return True

def install_files(specific_file=None, dry_run=False):
    here = os.path.dirname(os.path.realpath(__file__))
    install_dir = os.path.expanduser("~/.local/bin")

    # Ensure the installation directory exists
    os.makedirs(install_dir, exist_ok=True)

    console.print("\n[bold]1. Dotfiles Installation:[/bold]")
    
    for i in DOTFILES:
        if specific_file and i != specific_file:
            continue
        source_path = os.path.join(here, i)
        target_path = os.path.join(os.path.expanduser('~'), i)

        console.print(f"\n[bold]Processing file:[/bold] {i}")
        console.print(f"[bold]Source path:[/bold] {source_path}")
        console.print(f"[bold]Target path:[/bold] {target_path}")

        if os.path.exists(target_path) or os.path.islink(target_path):
            if os.path.islink(target_path) and os.readlink(target_path) == source_path:
                console.print("[green]✓ Already set up correctly.[/green]")
                continue
            else:
                console.print("[yellow]❗ Change needed.[/yellow]")
                if os.path.islink(target_path):
                    console.print(f"[yellow]Existing symlink points to:[/yellow] {os.readlink(target_path)}")
                else:
                    console.print("[yellow]Existing file is not a symlink.[/yellow]")

            if dry_run:
                console.print(f"[cyan]Dry run: Would replace {target_path} with symlink to {source_path}[/cyan]")
                continue

            console.print("[bold]Options:[/bold]")
            console.print("1. Keep existing")
            console.print("2. Replace with new symlink (with backup)")
            console.print("3. Replace with new symlink (without backup)")
            choice = console.input("Choose an option (1/2/3): ")

            if choice == '2':
                os.rename(target_path, target_path + '.bak')
                os.symlink(source_path, target_path)
                console.print(f"[green]Backed up {target_path} and created new symlink.[/green]")
            elif choice == '3':
                if os.path.islink(target_path):
                    os.unlink(target_path)
                else:
                    os.remove(target_path)
                os.symlink(source_path, target_path)
                console.print(f"[green]Replaced {target_path} with a new symlink.[/green]")
            else:
                console.print("[yellow]Keeping existing file/symlink.[/yellow]")
        else:
            console.print("[yellow]❗ File does not exist.[/yellow]")
            if dry_run:
                console.print(f"[cyan]Dry run: Would create symlink {target_path} -> {source_path}[/cyan]")
            else:
                os.symlink(source_path, target_path)
                console.print(f"[green]Created symlink for {target_path}.[/green]")

    # Create a table for dotfiles
    dotfiles_table = Table(title="Dotfiles to be installed/updated")
    dotfiles_table.add_column("File", style="cyan", no_wrap=True)
    dotfiles_table.add_column("Source", style="magenta")
    dotfiles_table.add_column("Target", style="green")
    dotfiles_table.add_column("Status", style="yellow")

    for i in DOTFILES:
        if specific_file and i != specific_file:
            continue
        source_path = os.path.join(here, i)
        target_path = os.path.join(os.path.expanduser('~'), i)
        
        if os.path.exists(target_path) or os.path.islink(target_path):
            if os.path.islink(target_path) and os.readlink(target_path) == source_path:
                status = "Up to date"
            else:
                status = "Needs update"
        else:
            status = "New"
        
        dotfiles_table.add_row(i, source_path, target_path, status)

    console.print(dotfiles_table)

    console.print("\n[bold]2. Wrapper Scripts Generation:[/bold]")
    generate_wrapper_scripts(install_dir, here, dry_run)

    console.print("\n[bold]3. Updating .zshrc Aliases:[/bold]")
    update_zshrc_aliases(dry_run)

    if dry_run:
        console.print('\n[yellow]Dry run complete. No changes were made.[/yellow]')
    else:
        console.print('\n[green]Installation complete.[/green]')
        console.print("[cyan]Please restart your terminal or run 'source ~/.zshrc' to use the new commands.[/cyan]")

def print_rich_help():
    help_text = Text()
    help_text.append("Dotfiles and Scripts Installer\n\n", style="bold underline")
    help_text.append("This script installs dotfiles and creates wrapper scripts for utility Python scripts.\n\n")
    
    help_text.append("Dotfiles to be installed:\n", style="bold")
    for dotfile in DOTFILES:
        help_text.append(f"  • {dotfile}\n", style="cyan")
    
    help_text.append("\nScripts to create wrappers for:\n", style="bold")
    for script in SCRIPTS:
        help_text.append(f"  • {script}\n", style="cyan")
    
    help_text.append("\nUsage:\n", style="bold")
    help_text.append("  python install.py [OPTIONS]\n\n")
    
    help_text.append("Options:\n", style="bold")
    help_text.append("  --dry-run    Show what would be done without making any changes\n", style="green")
    help_text.append("  --file FILE  Install only the specified file\n", style="green")
    help_text.append("  -h, --help   Show this help message and exit\n", style="green")

    console.print(Panel(help_text, title="Help", expand=False))

def main():
    parser = argparse.ArgumentParser(description='Install dotfiles', add_help=False)
    parser.add_argument('--dry-run', action='store_true', help='Display actions without making any changes')
    parser.add_argument('--file', type=str, help='Specify a file to install')
    parser.add_argument('-h', '--help', action='store_true', help='Show this help message and exit')
    args = parser.parse_args()

    if args.help:
        print_rich_help()
        return

    if args.dry_run:
        console.print("[yellow]Dry run mode activated. No changes will be made.[/yellow]")

    install_files(args.file, args.dry_run)

def update_zshrc_content(content, aliases, start_marker, end_marker, other_aliases_marker):
    new_content = []
    in_section = False
    section_added = False
    for line in content.splitlines():
        if line.strip() == start_marker:
            if not section_added:
                new_content.extend(generate_aliases_section(aliases, start_marker, end_marker))
                section_added = True
            in_section = True
        elif line.strip() == end_marker:
            in_section = False
        elif line.strip() == other_aliases_marker and not section_added:
            new_content.extend(generate_aliases_section(aliases, start_marker, end_marker))
            section_added = True
            new_content.append(line)
        elif not in_section:
            new_content.append(line)

    if not section_added:
        new_content.extend(generate_aliases_section(aliases, start_marker, end_marker))

    return '\n'.join(new_content)

def generate_aliases_section(aliases, start_marker, end_marker):
    section = [
        '',
        start_marker,
        *[f'alias {alias}="{command}"' for alias, command in aliases],
        end_marker,
        ''
    ]
    return section

if __name__ == '__main__':
    main()