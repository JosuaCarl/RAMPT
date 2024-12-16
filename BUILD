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

# TODO: IMPORT ALL LIBRARIES OR FIND A WAY FOR POETRY TO BE INSTALLED AND USED
pip_library(
    name = "poetry_install",
    package_name = "poetry",
    version = "1.8.3",
    visibility = ["PUBLIC"]
)
"""
genrule(
    name = "poetry_install",
    cmd = "curl -sSL https://install.python-poetry.org | python3 -",
    visibility = ["PUBLIC"]
)
"""

genrule(
    name = "Test poetry",
    outs = ["poetry_version.txt"],
    deps = [":poetry_install"],
    cmd = 'poetry --version > "$OUT"'
)

genrule(
    name = "poetry_lock",
    srcs = ["pyproject.toml"],
    deps = [":poetry_install"],
    outs = ["poetry_lock.txt"],
    cmd = 'poetry lock --no-update --no-interaction > "$OUT"',
    visibility = ["PUBLIC"]
)

genrule(
    name = "poetry_install",
    srcs = ["poetry.lock"],
    deps = [":poetry_lock"],
    outs = ["poetry_install.txt"],
    cmd = 'poetry install > "$OUT"',
    visibility = ["PUBLIC"]
)

'''
# TODO: Use cmd to install SIRIUS, MZMINE, MSCONVERT if not already installed
genrule(
    name = "word_count",
    srcs = ["file.txt"],
    outs = ["file.wordcount"],
    cmd = "wc $SRCS > $OUT",
)


# TODO: Define tests
python_test(
    name = "",
    srcs = ["greetings_test.py"],
    # Here we have used the shorthand `:greetings` label format. This format can be used to refer to a rule in the same
    # package and is shorthand for `//src/greetings:greetings`.
    deps = [":greetings"],
)



# TODO: Make final binary to export
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
'''