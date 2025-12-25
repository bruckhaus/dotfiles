dotfiles
========

My dot files, configs, and setups.

## Install

Clone the repo:

```sh
git clone git@github.com:bruckhaus/dotfiles.git
cd dotfiles
```

Create a local virtualenv for the installer + utilities:

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Preview changes (recommended):

```sh
python install.py --dry-run
```

Apply changes:

```sh
python install.py
```

### Using `just`

If you have [`just`](https://github.com/casey/just) installed:

```sh
just deps
just dry-run
just install
```

## What this repo installs

- Dotfiles listed in `config.yaml` are symlinked into your home directory.
- Wrapper scripts for utilities listed in `config.yaml` are created under `~/.local/bin`.
- Aliases listed in `config.yaml` are managed inside the `# START dotfiles utilities` section in `.zshrc`.

## Repository layout

- `config.yaml`: declarative list of dotfiles, utility scripts, and aliases
- `install.py`: installer (symlinks + wrapper scripts + alias updates)
- `scripts/`: Python utilities that can be invoked via installed wrappers
- `requirements.txt`: runtime dependencies for the installer and utilities
