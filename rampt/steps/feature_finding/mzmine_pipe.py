#!/usr/bin/env python3

"""
Use mzmine for feature finding.
"""

# Imports
import os
import argparse
from lxml import etree

from os.path import join

from ..general import *


def main(args: argparse.Namespace | dict, unknown_args: list[str] = []):
    """
    Find features with mzmine.

    :param args: Command line arguments
    :type args: argparse.Namespace|dict
    :param unknown_args: Command line arguments that are not known.
    :type unknown_args: list[str]
    """
    # Extract arguments
    exec_path = get_value(args, "exec_path", None)
    in_dir = get_value(args, "in_dir")
    out_dir = get_value(args, "out_dir")
    batch = get_value(args, "batch")
    user = get_value(args, "user", None)
    nested = get_value(args, "nested", False)
    valid_formats = get_value(args, "valid_formats", ["mzML", "mzXML", "imzML"])
    save_log = get_value(args, "save_log", False)
    verbosity = get_value(args, "verbosity", 1)
    additional_args = get_value(args, "mzmine_arguments", unknown_args)
    additional_args = additional_args if additional_args else unknown_args

    if not exec_path:
        exec_path = r"mzmine"

    mzmine_runner = MZmine_Runner(
        exec_path=exec_path,
        batch=batch,
        user=user,
        save_log=save_log,
        additional_args=additional_args,
        verbosity=verbosity,
        nested=nested,
        valid_formats=valid_formats,
    )
    if nested:
        mzmine_runner.scheduled_ios = {
            "in_paths": {"community_formatted_data_paths": in_dir},
            "out_path": {"processed_data_paths": out_dir},
            "run_style": "nested",
        }
    else:
        mzmine_runner.scheduled_ios = {
            "in_paths": {"community_formatted_data_paths": in_dir},
            "out_path": {"processed_data_paths": out_dir},
        }
    mzmine_runner.run()


