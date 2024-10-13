#!/usr/bin/env python3

import os
import argparse
import shutil
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.theme import Theme

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

custom_theme = Theme({
    "info": "cyan",
    "warning": "yellow",
    "danger": "bold red",
    "success": "bold green",
    "file": "cyan",
    "prompt": "blue",
    "highlight": "magenta",
    "dry_run": "dim white",
})

console = Console(theme=custom_theme)

class WrapperScript:
    def __init__(self, script_name, install_dir, script_dir):
        self.script_name = script_name
        self.wrapper_name = script_name.replace('.py', '_wrapper.sh')
        self.install_dir = install_dir
        self.script_dir = script_dir
        self.wrapper_path = os.path.join(install_dir, self.wrapper_name)
        self.wrapper_content = self._generate_content()

    def _generate_content(self):
        return f"""#!/bin/bash
{self.script_dir}/venv/bin/python {self.script_dir}/{self.script_name} "$@"
"""

    def get_status(self):
        if os.path.exists(self.wrapper_path):
            with open(self.wrapper_path, 'r') as f:
                existing_content = f.read()
            return "Up to date" if existing_content.strip() == self.wrapper_content.strip() else "Needs update"
        return "New"

    def process(self, dry_run=False):
        console.print(f"\n[bold]Processing wrapper script:[/bold] {self.wrapper_name}")
        console.print(f"[bold]Target path:[/bold] {self.wrapper_path}")

        status = self.get_status()
        if status == "Up to date":
            console.print("[green]✓ Wrapper script already up to date.[/green]")
            return

        if status == "Needs update":
            console.print("[yellow]❗ Wrapper script needs updating.[/yellow]")
        else:
            console.print("[yellow]❗ Wrapper script does not exist.[/yellow]")

        if dry_run:
            console.print(f"[cyan]Dry run: Would {'update' if status == 'Needs update' else 'create'} {self.wrapper_path}[/cyan]")
            return

        if status == "Needs update":
            choice = console.input("Choose an option (1: Keep existing, 2: Replace with backup, 3: Replace without backup): ")
            if choice == '2':
                os.rename(self.wrapper_path, self.wrapper_path + '.bak')
                console.print("[green]Backed up existing wrapper.[/green]")
            elif choice == '3':
                console.print("[yellow]Replacing without backup.[/yellow]")
            else:
                console.print("[yellow]Keeping existing wrapper script.[/yellow]")
                return

        with open(self.wrapper_path, 'w') as f:
            f.write(self.wrapper_content)
        os.chmod(self.wrapper_path, 0o755)
        console.print("[green]Created/Updated wrapper script.[/green]")

def create_wrapper_table(wrappers):
    table = Table(title="Wrapper Scripts")
    table.add_column("Script", style="cyan", no_wrap=True)
    table.add_column("Wrapper Path", style="magenta")
    table.add_column("Status", style="green")

    for wrapper in wrappers:
        table.add_row(wrapper.script_name, wrapper.wrapper_path, wrapper.get_status())

    return table

def generate_wrapper_scripts(install_dir, script_dir, dry_run=False):
    wrappers = [WrapperScript(script, install_dir, script_dir) for script in SCRIPTS]
    
    wrapper_table = Table(title="Wrapper Scripts Status")
    wrapper_table.add_column("Script", style="cyan", no_wrap=True)
    wrapper_table.add_column("Status", style="green")

    wrappers_to_update = []

    for wrapper in wrappers:
        status = wrapper.get_status()
        wrapper_table.add_row(wrapper.script_name, f"[{'green' if status == 'Up to date' else 'yellow'}]{status}[/{'green' if status == 'Up to date' else 'yellow'}]")
        if status != "Up to date":
            wrappers_to_update.append(wrapper)

    console.print(wrapper_table)

    if wrappers_to_update:
        console.print("\n[bold]Wrapper scripts requiring updates:[/bold]")
        for wrapper in wrappers_to_update:
            console.print(f"\n[cyan]{wrapper.script_name}[/cyan]")
            console.print(f"Target path: {wrapper.wrapper_path}")
            
            if dry_run:
                console.print(f"[dim]Dry run: Would {'update' if wrapper.get_status() == 'Needs update' else 'create'} {wrapper.wrapper_path}[/dim]")
            else:
                wrapper.process()

    return [wrapper.wrapper_path for wrapper in wrappers]

def generate_aliases_table(content, aliases, changes_needed):
    table = Table(title="Aliases to be added/updated in .zshrc")
    table.add_column("Alias", style="cyan", no_wrap=True)
    table.add_column("Command", style="magenta")
    table.add_column("Status", style="green")

    for alias, command in aliases:
        if changes_needed:
            status = "[yellow]Update[/yellow]" if f"alias {alias}=" in content else "[yellow]New[/yellow]"
        else:
            status = "[green]Up to date[/green]"
        table.add_row(alias, command, status)

    return table

def get_update_choice(file_path):
    console.print("Options:", style="prompt")
    console.print("1. Keep existing (no change)")
    console.print("2. Update without backup")
    console.print("3. Update with backup")
    while True:
        choice = console.input("Choose an option (1/2/3): ")
        if choice in ['1', '2', '3']:
            return choice
        console.print("Invalid choice. Please enter 1, 2, or 3.", style="danger")

def perform_update(file_path, update_function, *args):
    choice = get_update_choice(file_path)
    if choice == '1':
        console.print("Keeping existing file. No changes made.", style="info")
        return False
    elif choice == '3':
        if not create_backup(file_path):
            return False
    
    update_function(file_path, *args)
    console.print("File updated successfully.", style="success")
    return True

