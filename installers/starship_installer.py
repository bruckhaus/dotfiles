#!/usr/bin/env python3

import os
import shutil
import subprocess
import sys
from pathlib import Path

class StarshipInstaller:
    def __init__(self, console=None):
        """
        Initialize the Starship installer.
        
        Args:
            console: Optional Rich console for pretty output. If None, regular print statements are used.
        """
        self.console = console
        self.name = "starship"
        self.local_bin_path = os.path.expanduser("~/.local/bin")
        self.starship_path = os.path.join(self.local_bin_path, "starship")
        self.zshrc_path = os.path.expanduser("~/.zshrc")
        self.bashrc_path = os.path.expanduser("~/.bashrc")
        self.fish_config_path = os.path.expanduser("~/.config/fish/config.fish")
    
    def log(self, message, style=None):
        """Log a message using the console if available, otherwise use print."""
        if self.console:
            self.console.print(message, style=style)
        else:
            print(message)
    
    def is_installed(self):
        """Check if Starship is already installed."""
        return os.path.exists(self.starship_path) or shutil.which("starship") is not None
    
    def execute(self, dry_run=False):
        """
        Install Starship and configure shell integration.
        
        Args:
            dry_run: If True, only show what would be done without making changes.
            
        Returns:
            bool: True if changes were made, False otherwise.
        """
        if self.is_installed():
            self.log(f"Starship is already installed.", style="green")
            return self.ensure_proper_initialization(dry_run)
        
        if dry_run:
            self.log(f"Dry run: Would install Starship prompt", style="cyan")
            return False
        
        self.log(f"Installing Starship prompt...", style="yellow")
        
        # Create ~/.local/bin if it doesn't exist
        os.makedirs(self.local_bin_path, exist_ok=True)
        
        # Install Starship using the official installer script
        install_cmd = f'curl -sS https://starship.rs/install.sh | sh -s -- -y -b {self.local_bin_path}'
        result = os.system(install_cmd)
        
        if result != 0:
            self.log(f"Failed to install Starship.", style="red")
            return False
        
        # Add ~/.local/bin to PATH if needed
        self.ensure_path_in_profile()
        
        # Configure shell integration
        changes = self.ensure_proper_initialization(dry_run=False)
        
        self.log(f"Starship installed successfully!", style="green")
        return True
    
    def ensure_path_in_profile(self):
        """Ensure ~/.local/bin is in PATH by adding to ~/.profile if needed."""
        profile_path = os.path.expanduser("~/.profile")
        path_export = 'export PATH="$HOME/.local/bin:$PATH"'
        
        try:
            # Check if PATH export already exists
            if os.path.exists(profile_path):
                with open(profile_path, 'r') as f:
                    content = f.read()
                if path_export not in content and "$HOME/.local/bin" not in content:
                    with open(profile_path, 'a') as f:
                        f.write(f'\n# Add ~/.local/bin to PATH\n{path_export}\n')
            else:
                with open(profile_path, 'w') as f:
                    f.write(f'# Add ~/.local/bin to PATH\n{path_export}\n')
            
            # Also add to current environment
            os.environ['PATH'] = f"{self.local_bin_path}:{os.environ.get('PATH', '')}"
            
        except Exception as e:
            self.log(f"Warning: Could not update PATH in profile: {str(e)}", style="yellow")
    
    def ensure_proper_initialization(self, dry_run=False):
        """
        Ensure Starship is properly initialized in shell config files.
        
        Args:
            dry_run: If True, only show what would be done without making changes.
            
        Returns:
            bool: True if changes were made, False otherwise.
        """
        changes_made = False
        
        # Detect current shell
        current_shell = os.path.basename(os.environ.get('SHELL', ''))
        
        if current_shell == 'zsh' or os.path.exists(self.zshrc_path):
            changes_made |= self._update_zsh_config(dry_run)
        
        if current_shell == 'bash' or os.path.exists(self.bashrc_path):
            changes_made |= self._update_bash_config(dry_run)
        
        if current_shell == 'fish' or os.path.exists(os.path.dirname(self.fish_config_path)):
            changes_made |= self._update_fish_config(dry_run)
        
        return changes_made
    
    def _update_zsh_config(self, dry_run=False):
        """Update ZSH configuration to properly initialize Starship."""
        if not os.path.exists(self.zshrc_path):
            self.log(f"Warning: ~/.zshrc not found. Cannot configure Starship for ZSH.", style="yellow")
            return False
        
        with open(self.zshrc_path, 'r') as f:
            content = f.read()
        
        # Check for existing starship initialization
        has_starship_init = 'starship init zsh' in content
        has_conditional_check = 'if command -v starship' in content and 'starship init zsh' in content
        
        if has_starship_init and not has_conditional_check:
            # Need to replace with conditional initialization
            if dry_run:
                self.log(f"Dry run: Would update Starship initialization in ~/.zshrc", style="cyan")
                return True
            
            # Remove existing initialization
            new_content = []
            for line in content.splitlines():
                if 'starship init zsh' not in line:
                    new_content.append(line)
            
            # Add conditional initialization at the end
            new_content.extend([
                '',
                '# Initialize starship prompt',
                'if command -v starship &> /dev/null; then',
                '  eval "$(starship init zsh)"',
                'fi'
            ])
            
            with open(self.zshrc_path, 'w') as f:
                f.write('\n'.join(new_content))
            
            self.log(f"Updated Starship initialization in ~/.zshrc", style="green")
            return True
            
        elif not has_starship_init:
            # Need to add initialization
            if dry_run:
                self.log(f"Dry run: Would add Starship initialization to ~/.zshrc", style="cyan")
                return True
            
            with open(self.zshrc_path, 'a') as f:
                f.write('\n\n# Initialize starship prompt\n')
                f.write('if command -v starship &> /dev/null; then\n')
                f.write('  eval "$(starship init zsh)"\n')
                f.write('fi\n')
            
            self.log(f"Added Starship initialization to ~/.zshrc", style="green")
            return True
            
        else:
            # Already has conditional initialization
            self.log(f"Starship is already properly configured in ~/.zshrc", style="green")
            return False
    
    def _update_bash_config(self, dry_run=False):
        """Update Bash configuration to properly initialize Starship."""
        if not os.path.exists(self.bashrc_path):
            return False
        
        with open(self.bashrc_path, 'r') as f:
            content = f.read()
        
        # Check for existing starship initialization
        has_starship_init = 'starship init bash' in content
        has_conditional_check = 'if command -v starship' in content and 'starship init bash' in content
        
        if has_starship_init and not has_conditional_check:
            # Need to replace with conditional initialization
            if dry_run:
                self.log(f"Dry run: Would update Starship initialization in ~/.bashrc", style="cyan")
                return True
            
            # Remove existing initialization
            new_content = []
            for line in content.splitlines():
                if 'starship init bash' not in line:
                    new_content.append(line)
            
            # Add conditional initialization at the end
            new_content.extend([
                '',
                '# Initialize starship prompt',
                'if command -v starship &> /dev/null; then',
                '  eval "$(starship init bash)"',
                'fi'
            ])
            
            with open(self.bashrc_path, 'w') as f:
                f.write('\n'.join(new_content))
            
            self.log(f"Updated Starship initialization in ~/.bashrc", style="green")
            return True
            
        elif not has_starship_init:
            # Need to add initialization
            if dry_run:
                self.log(f"Dry run: Would add Starship initialization to ~/.bashrc", style="cyan")
                return True
            
            with open(self.bashrc_path, 'a') as f:
                f.write('\n\n# Initialize starship prompt\n')
                f.write('if command -v starship &> /dev/null; then\n')
                f.write('  eval "$(starship init bash)"\n')
                f.write('fi\n')
            
            self.log(f"Added Starship initialization to ~/.bashrc", style="green")
            return True
            
        else:
            # Already has conditional initialization
            self.log(f"Starship is already properly configured in ~/.bashrc", style="green")
            return False
    
    def _update_fish_config(self, dry_run=False):
        """Update Fish configuration to properly initialize Starship."""
        fish_config_dir = os.path.dirname(self.fish_config_path)
        
        # Create fish config directory if it doesn't exist
        if not os.path.exists(fish_config_dir):
            if dry_run:
                self.log(f"Dry run: Would create Fish config directory", style="cyan")
                return True
            os.makedirs(fish_config_dir, exist_ok=True)
        
        # Check if config file exists
        if not os.path.exists(self.fish_config_path):
            if dry_run:
                self.log(f"Dry run: Would create Fish config file with Starship initialization", style="cyan")
                return True
            
            with open(self.fish_config_path, 'w') as f:
                f.write('# Initialize starship prompt\n')
                f.write('if type -q starship\n')
                f.write('    starship init fish | source\n')
                f.write('end\n')
            
            self.log(f"Created Fish config with Starship initialization", style="green")
            return True
        
        # Check existing config
        with open(self.fish_config_path, 'r') as f:
            content = f.read()
        
        if 'starship init fish' not in content:
            if dry_run:
                self.log(f"Dry run: Would add Starship initialization to Fish config", style="cyan")
                return True
            
            with open(self.fish_config_path, 'a') as f:
                f.write('\n# Initialize starship prompt\n')
                f.write('if type -q starship\n')
                f.write('    starship init fish | source\n')
                f.write('end\n')
            
            self.log(f"Added Starship initialization to Fish config", style="green")
            return True
        
        self.log(f"Starship is already configured in Fish config", style="green")
        return False


def main():
    """Run the Starship installer as a standalone script."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Install and configure Starship prompt')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')
    args = parser.parse_args()
    
    installer = StarshipInstaller()
    
    if args.dry_run:
        print("Dry run mode activated. No changes will be made.")
    
    changes_made = installer.execute(dry_run=args.dry_run)
    
    if args.dry_run:
        print("Dry run complete. No changes were made.")
    elif changes_made:
        print("Starship installation and configuration complete.")
        print("Please restart your terminal or source your shell config file to use Starship.")
    else:
        print("No changes were necessary. Starship is already properly installed and configured.")


if __name__ == "__main__":
    main() 