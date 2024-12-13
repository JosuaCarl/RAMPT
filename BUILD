# BUILD

# Define a Python library for shared code like utils.py
python_library(
    name = "gui",
    srcs = [ "source/gui" ],  # Include all library files here
    visibility = ["//src:__subpackages__"],  # Allow usage in this package or subpackages
)

python_library(
    name = "steps",
    srcs = [ "source/steps" ],  # Include all library files here
    visibility = ["//src:__subpackages__"],  # Allow usage in this package or subpackages
)

python_library(
    name = "helpers",
    srcs = [ "source/helpers" ],  # Include all library files here
    visibility = ["//src:__subpackages__"],  # Allow usage in this package or subpackages
)

# Define the Python binary that will serve as the entry point
python_binary(
    name = "main",
    main = "source/gui/main.py",
    deps = [
        ":helpers",
        ":steps",
        ":gui"  # Add dependencies for the utils library
    ],
)