#!/usr/bin/bash

# Use ruff for formatting
uv run ruff format

# Use ruff for linting
uv run ruff check --fix
