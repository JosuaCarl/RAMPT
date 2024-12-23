#!/bin/bash
COMMANDS="mzmine mzmine_console"
INSTALL_PATH=$1

for COMMAND in $COMMANDS; do
    if ! command -v "$COMMAND" &> /dev/null; then
        echo "$COMMAND not found. Installing..."

        mkdir -p $INSTALL_PATH && chmod -R +w $INSTALL_PATH && \
        curl -L https://github.com/mzmine/mzmine/releases/download/v4.4.3/mzmine_Linux_portable-4.4.3.zip -o mzmine.zip && \
        unzip mzmine.zip -d $INSTALL_PATH && \
        chmod -R +x $INSTALL_PATH/* && \
        rm mzmine.zip

        exit 0
    else
        echo "$COMMAND is already available."
    fi
done
