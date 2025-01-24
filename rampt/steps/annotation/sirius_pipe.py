#!/usr/bin/env python3

"""
Use Sirius to annotate compounds and extract matching formulae and chemical classes.
"""

# Imports
import os
import argparse

from os.path import join

from ..general import *


def main(args: argparse.Namespace | dict, unknown_args: list[str] = []):
    """
    Execute the conversion.

    :param args: Command line arguments
    :type args: argparse.Namespace|dict
    :param unknown_args: Command line arguments that are not known.
    :type unknown_args: list[str]
    """
    # Extract arguments
    exec_path = get_value(args, "exec_path", "sirius")
    in_dir = get_value(args, "in_dir")
    out_dir = get_value(args, "out_dir", in_dir)
    projectspace = get_value(args, "projectspace", out_dir)
    config = get_value(args, "config", None)
    nested = get_value(args, "nested", False)
    n_workers = get_value(args, "workers", 1)
    save_log = get_value(args, "save_log", False)
    verbosity = get_value(args, "verbosity", 1)
    additional_args = get_value(args, "sirius_args", unknown_args)
    additional_args = additional_args if additional_args else unknown_args

    sirius_runner = Sirius_Runner(
        exec_path=exec_path,
        config=config,
        save_log=save_log,
        additional_args=additional_args,
        verbosity=verbosity,
        nested=nested,
        workers=n_workers,
    )
    sirius_runner.scheduled_ios = {
        "in_path": {"standard": in_dir},
        "out_path": {"standard": out_dir},
    }
    return sirius_runner.run(projectspace=projectspace)


