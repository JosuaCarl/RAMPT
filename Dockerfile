# Define environment image
FROM ubuntu:24.04

# Set the working directory in the container
WORKDIR /app

# Copy the application files into the container
COPY . .

# Install dependent packages
RUN apt-get update && \
    apt-get install -y \
    python3 \
    python3-pip \
    curl \
    build-essential \
    libssl-dev \
    libffi-dev \
    unzip \
    python3-dev && \
    apt-get clean

# Install Python packages using pip or Poetry
RUN pip install --no-cache-dir poetry

# Install Python dependencies listed in pyproject.toml
RUN poetry install --no-dev

# Install MZmine
ENV MZMINE_DIR=/home/opt/mzmine

RUN mkdir -p $MZMINE_DIR && \
    curl -L https://github.com/mzmine/mzmine/releases/download/v4.4.3/mzmine_Linux_portable-4.4.3.zip | \
    unzip -d $MZMINE_DIR -\
    chmod -R +x $MZMINE_DIR/*

ENV PATH="$PATH:$MZMINE_DIR/bin"


# Install Sirius
ENV SIRIUS_DIR=/home/opt/sirius

RUN mkdir -p $SIRIUS_DIR && \
    curl -L https://github.com/sirius-ms/sirius/releases/download/v6.0.7/sirius-6.0.7-linux64.zip | \
    unzip -d $SIRIUS_DIR - \
    chmod -R +x $SIRIUS_DIR/*

ENV PATH="$PATH:$SIRIUS_DIR/bin"


# Define alias for msconvert
RUN alias msconvert="docker pwiz run wine msconvert"



# Expose a port if needed (e.g., for a web server)
# EXPOSE 5000

# Specify the command to run when the container starts
CMD ["python", "-m", "source.gui.main"]