class MZmine_Runner(Pipe_Step):
    """
    A runner for mzmine operations. Collects processed files and console outputs/errors.
    """

    def __init__(
        self,
        exec_path: StrPath = "mzmine",
        batch: StrPath = "",
        login: str = "-login",
        user: str = None,
        valid_formats: list = ["mzML", "mzXML", "imzML"],
        save_log: bool = False,
        additional_args: list = [],
        verbosity: int = 1,
        **kwargs,
    ):
        """
        Initialize the MZmine_runner.

        :param exec_path: Path to mzmine executable, defaults to "mzmine"
        :type exec_path: StrPath
        :param batch: Path to mzmine batch file, defaults to ""
        :type batch: StrPath
        :param login: Login or user command, defaults to "-login"
        :type login: str, optional
        :param user: User command, defaults to None
        :type user: str, optional
        :param valid_formats: Formats to search for as valid endings, defaults to ["mzML", "mzXML", "imzML"]
        :type valid_formats: list, optional
        :param save_log: Whether to save the output(s).
        :type save_log: bool, optional
        :param additional_args: Additional arguments for mzmine, defaults to []
        :type additional_args: list, optional
        :param verbosity: Level of verbosity, defaults to 1
        :type verbosity: int, optional
        """
        self.data_ids = {
            "in_paths": ["community_formatted_data_paths"],
            "out_path": ["processed_data_paths"],
            "batch": ["standard"],
            "standard": ["community_formatted_data_paths"],
        }
        super().__init__(
            mandatory_patterns={
                self.data_ids["in_paths"][0]: rf".*\.({r'|'.join(valid_formats)})$",
                "batch": r".*\.mzbatch$",
            },
            patterns={self.data_ids["in_paths"][0]: r".*", "batch": r".*"},
            valid_runs=[
                {
                    "single": {
                        "in_paths": {
                            "community_formatted_data_paths": lambda val: (
                                isinstance(val, list) and all([os.path.isfile(v) for v in val])
                            )
                            or (isinstance(val, str) and os.path.isfile(val))
                        },
                        "out_path": {"processed_data_paths": lambda val: isinstance(val, str)},
                    }
                },
                {
                    "directory": {
                        "in_paths": {
                            "community_formatted_data_paths": lambda val: (
                                isinstance(val, list) and all([os.path.isdir(v) for v in val])
                            )
                            or (isinstance(val, str) and os.path.isdir(val))
                        },
                        "out_path": {"processed_data_paths": lambda val: isinstance(val, str)},
                    }
                },
                {
                    "nested": {
                        "in_paths": {
                            "community_formatted_data_paths": lambda val: (
                                isinstance(val, list) and all([os.path.isdir(v) for v in val])
                            )
                            or (isinstance(val, str) and os.path.isdir(val))
                        },
                        "out_path": {"processed_data_paths": lambda val: isinstance(val, str)},
                    }
                },
            ],
            save_log=save_log,
            additional_args=additional_args,
            verbosity=verbosity,
        )
        if kwargs:
            self.update(kwargs)
        self.common_execs = ["mzmine", "mzmine.exe", "mzmine_console"]
        self.exec_path = self.check_execs(exec_path=exec_path)
        self.batch = batch
        self.batchstep_methods = [
            "io.github.mzmine.modules.io.export_features_gnps.fbmn.GnpsFbmnExportAndSubmitModule",
            "io.github.mzmine.modules.io.export_features_sirius.SiriusExportModule",
            "io.github.mzmine.modules.io.export_features_gnps.fbmn.GnpsFbmnExportAndSubmitModule",
        ]
        self.valid_formats = valid_formats
        self.name = "mzmine"

        # Handle login to mzmine
        if user:
            self.login = f"--user {user}"
        elif "console" in login.lower():
            self.login = "--login-console"
        else:
            logger.log(
                message="You did not provide a user. You will be prompted to login by mzmine.\
                        For future use please find your user file under $USER/.mzmine/users/ after completing the login.",
                minimum_verbosity=2,
                verbosity=self.verbosity,
            )
            self.login = "--login"

    def check_attributes(self):
        if not os.path.isfile(self.batch):
            logger.error(
                message=f"Batch path {self.batch} is no file. Please point to a valid mzbatch file.",
                error_type=ValueError,
            )

    def adjust_batch_out(
        self, batch_path: StrPath, out_batch_path: StrPath = None, batchstep_methods: list[str] = []
    ) -> StrPath:
        """
        Adjust the batch file to integrate with future steps.

        :param batch_path: Path to batch_file
        :type batch_path: StrPath
        :param out_batch_path: Path to out_batch, defaults to None
        :type out_batch_path: StrPath, optional
        :param batchstep_methods: Methods to search for in batchsteps
        :type batchstep_methods: list[str]
        :return: Written batch out file
        :rtype: StrPath
        """
        batchstep_methods = batchstep_methods if batchstep_methods else self.batchstep_methods
        tree = etree.parse(batch_path)
        root = tree.getroot()

        # Change current file name
        for batchstep in root.iter("batchstep"):
            for parameter in batchstep.iter("parameter"):
                if "file" in parameter.attrib["name"].lower():
                    for current_file in parameter.iter("current_file"):
                        if (
                            batchstep.attrib["method"] in batchstep_methods
                            and "Filename" == parameter.attrib["name"]
                        ):
                            current_file.text = ""
                        else:
                            if current_file.text and not os.path.exists(current_file.text):
                                logger.warn(
                                    f"{current_file.text} not found. Please change batch file {batch_path} to contain only local paths."
                                )
                    for file in parameter.iter("file"):
                        if file.text and not os.path.exists(file.text):
                            logger.warn(
                                f"{file.text} not found. Please change batch file {batch_path} to contain only local paths."
                            )
        if not out_batch_path:
            head, tail = os.path.split(batch_path)
            file_name = ".".join(tail.split(".")[:-1])
            out_batch_path = os.path.join(head, f"{file_name}_rampt.mzbatch")

        tree.write(out_batch_path, pretty_print=True)

        return out_batch_path

    def collect_source_files(
        self, files: list, root_path_out: StrPath, root_path_in: StrPath = None
    ) -> list:
        """
        Collect all files in a source_files.txt that match the in_paths regex.

        :param files: List of file names
        :type files: list
        :param root_path_out: Root out path
        :type root_path_out: StrPath
        :param root_path_in: Root in path
        :type root_path_in: StrPath
        :return: List of source paths
        :rtype: list
        """
        source_files = []
        for file in files:
            if self.match_path(pattern=self.data_ids["in_paths"][0], path=file):
                if root_path_in:
                    source_files.append(join(root_path_in, file))
                else:
                    source_files.append(file)

        if source_files:
            os.makedirs(root_path_out, exist_ok=True)
            source_files_path = join(root_path_out, "source_files.txt")
            with open(source_files_path, "w", encoding="utf8") as f:
                f.write("\n".join(source_files))
            return source_files_path
        else:
            return None

    # RUN
    def run_single(
        self,
        in_paths: dict[str, StrPath],
        out_path: dict[str, StrPath],
        batch: dict[str, StrPath] = None,
        **kwargs,
    ):
        """
        Run a single mzmine batch.

        :param in_paths: Path to in files (as a .txt with filepaths or glob string)
        :type in_paths: dict[str, StrPath]
        :param out_path: Output directory
        :type out_path: dict[str, StrPath]
        :param batch: Batch file
        :type batch: dict[str, StrPath]
        """
        in_paths = to_list(get_if_dict(in_paths, self.data_ids["in_paths"]))
        out_path = get_if_dict(out_path, self.data_ids["out_path"])
        batch = get_if_dict(batch, self.data_ids["batch"])
        batch = batch if batch else self.batch
        additional_args = self.link_additional_args(**kwargs)

        if len(in_paths) > 1:
            source_file_path = self.collect_source_files(files=in_paths, root_path_out=out_path)
            in_path = source_file_path
        else:
            in_path = in_paths[0]

        batch = self.adjust_batch_out(batch)

        cmd = rf'"{self.exec_path}" {self.login} --batch "{batch}" --input "{in_path}" --output "{out_path}" {additional_args}'

        log_path = self.get_log_path(out_path=out_path)
        self.compute(
            step_function=execute_verbose_command,
            in_out=dict(
                in_paths={self.data_ids["in_paths"][0]: in_path},
                out_path={self.data_ids["out_path"][0]: out_path, "mzmine_log": log_path},
            ),
            log_path=log_path,
            cmd=cmd,
            verbosity=self.verbosity,
        )

    def run_directory(
        self,
        in_paths: dict[str, StrPath],
        out_path: dict[str, StrPath],
        batch: dict[str, StrPath] = None,
        **kwargs,
    ):
        """
        Compute a single mzmine batch on a folder.

        :param in_paths: Path to in folder
        :type in_paths: dict[str, StrPath]
        :param out_path: Output directory
        :type out_path: dict[str, StrPath]
        :param batch: Batch file, defaults to None
        :type batch: StrPath, optional
        """
        in_paths = to_list(get_if_dict(in_paths, self.data_ids["in_paths"]))
        out_path = get_if_dict(out_path, self.data_ids["out_path"])
        batch = get_if_dict(batch, self.data_ids["batch"])
        batch = batch if batch else self.batch

        ic(in_paths)

        for in_path in in_paths:
            ic(in_path)
            root, dirs, files = next(os.walk(in_path))

            # Look for batch file
            if not batch:
                for file in os.listdir(files):
                    if self.match_path(pattern="batch", path=file):
                        batch = join(in_path, file) if not self.batch else None

            # Collect source files
            source_file_path = self.collect_source_files(
                files=files, root_path_in=in_path, root_path_out=out_path
            )
            if source_file_path:
                self.run_single(in_paths=source_file_path, out_path=out_path, batch=batch)
            else:
                logger.warn(f"No valid files found at {in_path}.")

    def run_nested(
        self,
        in_paths: dict[str, StrPath],
        out_path: dict[str, StrPath],
        recusion_level: int = 0,
        **kwargs,
    ):
        """
        Run a mzmine batch on a nested structure.

        :param in_paths: Root directory for descending the structure
        :type in_paths: dict[str, StrPath]
        :param out_path: Root directory for output
        :type out_path: dict[str, StrPath]
        :param recusion_level: Current level of recursion, important for determination of level of verbose output, defaults to 0
        :type recusion_level: int, optional
        """
        in_paths = to_list(get_if_dict(in_paths, self.data_ids["in_paths"]))
        out_path = get_if_dict(out_path, self.data_ids["out_path"])

        for in_path in in_paths:
            root, dirs, files = next(os.walk(in_path))

            for file in files:
                if self.match_path(pattern=self.data_ids["in_paths"][0], path=file):
                    self.run_directory(in_paths=in_path, out_path=out_path, **kwargs)
                    break

            for dir in dirs:
                self.run_nested(
                    in_paths=join(in_path, dir),
                    out_path=join(out_path, dir),
                    recusion_level=recusion_level + 1,
                    **kwargs,
                )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="mzmine_pipe.py",
        description="Use MZmine batch to process the given spectra.\
                                                   A batch file can be created via the MZmine GUI.",
    )
    parser.add_argument("-mz", "--exec_path", required=False)
    parser.add_argument("-in", "--in_dir", required=True)
    parser.add_argument("-out", "--out_dir", required=True)
    parser.add_argument("-batch", "--batch", required=True)
    parser.add_argument("-u", "--user", required=False)
    parser.add_argument("-n", "--nested", required=False, action="store_true")
    parser.add_argument("-s", "--save_log", required=False, action="store_true")
    parser.add_argument("-v", "--verbosity", required=False, type=int)
    parser.add_argument("-mzmine", "--mzmine_arguments", required=False, nargs=argparse.REMAINDER)

    args, unknown_args = parser.parse_known_args()

    main(args=args, unknown_args=unknown_args)
