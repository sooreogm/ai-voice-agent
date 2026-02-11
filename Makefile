SHELL := /bin/bash
VENV := .venv
UVICORN := $(VENV)/bin/uvicorn
PYTHON := $(VENV)/bin/python
UV := uv

.PHONY: init create install update sync run activate clean import start

init:
	$(UV) init

create:
	@if [ ! -d "$(VENV)" ]; then \
		$(UV) venv $(VENV); \
	fi

sync: create
	$(UV) sync

import:
	uv add -r requirements.txt
	uv sync


install: create
	@if [ -f pyproject.toml ]; then \
		$(UV) sync; \
	elif [ -f requirements.txt ]; then \
		$(UV) pip install -r requirements.txt; \
	else \
		echo "No pyproject.toml or requirements.txt found."; \
		exit 1; \
	fi

update: create
	@if [ -f pyproject.toml ]; then \
		$(UV) sync; \
	elif [ -f requirements.txt ]; then \
		$(UV) pip install -U -r requirements.txt; \
	else \
		echo "No pyproject.toml or requirements.txt found."; \
		exit 1; \
	fi

run: create
	$(PYTHON) main.py

start:
	$(UVICORN) app.main:app --reload

activate:
	@echo "Run: source $(VENV)/bin/activate"

clean:
	rm -rf $(VENV)
