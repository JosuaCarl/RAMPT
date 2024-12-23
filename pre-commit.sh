#!/bin/bash

# Use ruff for formatting
poetry --directory dependencies/python run ruff --config dependencies/python/pyproject.toml format 

# Use ruff for linting
poetry --directory dependencies/python run ruff --config dependencies/python/pyproject.toml check --fix