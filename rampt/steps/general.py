#!/usr/bin/env python
"""
Provide super classed for steps in program to ensure transition of intermediate results.
"""

import os
import regex
import json
from multipledispatch import dispatch

from typing import Callable

import dask.multiprocessing

from rampt.helpers.general import *
from rampt.helpers.logging import *


# Helper methods for classes / namespaces
@dispatch(object, object)
def get_value(instance: object | dict, key):
    """
    Extract an attribute of a class or dictionary.

    :param instance: Instance of a class or dictionary
    :type instance: object | dict
    :param key: Attribute or key
    :type key: any
    :return: Value of given key
    :rtype: any
    """
    if isinstance(instance, dict):
        if key in instance:
            return instance.get(key)
    else:
        return getattr(instance, key)


@dispatch(object, object, object)
def get_value(instance: object | dict, key, default):  # noqa: F811
    """
    Extract an attribute of a class or dictionary. If none is present, return default.

    :param instance: Instance of a class or dictionary
    :type instance: object | dict
    :param key: Attribute or key
    :type key: any
    :param default: Default if entry is not found
    :type default: any
    :return: Value of given key
    :rtype: any
    """
    if isinstance(instance, dict):
        if key in instance:
            return instance.get(key, default)
    else:
        if hasattr(instance, key):
            value = getattr(instance, key, default)
            if value is None:
                return default
            else:
                return value
        else:
            return default


def set_value(instance: object | dict, key, new_value, add_key: bool):
    """
    Set the value of an attribute or dictionary entry.

    :param instance: Instance of a class or dictionary.
    :type instance: object | dict
    :param key: Attribute or key.
    :type key: any
    :param new_value: Value to link to entry.
    :type new_value: any
    :param add_key: Adds the key, if it is not already present.
    :type add_key: bool
    :return: Instance with updated value.
    :rtype: any
    """
    if isinstance(instance, dict):
        if add_key:
            instance.update({key: new_value})
        else:
            instance[key] = new_value
    else:
        if hasattr(instance, key):
            setattr(instance, key, new_value)
        elif add_key:
            setattr(instance, key, new_value)
        else:
            logger.error(
                message=f"The key={key} is not found in instance={instance} and add_key={add_key}.",
                error_type=ValueError,
            )

    return instance


