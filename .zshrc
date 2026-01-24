#!/bin/sh

# ZSH Options
# change directory without typing "cd"
setopt AUTO_CD
# can use "#" as comment:
unsetopt EXTENDED_GLOB
# Completion settings
zstyle ':completion:*' matcher-list 'm:{a-zA-Z}={A-Za-z}' 'r:|[._-]=* r:|=*' 'l:|=* r:|=*'
setopt MENU_COMPLETE
DISABLE_UPDATE_PROMPT=true
ZSH=$HOME/.oh-my-zsh
# Plugin configuration
plugins=(
    git
    zsh-syntax-highlighting
    zsh-autosuggestions
)
# Disable underline
(( ${+ZSH_HIGHLIGHT_STYLES} )) || typeset -A ZSH_HIGHLIGHT_STYLES
ZSH_HIGHLIGHT_STYLES[path]=none
ZSH_HIGHLIGHT_STYLES[path_prefix]=none
# no theme: we are using starship
ZSH_THEME=""
source $ZSH/oh-my-zsh.sh
# Starship prompt (after sourcing oh-my-zsh.sh)

# git:
git_push_preview() {
  local dotfiles_root="${DOTFILES_REPO:-$HOME/dev/dotfiles}"
  local helper="$dotfiles_root/scripts/git_push_preview.py"

  if [[ ! -f "$helper" ]]; then
    echo "git_push_preview helper not found at $helper" >&2
    return 1
  fi

  python3 "$helper" "$@"
}

git_go() {
  local dotfiles_root="${DOTFILES_REPO:-$HOME/dev/dotfiles}"
  local helper="$dotfiles_root/scripts/git_go.py"

  if [[ ! -f "$helper" ]]; then
    echo "git_go helper not found at $helper" >&2
    return 1
  fi

  local output
  output=$(python3 "$helper" "$@")
  local exit_code=$?

  if [[ $exit_code -ne 0 ]]; then
    [[ -n "$output" ]] && printf "%s\n" "$output"
    return $exit_code
  fi

  if [[ -d "$output" ]]; then
    cd "$output" || return $?
    return 0
  fi

  [[ -n "$output" ]] && printf "%s\n" "$output"
}

alias gs="git status"
alias glm='git --no-pager log origin/main..HEAD --pretty=oneline'
alias gnp='git --no-pager log --pretty=oneline origin/`gbn`..`gbn`'
alias gcon='git shortlog -s -n --no-merges'
alias gbn='git rev-parse --abbrev-ref HEAD'
alias gpom="git pull origin main"
alias gpod="git pull origin develop"
alias gb="git branch"
alias gco="git checkout"
alias gd="git diff"
alias gdp="GIT_PAGER=less git diff --color"
alias gdd='git diff origin/main..HEAD'
alias gddc="git --no-pager diff --cached"
alias gt='git branch -u $(git remote)/$(git rev-parse --abbrev-ref HEAD)'
alias pull="git pull"
alias push="git push"
alias pusht='git push --set-upstream $(git remote) $(git rev-parse --abbrev-ref HEAD)'
alias gu='git reset --soft HEAD\^'
alias ga="git add"
alias gc="git commit"
alias gcm="git add . && git commit -m"
alias gan="git add . -n"
alias gl="git log origin/main..HEAD"
alias gpp='git_push_preview'
alias gas="gh auth status"
alias gauth="gh auth switch --user"
alias gg='git_go'
alias gitgo='git_go'

# START dotfiles utilities
alias stash="$HOME/.local/bin/stash_wrapper.sh"
alias unzippy="$HOME/.local/bin/unzippy_wrapper.sh"
alias pr="function _pr() { perplexity_rag "$*"; }; _pr"
alias pn="function _pn() { perplexity ask --no-save-history "$*"; }; _pn"
alias pk="function _pk() { perplexity ask-notes "$*"; }; _pk"
alias pplxc="perplexity chat"
# END dotfiles utilities

# Common ls aliases
alias ls="ls --color=auto"
alias ll='ls -lah'
alias llt='ls -laht'
alias la='ls -lAh'
alias l='ls -lah'
alias lls='ls -lSh'

# python:
alias python=python3
alias ptc="pytest --color=yes"
alias ptest='python -m unittest discover'
alias pint='pytest -v -m "integration"'
alias punt='pytest -v -m "not integration"'
export PYTHONPATH=.:$PYTHONPATH
unalias venv 2>/dev/null

venv() {
  # Define color codes for output
  GREEN='\033[0;32m'
  YELLOW='\033[0;33m'
  NC='\033[0m' # No color

  # Check if a virtual environment is already active
  if [[ -n "$VIRTUAL_ENV" ]]; then
    echo -e "${YELLOW}venv already active at: $VIRTUAL_ENV${NC}"
  else
    # Check if the venv directory exists
    if [[ -d ".venv/bin" ]]; then
      # Activate the virtual environment
      source .venv/bin/activate
      echo "No active venv found..."
      echo -e "${GREEN}venv activated${NC}"
      echo "venv directory: $VIRTUAL_ENV"
    else
      echo "Error: .venv directory not found"
    fi
  fi
}

# other aliases:
alias less='less -R'
alias ccat='pygmentize -g'

# path:
# PATH organization: most specific/important paths first, system paths last
# Using prepending style consistently for correct priority order

# Start with system base paths (will end up at the end of PATH)
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

# Homebrew and package manager paths
export PATH="/opt/homebrew/opt/node@18/bin:$PATH"  # ARM64 Node.js
export PATH="/opt/homebrew/bin:$PATH"
export PATH="/usr/local/git/bin:$PATH"

# Programming language specific paths
export PATH="/Library/Frameworks/Python.framework/Versions/3.11/bin:$PATH"

# User specific paths and tools
export PATH="$HOME/.local/bin:$PATH"
export PATH="$HOME/google-cloud-sdk/bin:$PATH"

# source local profile (company environment variables, etc.)
export LOCAL_PROFILE=${HOME}/.local_profile.sh
[[ -r "${LOCAL_PROFILE}" ]] && source "${LOCAL_PROFILE}"

export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  # This loads nvm
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"  # This loads nvm bash_completion

export NVM_NODEJS_ORG_MIRROR=https://nodejs.org/download/release/
export NVM_ARCH=arm64

# START dotfiles utilities
alias stash="$HOME/.local/bin/stash_wrapper.sh"
alias unzippy="$HOME/.local/bin/unzippy_wrapper.sh"
alias pr="function _pr() { perplexity_rag "$*"; }; _pr"
alias pn="function _pn() { perplexity ask --no-save-history "$*"; }; _pn"
alias pk="function _pk() { perplexity ask-notes "$*"; }; _pk"
alias pplxc="perplexity chat"
# END dotfiles utilities

# Initialize starship prompt
if command -v starship &> /dev/null; then
  eval "$(starship init zsh)"
fi 

# The following lines have been added by Docker Desktop to enable Docker CLI completions.
fpath=($HOME/.docker/completions $fpath)
autoload -Uz compinit
compinit
# End of Docker CLI completions

# Added by Windsurf
export PATH="$HOME/.codeium/windsurf/bin:$PATH"

# opencode
export PATH=/Users/tilmannbruckhaus/.opencode/bin:$PATH

# Load environment variables from .env.local if it exists (gitignored for security)
if [[ -f "$HOME/.env.local" ]]; then
    set -a
    source "$HOME/.env.local"
    set +a
fi