def install_files(specific_file=None, dry_run=False):
    here = os.path.dirname(os.path.realpath(__file__))
    install_dir = os.path.expanduser("~/.local/bin")

    # Ensure the installation directory exists
    os.makedirs(install_dir, exist_ok=True)

    dotfiles_table = Table(title="Dotfiles Status")
    dotfiles_table.add_column("File", style="cyan", no_wrap=True)
    dotfiles_table.add_column("Status", style="green")
    
    files_to_update = []

    for i in DOTFILES:
        if specific_file and i != specific_file:
            continue
        source_path = os.path.join(here, i)
        target_path = os.path.join(os.path.expanduser('~'), i)

        if os.path.exists(target_path) or os.path.islink(target_path):
            if os.path.islink(target_path) and os.readlink(target_path) == source_path:
                status = "[green]Up to date[/green]"
            else:
                status = "[yellow]Needs update[/yellow]"
                files_to_update.append((i, source_path, target_path))
        else:
            status = "[yellow]New[/yellow]"
            files_to_update.append((i, source_path, target_path))

        dotfiles_table.add_row(i, status)

    console.print(dotfiles_table)

    files_changed = []

    for file, source, target in files_to_update:
        console.print(f"\n[cyan]{file}[/cyan]")
        console.print(f"Source: {source}")
        console.print(f"Target: {target}")
        
        if dry_run:
            console.print(f"[dim]Dry run: Would update {target}[/dim]")
        else:
            if perform_update(target, os.symlink, source, target):
                files_changed.append(file)

    return files_changed

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

    here = os.path.dirname(os.path.realpath(__file__))
    install_dir = os.path.expanduser("~/.local/bin")

    changes_made = False
    zshrc_changed = False

    console.print("\n[bold]1. Dotfiles Symlinks:[/bold]")
    dotfiles_changed = install_files(args.file, args.dry_run)
    changes_made |= bool(dotfiles_changed)
    zshrc_changed |= '.zshrc' in dotfiles_changed

    console.print("\n[bold]2. Wrapper Scripts Generation:[/bold]")
    changes_made |= bool(generate_wrapper_scripts(install_dir, here, args.dry_run))

    console.print("\n[bold]3. Updating .zshrc Aliases:[/bold]")
    aliases_changed = update_zshrc_aliases(args.dry_run)
    changes_made |= aliases_changed
    zshrc_changed |= aliases_changed

    if args.dry_run:
        console.print('\n[yellow]Dry run complete. No changes were made.[/yellow]')
    elif changes_made:
        console.print('\n[green]Installation complete.[/green]')
        if zshrc_changed:
            console.print("[yellow]Please restart your terminal or run 'source ~/.zshrc' to use the new commands.[/yellow]")
    else:
        console.print('\n[green]No changes were necessary. Everything is up to date.[/green]')

def update_zshrc_content(content, new_section, start_marker, end_marker):
    start_index = content.find(start_marker)
    end_index = content.find(end_marker, start_index)
    
    if start_index != -1 and end_index != -1:
        # Replace existing section
        return content[:start_index] + new_section + content[end_index + len(end_marker):]
    else:
        # Add new section at the end
        return content.rstrip() + '\n\n' + new_section + '\n'

def generate_aliases_section(aliases, start_marker, end_marker):
    section = [
        start_marker,
        *[f'alias {alias}="{command}"' for alias, command in aliases],
        end_marker
    ]
    return '\n'.join(section)

def update_zshrc_aliases(dry_run=False):
    here = os.path.dirname(os.path.realpath(__file__))
    zshrc_path = os.path.join(here, '.zshrc')

    start_marker = "# START dotfiles utilities"
    end_marker = "# END dotfiles utilities"
    aliases = [
        ('stash', '$HOME/.local/bin/stash_wrapper.sh $(pwd)'),
        ('unzippy', '$HOME/.local/bin/unzippy_wrapper.sh $(pwd)')
    ]

    try:
        with open(zshrc_path, 'r') as file:
            content = file.read()

        existing_section = extract_existing_section(content, start_marker, end_marker)
        new_section = generate_aliases_section(aliases, start_marker, end_marker)

        changes_needed = existing_section != new_section

        console.print(generate_aliases_table(content, aliases, changes_needed))

        if changes_needed:
            console.print("\n[bold]Aliases requiring updates:[/bold]")
            console.print(f"[cyan]Existing section:[/cyan]\n{existing_section}")
            console.print(f"[cyan]New section:[/cyan]\n{new_section}")
            
            if dry_run:
                console.print("[dim]Dry run: Would update .zshrc with the above changes[/dim]")
            else:
                def update_func(file_path, content, new_section, start_marker, end_marker):
                    new_content = update_zshrc_content(content, new_section, start_marker, end_marker)
                    with open(file_path, 'w') as outfile:
                        outfile.write(new_content)
                
                return perform_update(zshrc_path, update_func, content, new_section, start_marker, end_marker)
        return changes_needed

    except IOError as e:
        console.print(f"[red]Error updating .zshrc: {e}[/red]")
        return False

def extract_existing_section(content, start_marker, end_marker):
    start_index = content.find(start_marker)
    end_index = content.find(end_marker, start_index)
    if start_index != -1 and end_index != -1:
        return content[start_index:end_index + len(end_marker)].strip()
    return ""

def create_backup(file_path):
    backup_path = file_path + '.bak'
    try:
        shutil.copy2(file_path, backup_path)
        console.print(f"Backup created at {backup_path}", style="success")
    except IOError as e:
        console.print(f"Error creating backup: {e}", style="danger")
        return False
    return True

if __name__ == '__main__':
    main()