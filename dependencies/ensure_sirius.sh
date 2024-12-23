#!/bin/bash
COMMANDS="sirius"
INSTALL_PATH=$1

for COMMAND in $COMMANDS; do
    if ! command -v "$COMMAND" &> /dev/null; then
        echo "$COMMAND not found. Installing..."

        mkdir -p $INSTALL_PATH  && chmod -R +w $INSTALL_PATH &&  \
        curl -L https://github.com/sirius-ms/sirius/releases/download/v6.0.7/sirius-6.0.7-linux64.zip -o sirius.zip && \
        unzip sirius.zip -d $INSTALL_PATH && \
        mv $INSTALL_PATH/sirius/* $INSTALL_PATH && \
        rm -d $INSTALL_PATH/sirius && \
        chmod -R +x $INSTALL_PATH/* && \
        rm sirius.zip
        exit 0
    else
        echo "$COMMAND is already available."
    fi
done
