#!/bin/bash

# Use ruff for linting
poetry --directory dependencies/python run ruff --config dependencies/python/pyproject.toml check --fix