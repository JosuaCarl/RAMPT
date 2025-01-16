#!/usr/bin/env python3

import sys as sys
from cx_Freeze import setup, Executable

from os.path import join
import toml

with open("pyproject.toml", "r") as project_file:
    project_info = toml.load(project_file)["project"]

# Additional files
include_files = [(join("share", "ramp.png"), join("share", "ramp.png"))]

# Create an executable.
exe = Executable(
    script=join("source", "__main__.py"),
    base="gui",
    icon="ramp",
    target_name=project_info["name"].lower(),
)


def get_package_raw(dependency: str) -> str:
    package = ""
    for char in dependency:
        if char in "<>=":
            break
        package += char
    return package


# Setup cx_Freeze options.
options = {
    "build_exe": {
        "includes": [],
        "excludes": [],
        "packages": [],  # [get_package_raw(dependency) for dependency in project_info["dependencies"]],
        "include_files": include_files,
    }
}
print(options)

# Call the setup function.
setup(
    name=project_info["name"],
    version=project_info["version"],
    description=project_info["description"],
    author=", ".join([author["name"] for author in project_info["authors"]]),
    options=options,
    license=project_info["license"],
    keywords=project_info["keywords"],
    executables=[exe],
)
