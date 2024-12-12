# BUILD

# Define a Python library for shared code like utils.py
python_library(
    name = "utils",
    srcs = ["utils.py"],  # Include all library files here
    visibility = ["//src:__subpackages__"],  # Allow usage in this package or subpackages
)

# Define the Python binary that will serve as the entry point
python_binary(
    name = "main",
    srcs = ["main.py"],
    deps = [
        ":utils",  # Add dependencies for the utils library
    ],
)