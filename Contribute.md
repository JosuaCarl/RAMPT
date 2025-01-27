# Contribute

## General Informations:
- Package management with [uv](https://docs.astral.sh/uv/)
- Linting and Formatting with [Ruff](https://docs.astral.sh/ruff/)
- The installation can also be done with an installation script in ./rampt/installer.py


## Output
- Please use the methods in [source.helpers.logging](./source/helpers/logging.py) for verbose output

## TODO
- Improvement of Documentation
- Integration testing
    - test_90_taipy.py is not complete
- Testing of scripts that require non-python dependencies in Action workflow
    - Attention: MS conv can not be tested from MacOS (if statement to skip the job)
    - Sirius needs ENV variables (Github secrets) set to login
- x_out_paths should handle multiple files/folders (and return a list of paths that can be matched to in_paths)
- Parallelizastion especially of SIRIUS and GNPS
- Batch files are read to search for output information (parse .mzbatch file as XML)
- Use
- Search for TODO: and work on it