#!/bin/bash
COMMANDS="msconvert"
INSTALL_PATH=$1

for COMMAND in $COMMANDS; do
    if ! command -v "$COMMAND" &> /dev/null; then
        echo "$COMMAND not found. Installing..."
        exit 1
    else
        echo "$COMMAND is already available."
    fi
done
