#!/usr/bin/env python3

"""
Use mzmine for feature finding.
"""

# Imports
import os
import argparse

from os.path import join
from tqdm.auto import tqdm

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
    valid_formats = get_value(args, "valid_formats", ["mzML", "mzXML", "imzML"])
    user = get_value(args, "user", None)
    nested = get_value(args, "nested", False)
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
        valid_formats=valid_formats,
        save_log=save_log,
        additional_args=additional_args,
        verbosity=verbosity,
        nested=nested,
        scheduled_in=in_dir,
        scheduled_out=out_dir,
    )
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
        super().__init__(
            patterns={"in": rf".*({r'|'.join(valid_formats)})$"},
            save_log=save_log,
            additional_args=additional_args,
            verbosity=verbosity,
        )
        if kwargs:
            self.update(kwargs)
        self.common_execs = ["mzmine", "mzmine.exe", "mzmine_console"]
        self.exec_path = self.check_execs(exec_path=exec_path)
        self.batch = batch
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
                verbosity=self.verbosity
            )
            self.login = "--login"

    def check_attributes(self):
        if not os.path.isfile(self.batch):
            logger.error(
                message=f"Batch path {self.batch} is no file. Please point to a valid mzbatch file.",
                error_type=ValueError,
            )

    def run_single(self, in_path: StrPath, out_path: StrPath, batch: StrPath = None) -> bool:
        """
        Run a single mzmine batch.

        :param in_path: Path to in files (as a .txt with filepaths or glob string)
        :type in_path: StrPath
        :param out_path: Output directory
        :type out_path: StrPath
        :param out_path: Batch file
        :type out_path: StrPath
        :return: Success of the command
        :rtype: bool
        """
        batch = batch if batch else self.batch

        cmd = rf'"{self.exec_path}" {self.login} --batch "{batch}" --input "{in_path}" --output "{out_path}" {" ".join(self.additional_args)}'

        self.compute(
            step_function=execute_verbose_command,
            in_path=in_path,
            out_path=out_path,
            log_path=self.get_log_path(out_path=out_path),
            cmd=cmd,
            verbosity=self.verbosity,
        )

    def run_directory(self, in_path: StrPath, out_path: StrPath, batch: StrPath = None):
        """
        Compute a single mzmine batch on a folder.

        :param in_path: Path to in folder
        :type in_path: StrPath
        :param out_path: Output directory
        :type out_path: StrPath
        :param batch: Batch file, defaults to None
        :type batch: StrPath, optional
        """
        if not batch:
            for entry in os.listdir(in_path):
                if self.match_file_name(pattern=r".*\.mzbatch$", file_name=entry):
                    batch = join(in_path, entry) if not self.batch else None

        for entry in os.listdir(in_path):
            if self.match_file_name(pattern=self.patterns["in"], file_name=entry):
                self.run_single(in_path=join(in_path, entry), out_path=out_path, batch=batch)

    def run_nested(self, in_root_dir: StrPath, out_root_dir: StrPath, recusion_level: int = 0):
        """
        Run a mzmine batch on a nested structure.

        :param in_root_dir: Root directory for descending the structure
        :type in_root_dir: StrPath
        :param out_root_dir: Root directory for output
        :type out_root_dir: StrPath
        :param recusion_level: Current level of recursion, important for determination of level of verbose output, defaults to 0
        :type recusion_level: int, optional
        """
        verbose_tqdm = self.verbosity >= recusion_level + 2
        made_out_root_dir = False
        found_files = []
        batch = None

        for entry in tqdm(
            os.listdir(in_root_dir), disable=verbose_tqdm, desc="Schedule feature_finding"
        ):
            entry_path = join(in_root_dir, entry)

            if self.match_file_name(pattern=self.patterns["in"], file_name=entry):
                found_files.append(entry_path)
            elif self.match_file_name(pattern=r".*mzbatch$", file_name=entry):
                batch = entry_path if not self.batch else None
            elif os.path.isdir(entry_path):
                self.run_nested(
                    in_root_dir=entry_path,
                    out_root_dir=join(out_root_dir, entry),
                    recusion_level=recusion_level + 1,
                )

        source_paths_file = join(out_root_dir, "source_files.txt")
        if found_files:
            if not made_out_root_dir:
                os.makedirs(out_root_dir, exist_ok=True)
                made_out_root_dir = True
            with open(source_paths_file, "w", encoding="utf8") as f:
                f.write("\n".join(found_files))
            self.run_single(in_path=source_paths_file, out_path=out_root_dir, batch=batch)

    def run(self, in_paths: list = [], out_paths: list = [], batch: StrPath = None, **kwargs):
        return super().run(in_paths=in_paths, out_paths=out_paths, batch=batch, **kwargs)


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
    parser.add_argument("-formats", "--valid_formats", required=False, nargs="+")
    parser.add_argument("-u", "--user", required=False)
    parser.add_argument("-n", "--nested", required=False, action="store_true")
    parser.add_argument("-s", "--save_log", required=False, action="store_true")
    parser.add_argument("-v", "--verbosity", required=False, type=int)
    parser.add_argument("-mzmine", "--mzmine_arguments", required=False, nargs=argparse.REMAINDER)

    args, unknown_args = parser.parse_known_args()

    main(args=args, unknown_args=unknown_args)
