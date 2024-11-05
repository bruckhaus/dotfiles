#!/bin/bash

# Check if zsh is installed
if ! command -v zsh >/dev/null 2>&1; then
    echo "zsh is not installed. Installing zsh..."
    if command -v brew >/dev/null 2>&1; then
        brew install zsh
    elif command -v apt-get >/dev/null 2>&1; then
        sudo apt-get update && sudo apt-get install -y zsh
    elif command -v dnf >/dev/null 2>&1; then
        sudo dnf install -y zsh
    elif command -v yum >/dev/null 2>&1; then
        sudo yum install -y zsh
    else
        echo "Error: Could not install zsh. Please install zsh manually."
        exit 1
    fi
fi

# Check if Oh My Zsh is already installed
if [ -d "$HOME/.oh-my-zsh" ]; then
    echo "Oh My Zsh is already installed in $HOME/.oh-my-zsh"
    read -p "Do you want to reinstall? This will remove the existing installation (y/N): " confirm
    if [[ "$confirm" =~ ^[Yy]$ ]]; then
        echo "Removing existing Oh My Zsh installation..."
        rm -rf "$HOME/.oh-my-zsh"
    else
        echo "Keeping existing Oh My Zsh installation."
    fi
fi

# Only install Oh My Zsh if it doesn't exist or user confirmed reinstall
if [ ! -d "$HOME/.oh-my-zsh" ]; then
    echo "Installing Oh My Zsh..."
    sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended
fi

# Install plugins if they don't exist
install_plugin() {
    local plugin_name=$1
    local plugin_url=$2
    local plugin_dir="$HOME/.oh-my-zsh/plugins/$plugin_name"
    
    if [ -d "$plugin_dir" ]; then
        echo "Plugin $plugin_name is already installed"
        read -p "Do you want to reinstall? This will remove the existing plugin (y/N): " confirm
        if [[ "$confirm" =~ ^[Yy]$ ]]; then
            echo "Removing existing $plugin_name plugin..."
            rm -rf "$plugin_dir"
            echo "Installing $plugin_name..."
            git clone "$plugin_url" "$plugin_dir"
        else
            echo "Keeping existing $plugin_name plugin."
        fi
    else
        echo "Installing $plugin_name..."
        git clone "$plugin_url" "$plugin_dir"
    fi
}

install_plugin "zsh-autosuggestions" "https://github.com/zsh-users/zsh-autosuggestions.git"
install_plugin "zsh-syntax-highlighting" "https://github.com/zsh-syntax-highlighting/zsh-syntax-highlighting.git"

# Make zsh the default shell if it isn't already
if [ "$SHELL" != "$(which zsh)" ]; then
    echo "Changing default shell to zsh..."
    chsh -s "$(which zsh)"
fi

echo "Setup complete! Please restart your terminal to start using zsh with Oh My Zsh."
