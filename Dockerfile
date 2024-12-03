# Define environment image
FROM python:3.12.7-windowsservercore-ltsc2022

# Set the working directory in the container
WORKDIR /app

# Copy the application files into the container
COPY . .

# Install including Pipx
RUN python -m pip install --user pipx && \
    pipx ensurepath

# Install Conda
RUN curl https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86_64.exe -o miniconda.exe &&\
    start /wait "" .\miniconda.exe /S && \
    del miniconda.exe

# Install poetry
RUN pipx install poetry

# Install python dependencies
RUN conda create -n mine2sirius && \
    conda activate mine2sirius && \
    poetry lock --no-update && \
    poetry install


# INSTALL external dependencies
# Install MZmine
ENV MZMINE_DIR="C:\mzmine"

RUN mkdir $MZMINE_DIR && \
    curl https://github.com/mzmine/mzmine/releases/download/v4.4.3/mzmine_Windows_portable-4.4.3.zip -o mzmine.zip \
    tar -xf mzmine.zip -C $MZMINE_DIR -\
    rm mzmine.zip

ENV PATH="${MZMINE_DIR};${PATH}"


# Install Sirius
ENV SIRIUS_DIR="C:\sirius"

RUN mkdir -p $SIRIUS_DIR && \
    curl https://github.com/sirius-ms/sirius/releases/download/v6.0.7/sirius-6.0.7-win64.zip -o sirius.zip\
    tar -xf sirius.zip -C $SIRIUS_DIR - \
    rm sirius.zip

ENV PATH="${SIRIUS_DIR};${PATH}"


# Install msconvert
ENV MSCONVERT_DIR="C:\msconvert"

RUN mkdir -p $MSCONVERT_DIR && \
    curl https://mc-tca-01.s3.us-west-2.amazonaws.com/ProteoWizard/bt83/3291953/pwiz-bin-windows-x86_64-vc143-release-3_0_24337_5211b18.tar.bz2 -o msconvert.tar.bz2\
    tar -xf msconvert.tar.bz2 -C $MSCONVERT_DIR - \
    rm msconvert.tar.bz2

ENV PATH="${MSCONVERT_DIR};${PATH}"


# Specify the command to run when the container starts
CMD ["python", "-m", "source.gui.main"]
