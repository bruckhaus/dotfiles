set shell := ["bash", "-eu", "-o", "pipefail", "-c"]

venv_dir := ".venv"
python := venv_dir + "/bin/python"

default:
  @just --list

venv:
  python3 -m venv {{venv_dir}}

deps: venv
  {{python}} -m pip install -U pip
  {{python}} -m pip install -r requirements.txt
  {{python}} -m pip check

dry-run: deps
  {{python}} install.py --dry-run

install: deps
  {{python}} install.py

wrappers: deps
  {{python}} install.py --dry-run

status:
  @echo "python: $({{python}} -c 'import sys; print(sys.executable)')"
  @echo "pip: $({{python}} -m pip -V)"
