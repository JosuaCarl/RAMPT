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

# TODO: IMPORT ALL LIBARARIES
package(default_visibility = ["PUBLIC"])

pip_library(
    name = "poetry",
    version = "1.8.3",
    zip_safe = False,
)

genrule(
    name = "Test poetry"
    cmd = "poetry --version"
)

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