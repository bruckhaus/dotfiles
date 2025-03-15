#!/usr/bin/env python3

import os
import shutil
import subprocess
import sys
from pathlib import Path
import re

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
        self.fonts_dir = os.path.expanduser("~/.local/share/fonts")
    
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
            changes = self.ensure_proper_initialization(dry_run)
            # Install Nerd Font if needed
            changes |= self.install_nerd_font(dry_run)
            # Ask about icon rendering and offer no-nerd-font preset if needed
            changes |= self.check_icon_rendering(dry_run)
            return changes
        
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
        
        # Install Nerd Font
        changes |= self.install_nerd_font(dry_run=False)
        
        # Ask about icon rendering and offer no-nerd-font preset if needed
        changes |= self.check_icon_rendering(dry_run=False)
        
        self.log(f"Starship installed successfully!", style="green")
        return True
    
    def install_nerd_font(self, dry_run=False):
        """
        Install a Nerd Font to fix missing icons in Starship prompt.
        
        Args:
            dry_run: If True, only show what would be done without making changes.
            
        Returns:
            bool: True if changes were made, False otherwise.
        """
        # Check if a Nerd Font is already installed
        if self.is_nerd_font_installed():
            self.log("A Nerd Font is already installed on your system.", style="green")
            return False
            
        # Check if we're on Debian/Ubuntu
        is_debian = False
        try:
            with open('/etc/os-release', 'r') as f:
                content = f.read().lower()
                is_debian = 'debian' in content or 'ubuntu' in content
        except FileNotFoundError:
            pass
        
        self.log("\n[bold]Checking for Nerd Font:[/bold] Required for Starship icons to display correctly.", style="yellow")
        
        # Check if we're on macOS
        is_macos = sys.platform == 'darwin'
        
        # Try to install via homebrew if on macOS
        if is_macos:
            self.log("Detected macOS system. Checking for Homebrew...", style="cyan")
            
            if dry_run:
                self.log("Dry run: Would attempt to install Nerd Fonts via Homebrew", style="cyan")
                return True
            
            try:
                # Check if homebrew is installed
                result = subprocess.run(
                    ["which", "brew"], 
                    capture_output=True, 
                    text=True
                )
                
                if result.returncode == 0:
                    self.log("Found Homebrew. Installing JetBrainsMono Nerd Font...", style="cyan")
                    
                    # Install the font using homebrew
                    subprocess.run(
                        ["brew", "tap", "homebrew/cask-fonts"],
                        check=True
                    )
                    
                    subprocess.run(
                        ["brew", "install", "--cask", "font-jetbrains-mono-nerd-font"],
                        check=True
                    )
                    
                    self.log("Successfully installed JetBrainsMono Nerd Font via Homebrew.", style="green")
                    self.log("Please configure your terminal to use 'JetBrainsMono Nerd Font' in the terminal preferences.", style="yellow")
                    return True
            except (subprocess.SubprocessError, FileNotFoundError):
                self.log("Could not install via Homebrew. Falling back to manual installation.", style="yellow")
        
        # Try to install via apt if on Debian/Ubuntu
        elif is_debian:
            self.log("Detected Debian/Ubuntu system. Checking for Nerd Font packages...", style="cyan")
            
            if dry_run:
                self.log("Dry run: Would attempt to install Nerd Fonts via apt", style="cyan")
                return True
            
            try:
                # Check if the package is available
                result = subprocess.run(
                    ["apt-cache", "search", "fonts-firacode-nerd"], 
                    capture_output=True, 
                    text=True
                )
                
                if "fonts-firacode-nerd" in result.stdout:
                    self.log("Found Nerd Font package. Installing via apt...", style="cyan")
                    
                    # Install the package
                    subprocess.run(
                        ["sudo", "apt", "install", "-y", "fonts-firacode-nerd"],
                        check=True
                    )
                    
                    self.log("Successfully installed FiraCode Nerd Font via apt.", style="green")
                    self.log("Please configure your terminal to use 'FiraCode Nerd Font' in the terminal preferences.", style="yellow")
                    return True
            except (subprocess.SubprocessError, FileNotFoundError):
                self.log("Could not install via apt. Falling back to manual installation.", style="yellow")
        
        # Manual installation
        self.log("Installing JetBrainsMono Nerd Font manually...", style="cyan")
        
        if dry_run:
            self.log("Dry run: Would manually install JetBrainsMono Nerd Font", style="cyan")
            return True
        
        try:
            # Create fonts directory
            os.makedirs(self.fonts_dir, exist_ok=True)
            
            # Updated URL for JetBrainsMono Nerd Font
            font_url = "https://github.com/ryanoasis/nerd-fonts/releases/download/v3.0.2/JetBrainsMono.zip"
            zip_path = os.path.join(self.fonts_dir, "JetBrainsMono.zip")
            
            self.log(f"Downloading JetBrainsMono Nerd Font to {zip_path}...", style="cyan")
            
            # Use curl to download the font zip
            download_cmd = f'curl -fLo "{zip_path}" "{font_url}"'
            result = os.system(download_cmd)
            
            if result != 0:
                self.log("Failed to download font. Trying alternative method...", style="yellow")
                
                # Try an alternative font (Hack Nerd Font)
                font_url = "https://github.com/ryanoasis/nerd-fonts/releases/download/v3.0.2/Hack.zip"
                zip_path = os.path.join(self.fonts_dir, "Hack.zip")
                
                download_cmd = f'curl -fLo "{zip_path}" "{font_url}"'
                result = os.system(download_cmd)
                
                if result != 0:
                    self.log("Failed to download font. Please install a Nerd Font manually.", style="red")
                    self.log_manual_font_instructions()
                    return False
                
                self.log("Successfully downloaded Hack Nerd Font.", style="green")
            else:
                self.log("Successfully downloaded JetBrainsMono Nerd Font.", style="green")
            
            # Extract the zip file
            self.log("Extracting font files...", style="cyan")
            
            # Check if unzip is available
            unzip_available = shutil.which("unzip") is not None
            
            if unzip_available:
                extract_cmd = f'unzip -o "{zip_path}" -d "{self.fonts_dir}"'
                os.system(extract_cmd)
            else:
                # Try using Python's zipfile module
                import zipfile
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(self.fonts_dir)
            
            # Update font cache if on Linux
            if not is_macos and shutil.which("fc-cache") is not None:
                self.log("Updating font cache...", style="cyan")
                os.system("fc-cache -f -v")
            
            # Clean up zip file
            if os.path.exists(zip_path):
                os.remove(zip_path)
            
            font_name = "JetBrainsMono Nerd Font" if "JetBrains" in zip_path else "Hack Nerd Font"
            self.log(f"Successfully installed {font_name}.", style="green")
            self.log(f"Please configure your terminal to use '{font_name}' in the terminal preferences.", style="yellow")
            
            # Also try to install emoji fonts on Debian/Ubuntu
            if is_debian:
                try:
                    self.log("Installing additional emoji fonts for better symbol support...", style="cyan")
                    subprocess.run(
                        ["sudo", "apt", "install", "-y", "fonts-noto-color-emoji"],
                        check=True
                    )
                    self.log("Successfully installed additional emoji fonts.", style="green")
                except:
                    self.log("Could not install additional emoji fonts. This is optional.", style="yellow")
            
            return True
            
        except Exception as e:
            self.log(f"Error installing Nerd Font: {str(e)}", style="red")
            self.log_manual_font_instructions()
            return False
    
    def is_nerd_font_installed(self):
        """Check if a Nerd Font is already installed on the system."""
        # First, check if we already have Nerd Font files in our fonts directory
        if os.path.exists(self.fonts_dir):
            font_files = os.listdir(self.fonts_dir)
            nerd_font_indicators = ["nerdfont", "nerd font", "jetbrainsmono", "hack"]
            
            for file in font_files:
                file_lower = file.lower()
                if file_lower.endswith(".ttf") or file_lower.endswith(".otf"):
                    for indicator in nerd_font_indicators:
                        if indicator in file_lower:
                            self.log(f"Found Nerd Font file in local fonts directory: {file}", style="green")
                            return True
        
        is_macos = sys.platform == 'darwin'
        
        # On macOS, check using the system font registry
        if is_macos:
            try:
                # Check for JetBrainsMono Nerd Font files in the user's Library
                user_fonts_dir = os.path.expanduser("~/Library/Fonts")
                if os.path.exists(user_fonts_dir):
                    for file in os.listdir(user_fonts_dir):
                        file_lower = file.lower()
                        if ("nerd" in file_lower or "jetbrains" in file_lower) and (file_lower.endswith(".ttf") or file_lower.endswith(".otf")):
                            self.log(f"Found Nerd Font in user's Library: {file}", style="green")
                            return True
                
                # Check using Homebrew if available
                try:
                    brew_result = subprocess.run(
                        ["brew", "list", "--cask"], 
                        capture_output=True, 
                        text=True
                    )
                    
                    if "font-jetbrains-mono-nerd-font" in brew_result.stdout:
                        self.log("JetBrainsMono Nerd Font is installed via Homebrew", style="green")
                        return True
                except:
                    pass
                
                # Use the macOS font registry to check for installed fonts
                try:
                    result = subprocess.run(
                        ["system_profiler", "SPFontsDataType"], 
                        capture_output=True, 
                        text=True
                    )
                    
                    font_list = result.stdout
                    
                    # Check for common Nerd Fonts
                    nerd_font_patterns = [
                        "JetBrainsMono Nerd Font",
                        "Hack Nerd Font",
                        "FiraCode Nerd Font",
                        "Meslo LG.*Nerd Font",
                        ".*Nerd Font"  # Any Nerd Font
                    ]
                    
                    for pattern in nerd_font_patterns:
                        if re.search(pattern, font_list, re.IGNORECASE):
                            self.log(f"Found Nerd Font matching pattern '{pattern}' in system fonts", style="green")
                            return True
                except:
                    # If system_profiler fails, continue with other checks
                    pass
                    
                return False
            except:
                # If the check fails, fall back to checking the fonts directory
                pass
        
        # On Linux, check using fc-list
        elif shutil.which("fc-list") is not None:
            try:
                # Check for common Nerd Fonts
                result = subprocess.run(
                    ["fc-list"], 
                    capture_output=True, 
                    text=True
                )
                
                font_list = result.stdout.lower()
                
                # Check for common Nerd Font names
                nerd_font_indicators = [
                    "nerd font",
                    "nerdfont",
                    "jetbrainsmono nf",
                    "hack nf",
                    "firacode nf"
                ]
                
                for indicator in nerd_font_indicators:
                    if indicator in font_list:
                        self.log(f"Found Nerd Font containing '{indicator}' in system fonts", style="green")
                        return True
                
                return False
            except:
                # If the check fails, fall back to checking the fonts directory
                pass
        
        # If all checks fail, assume no Nerd Font is installed
        return False
    
    def log_manual_font_instructions(self):
        """Log instructions for manual Nerd Font installation."""
        self.log("\nTo manually install a Nerd Font:", style="yellow")
        self.log("1. Download a Nerd Font from https://www.nerdfonts.com/font-downloads", style="cyan")
        self.log("2. Install the font on your system", style="cyan")
        self.log("3. Configure your terminal to use the Nerd Font", style="cyan")
        self.log("   (Usually in your terminal's preferences/settings)", style="cyan")
        self.log("\nRecommended fonts: JetBrainsMono Nerd Font, Hack Nerd Font, or FiraCode Nerd Font", style="green")
        
        self.log("\nFor macOS users:", style="yellow")
        self.log("brew tap homebrew/cask-fonts", style="cyan")
        self.log("brew install --cask font-jetbrains-mono-nerd-font", style="cyan")
        
        self.log("\nFor Linux users:", style="yellow")
        self.log("mkdir -p ~/.local/share/fonts", style="cyan")
        self.log("cd ~/.local/share/fonts", style="cyan")
        self.log('curl -fLo "JetBrainsMono.zip" https://github.com/ryanoasis/nerd-fonts/releases/download/v3.0.2/JetBrainsMono.zip', style="cyan")
        self.log("unzip JetBrainsMono.zip", style="cyan")
        self.log("fc-cache -f -v", style="cyan")
    
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
        
        # New improved initialization
        improved_init = [
            '',
            '# Initialize starship prompt',
            'if command -v starship &> /dev/null; then',
            '  eval "$(starship init zsh)"',
            'fi'
        ]
        
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
            
            # Add improved initialization at the end
            new_content.extend(improved_init)
            
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
                f.write('\n'.join(improved_init))
            
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
    
    def check_icon_rendering(self, dry_run=False):
        """
        Ask the user if icons are rendering correctly and offer the no-nerd-font preset if needed.
        
        Args:
            dry_run: If True, only show what would be done without making changes.
            
        Returns:
            bool: True if changes were made, False otherwise.
        """
        # Skip in dry run mode
        if dry_run:
            self.log("Dry run: Would check if icons are rendering correctly", style="cyan")
            return False
        
        self.log("\n[bold]Icon Rendering Check:[/bold]", style="yellow")
        self.log("After restarting your terminal, you should see icons in your prompt.", style="yellow")
        self.log("If icons don't display correctly, you can use the no-nerd-font preset.", style="yellow")
        
        # Ask the user if they want to apply the no-nerd-font preset now
        response = input("\nDo you want to apply the no-nerd-font preset now? (y/n): ").strip().lower()
        
        if response == 'y' or response == 'yes':
            return self.apply_no_nerd_font_preset(dry_run)
        else:
            self.log("\nIf you encounter icon rendering issues later, you can run:", style="yellow")
            self.log("starship preset no-nerd-font -o ~/.config/starship.toml", style="cyan")
            return False
    
    def apply_no_nerd_font_preset(self, dry_run=False):
        """
        Apply the no-nerd-font preset to the Starship configuration.
        
        Args:
            dry_run: If True, only show what would be done without making changes.
            
        Returns:
            bool: True if changes were made, False otherwise.
        """
        if dry_run:
            self.log("Dry run: Would apply no-nerd-font preset to Starship configuration", style="cyan")
            return True
        
        self.log("Applying no-nerd-font preset to Starship configuration...", style="yellow")
        
        try:
            # Check if starship is in PATH
            if not shutil.which("starship"):
                # Add ~/.local/bin to PATH temporarily if needed
                if os.path.exists(self.starship_path):
                    os.environ['PATH'] = f"{self.local_bin_path}:{os.environ.get('PATH', '')}"
            
            # Apply the no-nerd-font preset
            result = subprocess.run(
                ["starship", "preset", "no-nerd-font", "-o", os.path.expanduser("~/.config/starship.toml")],
                check=True
            )
            
            self.log("Successfully applied no-nerd-font preset.", style="green")
            self.log("Your Starship prompt will now use standard Unicode symbols instead of Nerd Font icons.", style="green")
            return True
            
        except subprocess.SubprocessError as e:
            self.log(f"Error applying no-nerd-font preset: {str(e)}", style="red")
            self.log("You can manually apply the preset with:", style="yellow")
            self.log("starship preset no-nerd-font -o ~/.config/starship.toml", style="cyan")
            return False


def main():
    """Run the Starship installer as a standalone script."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Install and configure Starship prompt')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')
    parser.add_argument('--install-font', action='store_true', help='Install a Nerd Font for Starship icons')
    args = parser.parse_args()
    
    installer = StarshipInstaller()
    
    if args.dry_run:
        print("Dry run mode activated. No changes will be made.")
    
    if args.install_font:
        installer.install_nerd_font(dry_run=args.dry_run)
        return
    
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