class Sirius_Runner(Pipe_Step):
    """
    A runner for SIRIUS annotation.
    """

    def __init__(
        self,
        exec_path: StrPath = "sirius",
        config: StrPath = "",
        projectspace: StrPath = None,
        save_log: bool = False,
        additional_args: list = [],
        verbosity: int = 1,
        **kwargs,
    ):
        """
        Initialize the Sirius_Runner. To use this, you must have logged in in the Sirius GUI.

        :param exec_path: Path to SIRIUS executable, defaults to "sirius"
        :type exec_path: StrPath
        :param config: Path to SIRIS configuration file or direct configuration string, defaults to "config.txt"
        :type config: StrPath
        :param projectspace: Path to SIRIUS projectspace, defaults to None
        :type projectspace: StrPath
        :param save_log: Whether to save the output(s).
        :type save_log: bool, optional
        :param additional_args: Additional arguments for mzmine, defaults to []
        :type additional_args: list, optional
        :param verbosity: Level of verbosity, defaults to 1
        :type verbosity: int, optional
        """
        super().__init__(
            patterns={"in": r".*_sirius\.mgf$", "config": r"sirius_config\.txt"},
            save_log=save_log,
            additional_args=additional_args,
            verbosity=verbosity,
        )
        if kwargs:
            self.update(kwargs)
        self.exec_path = exec_path if exec_path else "sirius"
        self.config = self.extract_config(config)
        self.projectspace = projectspace
        self.name = "sirius"

    def extract_config(self, config: StrPath):
        if os.path.isdir(config):
            if os.path.isfile(join(config, "sirius_config.txt")):
                config = join(config, "sirius_config.txt")
            else:
                logger.error(
                    message=f"{config} directory does not contain sirius_config.txt",
                    error_type=ValueError,
                )
        if os.path.isfile(config):
            with open(config, "r") as config_file:
                config = config_file.read()
            config = config[6:] if config.startswith("config") else config
        return config.strip()

    # Distribution
    def distribute_scheduled(self, **scheduled_io):
        return super().distribute_scheduled(**scheduled_io)

    # RUN
    def run_single(
        self,
        in_path: dict[str, StrPath],
        out_path: dict[str, StrPath],
        projectspace: dict[str, StrPath] = None,
        config: dict[str, StrPath] = None,
        **kwargs,
    ) -> bool:
        """
        Run a single SIRIUS configuration.

        :param in_path: Path to in file
        :type in_path: dict[str, StrPath]
        :param out_path: Output directory
        :type out_path: dict[str, StrPath]
        :param projectspace: Path to projectspace file / directory, defaults to out_path
        :type projectspace: dict[str, StrPath]
        :param config: Path to configuration file / directory or configuration as string, defaults to None
        :type config: dict[str, StrPath], optional
        :return: Success of the command
        :rtype: bool
        """
        in_path, out_path, projectspace, config = self.extract_standard(
            in_path=in_path, out_path=out_path, projectspace=projectspace, config=config
        )
        additional_args = self.link_additional_args(**kwargs)

        if projectspace is None:
            projectspace = self.projectspace if self.projectspace else out_path
        if config is None:
            config = self.config
        config = self.extract_config(config=config)

        cmd = (
            rf'"{self.exec_path}" --project "{join(projectspace, "projectspace.sirius")}" --input "{in_path}" '
            + rf'config {config} write-summaries --output "{out_path}" {additional_args}'
        )

        self.compute(
            step_function=execute_verbose_command,
            in_out=dict(in_path=in_path, out_path=out_path),
            log_path=self.get_log_path(out_path=out_path),
            cmd=cmd,
            verbosity=self.verbosity,
            decode_text=False,
        )

    def run_directory(
        self,
        in_path: dict[str, StrPath],
        out_path: dict[str, StrPath],
        projectspace: StrPath = None,
        config: str = None,
        **kwargs,
    ):
        """
        Compute a sirius run on a folder. When no config is defined, it will search in the folder for config.txt.

        :param in_dir: Path to in folder
        :type in_dir: StrPath
        :param out_dir: Output directory
        :type out_dir: StrPath
        :param projectspace: Path to projectspace file / directory, defaults to out_path
        :type projectspace: StrPath
        :param config: Configuration (file), defaults to None
        :type config: StrPath, optional
        """
        in_path, out_path, projectspace, config = self.extract_standard(
            in_path=in_path, out_path=out_path, projectspace=projectspace, config=config
        )

        # Search for config present in folder
        if config is None and self.config is None:
            for entry in os.listdir(in_path):
                if self.match_path(pattern=self.patterns["config"], path=entry):
                    config = join(in_path, entry)

        # Search for relevant files
        for entry in os.listdir(in_path):
            if self.match_path(pattern=self.patterns["in"], path=entry):
                os.makedirs(out_path, exist_ok=True)
                self.run_single(
                    in_path=join(in_path, entry),
                    out_path=out_path,
                    projectspace=projectspace,
                    config=config,
                    **kwargs,
                )

    def run_nested(
        self,
        in_path: dict[str, StrPath],
        out_path: dict[str, StrPath],
        recusion_level: int = 0,
        **kwargs,
    ):
        """
        Run SIRIUS Pipeline in nested directories.

        :param in_path: Root input directory
        :type in_path: dict[str, StrPath]
        :param out_path: Root output directory
        :type out_path: dict[str, StrPath]
        :param recusion_level: Current level of recursion, important for determination of level of verbose output, defaults to 0
        :type recusion_level: int, optional
        """
        in_path, out_path = self.extract_standard(in_path=in_path, out_path=out_path)

        root, dirs, files = next(os.walk(in_path))

        for file in files:
            if self.match_path(pattern=self.patterns["in"], path=file):
                self.run_directory(in_path=in_path, out_path=out_path, **kwargs)

        for dir in dirs:
            self.run_nested(
                in_path=join(in_path, dir),
                out_path=join(out_path, dir),
                recusion_level=recusion_level + 1,
                **kwargs,
            )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="sirius_pipe.py",
        description="Obtain anntations from MS1 & MS2 feature annotation by SIRIUS.",
    )
    parser.add_argument("-si", "--exec_path", required=False)
    parser.add_argument("-in", "--in_dir", required=True)
    parser.add_argument("-out", "--out_dir", required=False)
    parser.add_argument("-p", "--projectspace", required=True)
    parser.add_argument("-c", "--config", required=False)
    parser.add_argument("-n", "--nested", required=False, action="store_true")
    parser.add_argument("-s", "--save_log", required=False, action="store_true")
    parser.add_argument("-w", "--workers", required=False, type=int)
    parser.add_argument("-v", "--verbosity", required=False, type=int)
    parser.add_argument("-sirius", "--sirius_args", required=False, nargs=argparse.REMAINDER)

    args, unknown_args = parser.parse_known_args()

    main(args=args, unknown_args=unknown_args)
