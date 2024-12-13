# Import Proteowizard
FROM chambm/pwiz-skyline-i-agree-to-the-vendor-licenses:3.0.24284-bc93c28 AS converter

# Set the working directory in the container
WORKDIR /app

# Copy the application files into the container
COPY . .


# Define alias for msconvert
RUN echo '#!/bin/bash\nwine msconvert' > /usr/bin/msconvert && \
    chmod +x /usr/bin/msconvert


# Install dependencies on Ubuntu
RUN apt-get update && apt-get install -y \
    software-properties-common\
    tree \
    curl

# Install python dependencies
RUN add-apt-repository ppa:deadsnakes/ppa && apt-get update && apt-get install -y \
    build-essential \
    libffi-dev \
    libssl-dev \
    zlib1g-dev \
    libbz2-dev \
    libreadline-dev \
    libsqlite3-dev \
    libncurses5-dev \
    libgdbm-dev \
    libnss3-dev \
    liblzma-dev \
    --no-install-recommends && \
    apt-get clean

# Install python
ENV PYTHON_VERSION="3.12.8"
RUN curl -L https://www.python.org/ftp/python/$PYTHON_VERSION/Python-$PYTHON_VERSION.tgz -o Python-$PYTHON_VERSION.tgz && \
    tar -xf Python-$PYTHON_VERSION.tgz && \
    cd Python-$PYTHON_VERSION && \
    ./configure --enable-optimizations && \
    make -j$(nproc) && \
    make altinstall && \
    rm -rf Python-$PYTHON_VERSION Python-$PYTHON_VERSION.tgz

# Define alias for python
RUN echo '#!/bin/bash\npython3.12' > /usr/bin/python && \
    chmod +x /usr/bin/python

# Install poetry
RUN curl -sSL https://install.python-poetry.org | python - && \
    ln -s /root/.local/bin/poetry /usr/local/bin/poetry


# Install Python dependencies listed in pyproject.toml
RUN poetry lock --no-update && \
    poetry install --no-root

# Install MZmine
ENV MZMINE_DIR=/app/mzmine

RUN mkdir -p $MZMINE_DIR && chmod -R +w $MZMINE_DIR && \
    curl -L https://github.com/mzmine/mzmine/releases/download/v4.4.3/mzmine_Linux_portable-4.4.3.zip -o mzmine.zip && \
    unzip mzmine.zip -d $MZMINE_DIR && \
    chmod -R +x $MZMINE_DIR/* && \
    rm mzmine.zip

ENV PATH="$PATH:$MZMINE_DIR/bin"

# Install Sirius
ENV SIRIUS_DIR=/app/sirius

RUN mkdir -p $SIRIUS_DIR  && chmod -R +w $MZMINE_DIR &&  \
    curl -L https://github.com/sirius-ms/sirius/releases/download/v6.0.7/sirius-6.0.7-linux64.zip -o sirius.zip && \
    unzip sirius.zip -d $SIRIUS_DIR && \
    mv $SIRIUS_DIR/sirius/* $SIRIUS_DIR && \
    rm -d $SIRIUS_DIR/sirius && \
    chmod -R +x $SIRIUS_DIR/* && \
    rm sirius.zip

ENV PATH="$PATH:$SIRIUS_DIR/bin"

# Clean apt-get
RUN apt-get purge -y build-essential \
    && apt-get autoremove -y \
    && apt-get clean

# Expose 5000 to host
EXPOSE 5000

CMD [ "python", "-m", "source.gui.main" "-H" "0.0.0.0" "--debug" ]