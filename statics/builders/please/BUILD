# BUILD

# Define a Python libraries
python_library(
    name = "gui",
    srcs = [ "source/gui" ],  # Include all library files here
    visibility = ["//src:__subpackages__"],  # Allow usage in this package or subpackages
)

python_library(
    name = "steps",
    srcs = [ "source/steps" ],
    visibility = ["//src:__subpackages__"]
)

python_library(
    name = "helpers",
    srcs = [ "source/helpers" ],
    visibility = ["//src:__subpackages__"]
)

# Install poetry
pip_library(
    name = "install_poetry",
    package_name = "poetry",
    version = "1.8.3",
    visibility = ["PUBLIC"]
)

# Poetry test
gentest(
    name = "Test poetry",
    outs = ["poetry_version.txt"],
    deps = [":install_poetry"],
    test_cmd = 'poetry --version > "$OUT"'
)

# Install python dependencies
genrule(
    name = "poetry_lock",
    srcs = ["pyproject.toml"],
    deps = [":install_poetry"],
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

# Test dependency availability
gentest(
    name = "Test dependency",
    outs = ["ruff_version.txt"],
    deps = [":poetry_install"],
    test_cmd = 'ruff --version > "$OUT"'
)


# Ensure MSCONVERT
genrule(
    name = "ensure_msconvert",
    srcs = ["dependencies/ensure_msconvert.sh"],
    outs = ["dependencies/msconvert"],
    cmd = "bash $(location dependencies/ensure_msconvert.sh) $(out)",
)

"""
docker_pull(
    name = "msconvert_docker_image",
    image = "chambm/pwiz-skyline-i-agree-to-the-vendor-licenses:3.0.24284-bc93c28",
)
genrule(
    name = "add_msconvert",
    docker = "msconvert_docker_image",
    visibility = ["PUBLIC"]
)
"""


# Ensure MZMINE
genrule(
    name = "ensure_mzmine",
    srcs = ["dependencies/ensure_mzmine.sh"],
    outs = ["dependencies/mzmine"],
    cmd = "bash $(location dependencies/ensure_mzmine.sh) $(out)",
)


# Ensure SIRIUS
genrule(
    name = "ensure_sirius",
    srcs = ["dependencies/ensure_sirius.sh"],
    outs = ["dependencies/sirius"],
    cmd = "bash $(location dependencies/ensure_sirius.sh) $(out)",
)



'''
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