class Step_Configuration:
    """
    Class configuration of pipeline steps in the pipeline.
    """

    def __init__(
        self,
        name: str = None,
        platform: str = "Linux",
        overwrite: bool = True,
        nested: bool = False,
        workers: int = 1,
        pattern: str = None,
        suffix: str = None,
        prefix: str = None,
        contains: str = None,
        patterns: dict[str, str] = {},
        mandatory_patterns: dict[str, str] = {},
        save_log: bool = True,
        verbosity: int = 1,
    ):
        """
        Initialize the pipeline step configuration. Used for pattern matching.
        Provides additional variables for saving processed input and out_locations, its output, and errors.

        :param name: Name of the step, defaults to None
        :type name: str, optional
        :param platform: Computation platform, defaults to "Linux"
        :type platform: str, optional
        :param overwrite: overwrite previous results, defaults to True
        :type overwrite: bool, optional
        :param workers: Number of workers to use for parallel execution, defaults to 1
        :type workers: int, optional
        :param pattern: Pattern for folder matching, defaults to ""
        :type pattern: str, optional
        :param suffix: Suffix for folder matching, defaults to None
        :type suffix: str, optional
        :param prefix: Prefix for folder matching, defaults to None
        :type prefix: str, optional
        :param contains: Contained strings for folder matching, defaults to None
        :type contains: str, optional
        :param patterns: Matching patterns for finding appropriate folders, defaults to None
        :type patterns: dict[str,str], optional
        :param mandatory_patterns: Mandatory pattern, that must be in the step, defaults to 1
        :type mandatory_patterns: dict[str,str], optional
        :param save_log: Whether to save the output(s), defaults to True.
        :type save_log: bool, optional
        :param verbosity: Level of verbosity, defaults to 1
        :type verbosity: int, optional
        """
        self.name = name
        self.platform = platform
        self.overwrite = overwrite
        self.nested = nested
        self.workers = workers
        self.pattern = pattern
        self.suffix = suffix
        self.prefix = prefix
        self.contains = contains
        self.patterns = patterns
        self.mandatory_patterns = mandatory_patterns
        self.save_log = save_log
        self.verbosity = verbosity
        self.update_patterns(list(self.patterns.keys()))

    # Update variables
    def update(self, attributions: dict):
        """
        Update an attribute of this object.

        :param attributions: Key value pair of attribute name and value
        :type attributions: str
        """
        self.__dict__.update(attributions)
        self.update_patterns(list(self.patterns.keys()))

    def update_pattern(
        self,
        key: str,
        pattern: str = None,
        contains: str = None,
        suffix: str = None,
        prefix: str = None,
    ):
        # Check for existing patterns
        pattern = pattern if pattern else self.pattern
        contains = contains if contains else self.contains
        suffix = suffix if suffix else self.suffix
        prefix = prefix if prefix else self.prefix

        regex_all = None
        if pattern:
            regex_all = pattern
        if contains:
            regex_all = rf"{regex_all}|.*{contains}.*" if regex_all else rf".*{contains}.*"
        if suffix:
            regex_all = rf"{regex_all}.*{suffix}$" if regex_all else rf".*{suffix}$"
        if prefix:
            regex_all = rf"^{prefix}.*{regex_all}" if regex_all else rf"^{prefix}.*"

        # Save inputs
        if regex_all:
            self.patterns[key] = regex_all

    def update_patterns(self, fill_patterns: list = []):
        for key in fill_patterns:
            self.update_pattern(
                key=key,
                pattern=self.pattern,
                contains=self.contains,
                suffix=self.suffix,
                prefix=self.prefix,
            )

    def contruct_full_regex(self, regex_id: str) -> str:
        pattern_regex = self.patterns.get(regex_id, None)
        mandatory_regex = self.mandatory_patterns.get(regex_id, None)
        if pattern_regex and mandatory_regex:
            return rf"(?={pattern_regex})(?={mandatory_regex})"
        elif pattern_regex:
            return pattern_regex
        elif mandatory_regex:
            return mandatory_regex
        else:
            return None

    # Dictionary represenation
    def dict_representation(self, attribute=None):
        attribute = attribute if attribute is not None else self

        # Case iterable (list)
        attributes_list = []
        if isinstance(attribute, list):
            for value in attribute:
                if hasattr(value, "__dict__") or isinstance(value, dict):
                    attributes_list.append(self.dict_representation(value))
                elif isinstance(value, list):
                    attributes_list.append(self.dict_representation(value))
                elif callable(value):
                    # Replace functions with True (we have only bool functions in representations)
                    attributes_list.append(True)
                else:
                    attributes_list.append(value)
            return attributes_list

        # Case dictionary
        attributes_dict = {}
        attributes_dict_representation = (
            attribute if isinstance(attribute, dict) else attribute.__dict__
        )
        for attribute, value in attributes_dict_representation.items():
            if hasattr(value, "__dict__") or isinstance(value, dict):
                attributes_dict[attribute] = self.dict_representation(value)
            elif isinstance(value, list):
                attributes_dict[attribute] = self.dict_representation(value)
            elif callable(value):
                # Replace functions with True (we have only bool functions in representations)
                attributes_dict[attribute] = True
            else:
                attributes_dict[attribute] = value
        return attributes_dict

    # IO
    def save(self, location):
        with open(location, "w") as f:
            json.dump(self.dict_representation(self), f, indent=4)

    def load(self, location):
        with open(location, "r") as f:
            config = json.loads(f.read())
        self.__init__(**config)


