#!/bin/sh

if [ -f ${HOME}/.bash_profile ]; then
   source ${HOME}/.bash_profile
fi

# zsh:
DISABLE_UPDATE_PROMPT=true
# Path to your oh-my-zsh configuration.
ZSH=$HOME/.oh-my-zsh
# Set name of the theme to load.
# Look in ~/.oh-my-zsh/themes/
# Optionally, if you set this to "random", it'll load a random theme each
# time that oh-my-zsh is loaded.
ZSH_THEME="candy"
# ZSH_THEME="bullet-train"
# ZSH_THEME="robbyrussell"
# ZSH_THEME="gnzh"
# ZSH_THEME="wedisagree"
# Set to this to use case-sensitive completion
# CASE_SENSITIVE="true"
# Comment this out to disable bi-weekly auto-update checks
# DISABLE_AUTO_UPDATE="true"
# Uncomment to change how often before auto-updates occur? (in days)
# export UPDATE_ZSH_DAYS=13
# Uncomment following line if you want to disable colors in ls
# DISABLE_LS_COLORS="true"
# Uncomment following line if you want to disable autosetting terminal title.
# DISABLE_AUTO_TITLE="true"
# Uncomment following line if you want to disable command autocorrection
# DISABLE_CORRECTION="true"
# Uncomment following line if you want red dots to be displayed while waiting for completion
# COMPLETION_WAITING_DOTS="true"
# vcs:
# Uncomment following line if you want to disable marking untracked files under
# VCS as dirty. This makes repository status check for large repositories much,
# much faster.
# DISABLE_UNTRACKED_FILES_DIRTY="true"
# Which plugins would you like to load? (plugins can be found in ~/.oh-my-zsh/plugins/*)
# Custom plugins may be added to ~/.oh-my-zsh/custom/plugins/
# Example format: plugins=(rails git textmate ruby lighthouse)
plugins=(git)
# source $ZSH/oh-my-zsh.sh

# Starship
eval "$(starship init zsh)"
# Activate syntax highlighting
source $(brew --prefix)/share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh
# Disable underline
(( ${+ZSH_HIGHLIGHT_STYLES} )) || typeset -A ZSH_HIGHLIGHT_STYLES
ZSH_HIGHLIGHT_STYLES[path]=none
ZSH_HIGHLIGHT_STYLES[path_prefix]=none
# Activate autosuggestions
source $(brew --prefix)/share/zsh-autosuggestions/zsh-autosuggestions.zsh
# Allow changing directories without typing 'cd'
setopt AUTO_CD

# git:
alias git=hub
alias gs="git status"
#alias glm='git log origin/main..HEAD --oneline | cat'
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
alias ll='ls -lah'
alias llt='ls -laht'
alias la='ls -lAh'
alias l='ls -lah'
alias ls='ls -G'

# python:
alias python=python3
alias ptest='python -m unittest discover'
alias venv='source .env/bin/activate'
export PYTHONPATH=.:$PYTHONPATH
export PATH="/Library/Frameworks/Python.framework/Versions/3.11/bin:$PATH"

# other aliases:
alias less='less -R'
alias ccat='pygmentize -g'
alias stash="$HOME/.local/bin/stash_wrapper.sh"

# path:
# Customize to your needs...
export PATH=$PATH:/bin
export PATH=$PATH:/sbin
export PATH=$PATH:/usr/bin
export PATH=$PATH:/usr/sbin
export PATH=$PATH:/usr/local/bin
export PATH=$PATH:/usr/local/sbin
export PATH=$PATH:/usr/local/git/bin
# export PATH="$HOME/anaconda/bin:$PATH"

# mysql:
export PATH=$PATH:/usr/local/mysql/bin

# Scala:
SCALA_HOME=/usr/share/scala; export SCALA_HOME
PATH=$SCALA_HOME/bin:$PATH; export PATH

# Spark:
SPARK_HOME=/Users/tilmannbruckhaus/dev/spark-1.2.0-bin-hadoop2.4; export SPARK_HOME

# cert:
## export SSL_CERT_FILE=/usr/local/etc/cacert.pem

# RVM:
[[ -s "$HOME/.rvm/scripts/rvm" ]] && source "$HOME/.rvm/scripts/rvm" # Load RVM into a shell session *as a function*
[[ -s "$HOME/.rvm/scripts/rvm" ]] && . "$HOME/.rvm/scripts/rvm"  # This loads RVM into a shell session.
PATH=$PATH:$HOME/.rvm/bin # Add RVM to PATH for scripting
export PATH=$PATH:/Users/tilmannbruckhaus/.rvm/gems/ruby-1.9.3-p392/bin
export PATH=$PATH:/Users/tilmannbruckhaus/.rvm/gems/ruby-1.9.3-p392@global/bin
export PATH=$PATH:/Users/tilmannbruckhaus/.rvm/rubies/ruby-1.9.3-p392/bin
export PATH=$PATH:/Users/tilmannbruckhaus/.rvm/bin

# source local profile (company environment variables, etc.)
export LOCAL_PROFILE=${HOME}/.local_profile.sh
[[ -r "${LOCAL_PROFILE}" ]] && source "${LOCAL_PROFILE}"

export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  # This loads nvm
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"  # This loads nvm bash_completion

# The next line updates PATH for the Google Cloud SDK.
if [ -f '/Users/tilmannbruckhaus/google-cloud-sdk/path.zsh.inc' ]; then . '/Users/tilmannbruckhaus/google-cloud-sdk/path.zsh.inc'; fi

# The next line enables shell command completion for gcloud.
if [ -f '/Users/tilmannbruckhaus/google-cloud-sdk/completion.zsh.inc' ]; then . '/Users/tilmannbruckhaus/google-cloud-sdk/completion.zsh.inc'; fi

export PATH="$HOME/.local/bin:$PATH"

alias stash="/Users/tilmannbruckhaus/.local/bin/stash_wrapper.sh $(pwd)"

alias stash="/Users/tilmannbruckhaus/.local/bin/stash_wrapper.sh"
