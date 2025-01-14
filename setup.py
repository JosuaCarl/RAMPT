#!/usr/bin/env python3

import sys as sys
from cx_Freeze import setup, Executable

from os.path import join
import toml

with open("pyproject.toml", "r") as project_file:
    project_info = toml.load(project_file)["project"]

# Additional files
include_files = [
    ("ramp.png", join("share", "ramp.png"))
]

# Create an executable.
exe = Executable(
    script=join("source", "__main__.py"),
    base="gui",
    icon="ramp",
    target_name=project_info['name'].lower(),
)


# Setup cx_Freeze options.
options = {
    "build_exe": {
        "includes": [],
        "excludes": [],
        "packages": [],
        "include_files": include_files,
    }
}

# Call the setup function.
setup(
    name=project_info['name'],
    version=project_info['version'],
    description=project_info['description'],
    author=", ".join([author["name"] for author in project_info['authors']]),
    author_email=", ".join([author["email"] for author in project_info['authors']]),
    url=""
    options=options,
    executables=[exe],
)