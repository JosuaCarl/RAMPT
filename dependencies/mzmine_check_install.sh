#/bin/bash

MZMINE_DIR = 

mkdir -p $MZMINE_DIR && chmod -R +w $MZMINE_DIR && \
curl -L https://github.com/mzmine/mzmine/releases/download/v4.4.3/mzmine_Linux_portable-4.4.3.zip -o mzmine.zip && \
unzip mzmine.zip -d $MZMINE_DIR && \
chmod -R +x $MZMINE_DIR/* && \
rm mzmine.zip