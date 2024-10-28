#!/bin/sh

# Early environment setup
if [ -f ${HOME}/.bash_profile ]; then
   source ${HOME}/.bash_profile
fi

# ZSH Options
# change directory without typing "cd"
setopt AUTO_CD
# can use "#" as comment:
unsetopt EXTENDED_GLOB
# Completion settings
zstyle ':completion:*' matcher-list 'm:{a-zA-Z}={A-Za-z}' 'r:|[._-]=* r:|=*' 'l:|=* r:|=*'
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
eval "$(starship init zsh)"

# git:
alias git=hub
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
alias gdd='git diff origin/main..HEAD'
alias gddc="git --no-pager diff --cached"
alias gt='git branch -u $(git remote)/$(git rev-parse --abbrev-ref HEAD)'
alias pull="git pull"
alias push="git push"
alias pusht='git push --set-upstream $(git remote) $(git rev-parse --abbrev-ref HEAD)'
alias gu='git reset --soft HEAD\^'
alias ga="git add"
alias gc="git commit"

# Common ls aliases
alias ls="ls --color=auto"
alias ll='ls -lah'
alias llt='ls -laht'
alias la='ls -lAh'
alias l='ls -lah'
alias lls='ls -lSh'

# python:
alias python=python3
alias ptest='python -m unittest discover'
alias venv='source .env/bin/activate'
export PYTHONPATH=.:$PYTHONPATH
export PATH="/Library/Frameworks/Python.framework/Versions/3.11/bin:$PATH"

# other aliases:
alias less='less -R'
alias ccat='pygmentize -g'

# path:
export PATH=$PATH:/bin
export PATH=$PATH:/sbin
export PATH=$PATH:/usr/bin
export PATH=$PATH:/usr/sbin
export PATH=$PATH:/usr/local/bin
export PATH=$PATH:/usr/local/sbin
export PATH=$PATH:/usr/local/git/bin
export PATH="$HOME/.local/bin:$PATH"

# source local profile (company environment variables, etc.)
export LOCAL_PROFILE=${HOME}/.local_profile.sh
[[ -r "${LOCAL_PROFILE}" ]] && source "${LOCAL_PROFILE}"

export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  # This loads nvm
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"  # This loads nvm bash_completion

# START dotfiles utilities
alias stash="$HOME/.local/bin/stash_wrapper.sh"
alias unzippy="$HOME/.local/bin/unzippy_wrapper.sh"
# END dotfiles utilities