class Pipe_Step(Step_Configuration):
    """
    Class for steps in the pipeline.
    """

    def __init__(
        self,
        name: str = None,
        exec_path: StrPath = None,
        platform: str = "Linux",
        overwrite: bool = True,
        nested: bool = False,
        workers: int = 1,
        pattern: str = None,
        suffix: str = None,
        prefix: str = None,
        contains: str = None,
        patterns: dict[str, str] = {"in": ".*"},
        mandatory_patterns: dict[str, str] = {"in": ".*"},
        valid_runs: list[dict] = [],
        save_log: bool = False,
        verbosity: int = 1,
        additional_args: list = [],
    ):
        """
        Initialize the pipeline step. Used for pattern matching.
        Provides additional variables for saving processed input and out_locations, its output, and errors.

        :param name: Name of the step, defaults to None
        :type name: str, optional
        :param exec_path: Path of executive
        :type exec_path: StrPath
        :param platform: Computational platform/OS, defaults to Linux
        :type platform: str, optional
        :param overwrite: Whether to overwrite previous runs, defaults to True
        :type overwrite: bool, optional
        :param nested: Execute step in a nested fashion, defaults to False
        :type nested: bool, optional
        :param workers: Number of workers to use for parallel execution, defaults to 1
        :type workers: int, optional
        :param pattern: Pattern for folder matching, defaults to ""
        :type pattern: str, optional
        :param suffix: Suffix for folder matching, defaults to None
        :type suffix: str, optional
        :param prefix: Prefix for folder matching, defaults to None
        :type prefix: str, optional
        :param contains: Contained strings for folder matching, defaults to None
        :type contains: str, optional
        :param patterns: Matching patterns for finding appropriate folders, defaults to None
        :type patterns: dict[str,str], optional
        :param mandatory_patterns: Mandatory pattern, that must be in the step, defaults to {}
        :type mandatory_patterns: dict[str,str], optional
        :param valid_runs: Valid runs to check for, defaults to []
        :type valid_runs: list[dict], optional
        :param save_log: Whether to save the output(s).
        :type save_log: bool, optional
        :param verbosity: Level of verbosity, defaults to 1
        :type verbosity: int, optional
        :param additional_args: Additional arguments for mzmine, defaults to []
        :type additional_args: list, optional
        :param additional_args: Additional arguments for mzmine, defaults to []
        :type additional_args: list, optional
        """
        super().__init__(
            name=name,
            platform=platform,
            overwrite=overwrite,
            nested=nested,
            workers=workers,
            pattern=pattern,
            contains=contains,
            prefix=prefix,
            suffix=suffix,
            patterns=patterns,
            mandatory_patterns=mandatory_patterns,
            save_log=save_log,
            verbosity=verbosity,
        )
        self.valid_runs = valid_runs
        self.common_execs = []
        self.exec_path = exec_path
        self.futures = []
        self.scheduled_ios = []
        self.processed_ios = []
        self.outs = []
        self.errs = []
        self.log_paths = []
        self.results = []
        self.additional_args = additional_args

    # Executives
    def check_exec_path(self, exec_path: StrPath = None) -> bool:
        """
        Check whether a path to an executable is valid.

        :param exec_path: Path to executable, defaults to None
        :type exec_path: StrPath, optional
        :return: Path valid or not
        :rtype: bool
        """
        try:
            execute_verbose_command(f"{exec_path} --help", verbosity=0)
            return True
        except BaseException:
            pass
        return False

    def check_execs(self, exec_path: StrPath) -> StrPath:
        """
        Check a number of execuatable paths

        :param exec_path: Path to executable
        :type exec_path: StrPath
        :return: Valid path
        :rtype: StrPath
        """
        valid_exec = None
        for exec in [exec_path] + self.common_execs:
            if self.check_exec_path(exec):
                valid_exec = exec
                break

        if valid_exec and valid_exec != exec_path:
            logger.warn(f"{self.name} exec_path is set to {self.exec_path}")

        return valid_exec

    # Matching
    def match_path(self, pattern: str, path: StrPath, by_name=True) -> bool:
        """
        Match a file_name against a regex expression

        :param pattern: Pattern
        :type pattern: str
        :param path: Name of the file
        :type path: StrPath
        :return: Whether the patter is in the file name
        :rtype: bool
        """
        if by_name:
            pattern = self.contruct_full_regex(regex_id=pattern)
        if not pattern:
            return False
        return bool(regex.search(pattern=pattern, string=str(path)))

    def match_dir_paths(
        self,
        dir: StrPath,
        valid_paths: dict[str, StrPath] = {},
        patterns: dict[str, str] = {},
        check_dirs: bool = False,
    ) -> dict[str, StrPath]:
        """
        Match whether the needed files for GNPS POST request are present, according to mzmine naming scheme.

        :param dir: Directory to search in
        :type dir: StrPath
        :param valid_paths: Valid files in directory, defaults to {}
        :type valid_paths: dict[str, StrPath]
        :param patterns: Custom patterns to match against, defaults to {}
        :type patterns: dict[str, str]
        :param check_dirs: Custom patterns to match against, defaults to {}
        :type check_dirs: dict[str, str]
        :return: Valid paths
        :rtype: dict[str, StrPath]
        """
        patterns = patterns if patterns else self.patterns

        root, dirs, files = next(os.walk(dir))

        for file in files:
            for name, pattern in patterns.items():
                if valid_paths.get(name, None) and self.match_path(pattern, file):
                    valid_paths[name] = os.path.join(root, file)

        if check_dirs:
            for dir in dirs:
                for name, pattern in patterns.items():
                    if valid_paths.get(name, None) and self.match_path(pattern, dir):
                        valid_paths[name] = os.path.join(root, dir)

        return valid_paths

    # Saving
    def get_log_path(self, out_path: StrPath) -> StrPath:
        log_path = (
            os.path.join(get_directory(out_path), f"{self.name}_log.txt") if self.save_log else None
        )
        return log_path

    def store_progress(
        self,
        in_out: dict[str, StrPath],
        results=None,
        future=None,
        out: str = "",
        err: str = "",
        log_path: str = "",
    ):
        """
        Store progress in PipeStep variables. Ensures a match between reprocessed in_paths and out_paths.

        :param in_out: I/O combination with paths
        :type in_out: dict[str, StrPath]
        :param results: Results of computation in pythonic form.
        :type results: any
        :param out: Output of run, defaults to ""
        :type out: str, optional
        :param err: Error messages of run, defaults to ""
        :type err: str, optional
        :param log_path: Path to log file, defaults to ""
        :type log_path: str, optional
        """
        if in_out in self.processed_ios:
            i = self.processed_ios.index(in_out)
            self.log_paths[i] = log_path
            self.outs[i] = out
            self.errs[i] = err
            self.results[i] = results
            self.futures[i] = future
        else:
            self.processed_ios.append(in_out)
            self.outs.append(out)
            self.errs.append(err)
            self.log_paths.append(log_path)
            self.results.append(results)
            self.futures.append(future)

    def reset_progress(self):
        self.processed_ios = []
        self.log_paths = []
        self.outs = []
        self.errs = []
        self.results = []
        self.futures = []

    # Executing
    def compute(self, step_function: Callable | str | list, *args, **kwargs):
        """
        Execute a computation of a command with or without parallelization.

        :param step_function: Function to execute with arguments
        :type step_function: Callable|str|list
        :param *args: Arguments without keywords for the function
        :type *args: *args
        :param **kwargs: Keyword arguments, must contain in_paths, and out_path
        :type **kwargs: **kwargs
        """
        # Catch passed bash commands
        if isinstance(step_function, str):
            kwargs["cmd"] = step_function
            step_function = execute_verbose_command

        # Check parallelization
        if self.workers > 1:
            response = [None, None, None]
            future = dask.delayed(step_function)(*args, **kwargs)
        else:
            response = step_function(*args, **kwargs)
            future = None

        # Extract results
        results = response[0]
        out, err = [response[i] if i < len(response) else None for i in range(1, 3)]

        self.store_progress(
            in_out=kwargs.get("in_out"),
            results=results,
            future=future,
            out=out,
            err=err,
            log_path=kwargs.get("log_path", None),
        )

    def compute_futures(self):
        """
        Compute scheduled operations (futures).
        """
        futures = []
        in_outs = []
        for in_out, future in zip(self.processed_ios, self.futures):
            if future is not None:
                in_outs.append(in_out)
                futures.append(future)

        response = compute_scheduled(
            futures=futures, num_workers=self.workers, verbose=self.verbosity >= 1
        )
        for in_out, (results, out, err) in zip(in_outs, response[0]):
            i = self.processed_ios.index(in_out)
            self.outs[i] = out
            self.errs[i] = err
            self.results[i] = results

    # RUN Methods
    def run_single(self, **kwargs):
        """
        Compute a single instance of the runner

        :param kwargs: Dictionary of additional arguments for computation
        :type kwargs: ...
        """
        logger.error(
            message="The run_single function seems to be missing in local implementation",
            error_type=NotImplementedError,
        )

    def run_directory(self, **kwargs):
        """
        Compute a folder with the runner

        :param kwargs: Dictionary of additional arguments for computation
        :type kwargs: ...
        """
        logger.error(
            message="The run_directory function seems to be missing in local implementation",
            error_type=NotImplementedError,
        )

    def run_nested(self, **kwargs):
        """
        Schedule the computation of files in nested folders

        :param kwargs: Dictionary of additional arguments for computation
        :type kwargs: ...
        """
        logger.error(
            message="The run_nested function seems to be missing in local implementation",
            error_type=NotImplementedError,
        )

    # Distribution methods
    def fill_dict_standards(
        self, dictionary: dict, replacement_keys: list[str], standards_key: str = "standard"
    ):
        if standards_key in dictionary:
            for replacement_key in replacement_keys:
                if replacement_key not in dictionary:
                    dictionary[replacement_key] = dictionary[standards_key]

        return dictionary

    def extract_standard(self, standard_value: str = "standard", **kwargs) -> dict:
        """
        Extracts standard values from kwargs. If the value is not a dictionary, it is returned instead.

        :param standard_value: Standard value key, defaults to "standard"
        :type standard_value: str, optional
        :return: Dictioary with only standard values
        :rtype: dict
        """
        standards = [
            value.get(standard_value, value) if isinstance(value, dict) else value
            for key, value in kwargs.items()
        ]
        if len(kwargs) == 0:
            logger.error(
                "Gave no arguments to extract_standard. You must at least provide one.",
                error_type=ValueError,
            )
        elif len(kwargs) == 1:
            return standards[0]
        else:
            return standards

    def extract_optional(self, dictionary: dict, keys: list, return_dict: bool = False) -> dict:
        """
        Extracts standard values from kwargs. If the value is not a dictionary, it is returned instead.

        :param dictionary: Dictionary to extract
        :type dictionary: dict
        :return: Dictioary with only standard values
        :rtype: dict
        """
        optionals = {key: dictionary[key] if key in dictionary else None for key in keys}
        if len(keys) == 0:
            logger.error(
                "Gave no keys to extract_optional. You must at least provide one.",
                error_type=ValueError,
            )
        if return_dict:
            return optionals
        elif len(keys) == 1:
            return next(iter(optionals.values()))
        else:
            return list(optionals.values())

    # Input valudation an distribution
    def check_io(self, io: dict, valid_runs: list[dict] = []) -> list:
        """
        Check for a valid run style (single, directory, nested,...).

        :param io: In_out dictionary
        :type io: dict
        :param valid_runs: A list of valid run_style, i/o dicts, defaults to []
        :type valid_runs: list[dict], optional
        :return: Valid run styles
        :rtype: list
        """
        valid_runs = valid_runs if valid_runs else self.valid_runs
        # Check keys
        valid_run_styles = []
        for valid_run in valid_runs:
            for run_style, io_combos in valid_run.items():
                combo_valid = True
                for io_key, io_dict in io_combos.items():
                    if io_key in io:
                        for key, value_validation_method in io_dict.items():
                            if key not in io[io_key]:
                                combo_valid = False
                                break
                            if callable(value_validation_method) and not value_validation_method(
                                io[io_key][key]
                            ):
                                combo_valid = False
                                break
                    else:
                        combo_valid = False
                        break
                if combo_valid:
                    valid_run_styles.append(run_style)
        return valid_run_styles

    def distribute_scheduled(
        self,
        standard_value: str = "standard",
        correct_runner: str = None,
        kwargs: dict = {},
        **scheduled_io,
    ):
        """
        Distribute the scheduled

        :param standard_value: _description_, defaults to "standard"
        :type standard_value: str, optional
        :return: _description_
        :rtype: _type_
        """
        if hasattr(self, "data_ids") and standard_value == "standard":
            standard_value = self.data_ids["standard"][0]
        standard_in = self.extract_standard(standard_value, in_paths=scheduled_io["in_paths"])

        if not correct_runner:
            if self.nested:
                correct_runner = "nested"
            elif os.path.isdir(standard_in):
                correct_runner = "directory"
            else:
                correct_runner = "single"

        match correct_runner:
            case "nested":
                logger.log(
                    f"Distributing to {self.__class__.__name__} nested run.",
                    minimum_verbosity=3,
                    verbosity=self.verbosity,
                )
                return self.run_nested(**scheduled_io, **kwargs)

            case "directory":
                logger.log(
                    f"Distributing to {self.__class__.__name__} directory run.",
                    minimum_verbosity=3,
                    verbosity=self.verbosity,
                )
                return self.run_directory(**scheduled_io, **kwargs)
            case "single":
                logger.log(
                    f"Distributing to {self.__class__.__name__} single run.",
                    minimum_verbosity=3,
                    verbosity=self.verbosity,
                )
                return self.run_single(**scheduled_io, **kwargs)
            case _:
                logger.error(
                    f"correct_runner: {correct_runner} did not match any run implementation."
                )

    def link_additional_args(self, **kwargs) -> str:
        """
        Link the additional arguments given to kwargs. Packs kwargs automatically in strings.

        :return: Additional arguments
        :rtype: str
        """
        additional_args = (
            kwargs.pop("additional_args") if "additional_args" in kwargs else self.additional_args
        )

        additional_args = " ".join(
            filter(
                None,
                [
                    " ".join(additional_args),
                    " ".join(
                        [" ".join([f"--{key}", f'"{value}"']) for key, value in kwargs.items()]
                    ),
                ],
            )
        )

        return additional_args

    # RUN
    def run(
        self,
        in_outs: list[dict] = [],
        out_folder: StrPath = "pipe_step_out",
        standard_in: str = "standard",
        **kwargs,
    ) -> list[dict]:
        """
        Run the instance step with the given in_paths and out_paths. Constructs a new out_target_folder for each directory, if given.

        :param in_outs: Dicitionary with "in" and "out", containing dictionaries with i/o information
        :type in_outs: list[dict]
        :param kwargs: Dictionary of additional arguments for computation
        :type kwargs: ...
        :return: Output that was processed
        :rtype: list[dict]
        """
        logger.log(
            message=f"Started {self.__class__.__name__} step",
            minimum_verbosity=1,
            verbosity=self.verbosity,
        )

        # Extend scheduled paths
        self.scheduled_ios = extend_list(self.scheduled_ios, in_outs)

        # Handle empty output paths by choosing input directory as base
        for scheduled_io in self.scheduled_ios:
            if "out_path" not in scheduled_io:
                if standard_in in scheduled_io["in_paths"]:
                    standard_in_paths = self.extract_standard(
                        standard_in, in_paths=scheduled_io["in_paths"]
                    )[0]
                else:
                    standard_in_paths = next(filter(None, flatten_values(scheduled_io["in_paths"])))
                scheduled_io["out_path"] = {
                    "standard": os.path.abspath(
                        os.path.join(get_directory(standard_in_paths), "..", out_folder)
                    )
                }

        # Loop over all in/out combinations
        for scheduled_io in self.scheduled_ios:
            # Skip already processed files/folders
            if scheduled_io in self.processed_ios and not self.overwrite:
                continue

            logger.log(
                message=f'Processing {scheduled_io["in_paths"]} -> {scheduled_io["out_path"]}',
                minimum_verbosity=2,
                verbosity=self.verbosity,
            )

            self.distribute_scheduled(
                correct_runner=scheduled_io.get("run_style", None), kwargs=kwargs, **scheduled_io
            )

            logger.log(
                message=f'Processed {scheduled_io["in_paths"]} -> {scheduled_io["out_path"]}',
                minimum_verbosity=2,
                verbosity=self.verbosity,
            )

        # Compute futures
        if self.futures:
            self.compute_futures()

        # Clear schedules
        self.scheduled_ios = []

        logger.log(
            message=f"Finished {self.__class__.__name__} step",
            minimum_verbosity=1,
            verbosity=self.verbosity,
        )

        return self.processed_ios
