# Python BASE
FROM python:3.12-slim AS base-image

# Install on Debian
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    unzip && \
    apt-get clean

# Install poetry
RUN curl -sSL https://install.python-poetry.org | python - && \
    ln -s /root/.local/bin/poetry /usr/local/bin/poetry


# Set the working directory in the container
WORKDIR /app

# Copy the application files into the container
COPY . .

ENV PYTHON_VENV="/app/mine2sirius_venv"
RUN python -m venv $PYTHON_VENV

# Install Python dependencies listed in pyproject.toml
RUN poetry env use $PYTHON_VENV/bin/python && \
    poetry lock --no-update && \
    poetry install


# INSTALL external dependencies
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


# Import Proteowizard
FROM chambm/pwiz-skyline-i-agree-to-the-vendor-licenses:3.0.24284-bc93c28 AS converter

# Set the working directory in the container
WORKDIR /app

# Copy the application files into the container
COPY --from=base-image /app /app

# Define alias for msconvert
RUN echo '#!/bin/bash\nwine msconvert' > /usr/bin/msconvert && \
    chmod +x /usr/bin/msconvert

# Define aliases for other programs
ENV PATH="$PATH:/app/sirius/bin"
ENV PATH="$PATH:/app/mzmine/bin"

# Expose a port if needed (e.g., for a web server)
# EXPOSE 5000
RUN . /app/mine2sirius_venv/bin/activate
RUN echo '#!/bin/bash\n/app/mine2sirius_venv/bin/python' > /usr/bin/python && \
    chmod +x /usr/bin/python
RUN python --version && sleep 2

RUN tree /app && sleep 5

# Specify the command to run when the container starts
CMD ["python", "-m", "source.gui.main"]
