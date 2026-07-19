# Hexling - a robot pet for the Tildagon badge + BadgeBot/HexDrive hexpansion.

SIM_DIR ?= $(HOME)/projects/tildagon/official/badge-2024-software
SIM_PY  := $(CURDIR)/.venv-sim/bin/python
MPR     := $(CURDIR)/.venv-sim/bin/mpremote

# Everything the badge needs at runtime; nothing else gets deployed.
APP_FILES = __init__.py app.py face.py hexdrive.py metadata.json moves.py pet.py tildagon.toml

.PHONY: test sim deploy venv clean

# Headless test suite (plain CPython; no simulator or badge needed).
test:
	python3 -m pytest tests/ -q

# One-time environment for sim + deploy (needs uv).
venv:
	uv venv --python 3.10 --managed-python .venv-sim
	uv pip install --python $(SIM_PY) -r $(SIM_DIR)/sim/requirements.txt mpremote pytest

# Run the app in the official badge simulator (keyboard a-f = buttons).
sim:
	ln -sfn $(CURDIR) $(SIM_DIR)/sim/apps/hexling
	cd $(SIM_DIR)/sim && $(SIM_PY) run.py hexling.HexlingApp

# Copy the app onto a badge connected over USB.
deploy:
	$(MPR) fs mkdir :/apps 2>/dev/null || true
	$(MPR) fs rm -rv :/apps/hexling 2>/dev/null || true
	$(MPR) fs mkdir :/apps/hexling
	$(MPR) fs cp $(APP_FILES) :/apps/hexling/
	$(MPR) reset

clean:
	find . -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache
