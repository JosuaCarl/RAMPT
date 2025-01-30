import os
import io
from os.path import join
import shutil
import warnings

from datetime import datetime

import requests
import hashlib
import tarfile
import zipfile

from pathlib import Path

import platform as pf

import subprocess

import webbrowser

import tkinter as tk
from tkinter import filedialog
from tkinter.ttk import Frame, Label, Button, Checkbutton, Progressbar, Scrollbar


project_license = """
This is free and unencumbered software released into the public domain.

Anyone is free to copy, modify, publish, use, compile, sell, or distribute this software, either in source code form or as a compiled binary, for any purpose, commercial or non-commercial, and by any means.

In jurisdictions that recognize copyright laws, the author or authors of this software dedicate any and all copyright interest in the software to the public domain. We make this dedication for the benefit of the public at large and to the detriment of our heirs and successors. We intend this dedication to be an overt act of relinquishment in perpetuity of all present and future rights to this software under copyright law.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""


class Logger:
    def __init__(self, log_file_path: str):
        self.out = ""
        self.err = ""
        self.log_file_path = log_file_path
        self.log(f"Saving log file to {log_file_path}")

    def get_now(self) -> str:
        return str(datetime.now().replace(microsecond=0))

    def log(self, message: str, log_file_path: str = None):
        message = f"[{self.get_now()}][rampt_install][INFO]\t{message}"
        print(message)
        self.out += message
        self.write_log_file(message, log_file_path=log_file_path)

    def warn(self, message: str, log_file_path: str = None):
        message = f"[{self.get_now()}][rampt_install][WARNING]\t{message}"
        warnings.warn(UserWarning(message))
        self.err += message
        self.write_log_file(message, log_file_path=log_file_path)

    def error(self, error, log_file_path: str = None):
        message = f"[{self.get_now()}][rampt_install][ERROR]\t{str(error)}"
        print(message)
        self.err += message
        self.write_log_file(message, log_file_path=log_file_path)
        raise error

    def execute_command(
        self, cmd: str | list, wait: bool = True, text: bool = True, shell: bool = False, **kwargs
    ) -> subprocess.Popen:
        """
        Execute a command with the adequate verbosity.

        :param cmd: Command as a string or list
        :type cmd: str|list
        :return: Stdout, Stderr
        :rtype: tuple[str,str]
        """
        self.log(f"Starting command: {cmd}")
        process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=text, shell=shell, **kwargs
        )

        if wait:
            process.wait()

        out = process.stdout.read()
        err = process.stderr.read()

        if not text:
            out, err = (out.decode(), err.decode())

        self.out += out
        self.err += err

        self.write_log_file("\n" + out + "\n" + err)

        self.log(f"Command {cmd} finished.")

        return process

    def write_log_file(self, output: str, log_file_path: str = None):
        if not log_file_path:
            log_file_path = self.log_file_path
        with open(log_file_path, "a") as log_file:
            log_file.write("\n" + output)


rampt_user_path = os.path.abspath(os.path.join(Path.home(), ".rampt"))
os.makedirs(rampt_user_path, exist_ok=True)
log_file_path = os.path.normpath(os.path.join(rampt_user_path, "rampt_installer_log.txt"))
logger = Logger(log_file_path)


# PATH CHECKING
def tool_available(executable: str | list) -> str:
    """
    Tool can be accessed in environment.
    """
    if isinstance(executable, str):
        which = shutil.which(executable)
        if which:
            logger.log(f"Tool {executable} already available.")
        return which
    if isinstance(executable, list):
        whiches = [shutil.which(exe) for exe in executable]
        if any(whiches):
            logger.log(f"Tool {executable} already available.")
            return whiches
        else:
            return None
    else:
        return None


def is_in_path(directory_or_program: str) -> bool:
    """
    Check if a directory or program is in the PATH environment variable.

    :param directory_or_program: Directory, that should be a direct entry in PATH, or program, that should be resolved by PATH.
    :type directory_or_program: StrPath
    :return: Whether it is on PATH
    :rtype: bool
    """
    # Get the PATH environment variable
    path_dirs = os.environ.get("PATH", "").split(os.pathsep)

    # Normalize the input path
    target = Path(directory_or_program).resolve()

    on_path = False
    # Check if it's a directory
    if target.is_dir():
        on_path = any(Path(p).resolve() == target for p in path_dirs)

    # Check if it's a program (file in any PATH directory)
    if target.is_file():
        on_path = any((Path(p) / target.name).is_file() for p in path_dirs)

    if on_path:
        logger.log(f"{directory_or_program} is already on PATH")

    return on_path


# PATH APPENDING
def add_to_local_path(new_path: str):
    current_path = os.environ.get("PATH", "")
    os.environ["PATH"] = f"{current_path}{os.pathsep}{new_path}"
    logger.log(f"Linked {new_path} to local python environment.")


def add_to_path(op_sys: str, path: str, local_only: bool = False):
    if not local_only and not is_in_path(path):
        exported_to_path = False
        if "windows" in op_sys:
            current_path = os.environ.get("PATH", "")
            if str(path) not in current_path:
                logger.execute_command(["setx", "PATH", f"{path};{current_path}"], wait=True)
            exported_to_path = True
        else:
            for shell_profile in [
                ".profile",
                ".bashrc",
                ".zshrc",
                os.path.join(".config", "fish", "config.fish"),
                "~/.cshrc",
                "~/.tcshrc",
            ]:
                shell_profile = Path.home() / shell_profile
                if shell_profile.exists():
                    export_line = f'export PATH="{path}:$PATH"'
                    with shell_profile.open("a") as file:
                        file.write(f"\n# Ensure {path} is on PATH\n{export_line}\n")
                    exported_to_path = True
                    logger.log(f"Added {path} to PATH in {shell_profile}")
        if not exported_to_path:
            logger.warn(
                "No shell rc was found to export ~/.local/bin to PATH. You might have to do it yourself."
            )
    add_to_local_path(path)


# PROGRAM INSTALLATION
def calculate_file_hash(file: str | io.BufferedReader, hashing_algorithm: str = "sha256"):
    if isinstance(file, str):
        file = open(file, "rb")

    # Read the file in 64KB chunks to efficiently handle large files.
    hasher = hashlib.new(name=hashing_algorithm)
    data = True
    while data:
        data = file.read(65536)
        hasher.update(data)

    file.close()
    return hasher.hexdigest()


def verify_hash(downloaded_file: str | io.BufferedReader, expected_hash: str):
    calculated_hash = calculate_file_hash(downloaded_file)
    return calculated_hash == expected_hash


def download_extract(
    url: str, target_path: str, expected_hash: str = None, extraction_method: str = "zip"
):
    """
    Download a compressed file and extract its contents to target_path.
    """
    response = requests.get(url)
    if expected_hash is None or verify_hash(io.BytesIO(response.content), expected_hash):
        if "zip" in extraction_method:
            with zipfile.ZipFile(io.BytesIO(response.content)) as zip_file:
                zip_file.extractall(path=target_path)
        elif "tar.bz2" in extraction_method:
            with tarfile.open(fileobj=io.BytesIO(response.content)) as tar_file:
                tar_file.extractall(target_path)
    else:
        logger.error(ValueError("Wrong hashing value of file."))


# LINK PROGRAM
def create_symlink(target_file, symlink_path):
    """
    Create a symbolic link pointing to the target file.

    :param target_file: The path to the file to be linked to (the target).
    :param symlink_path: The path for the symbolic link to be created.
    """
    if os.path.exists(symlink_path):
        if os.path.islink(symlink_path):
            os.remove(symlink_path)
        else:
            logger.error(
                Exception(f"{symlink_path} leads to a directory or file that is no symbolic link.")
            )
    os.symlink(target_file, symlink_path)
    logger.log(f"Symbolic link created: {symlink_path} -> {target_file}")


def create_shortcut_windows(
    shortcut_script_path: str, target_path: str, shortcut_path: str, icon_path: str
):
    if not os.path.isfile(shortcut_script_path):
        shortcut_script = (
            r'set SCRIPT="%TEMP%\%RANDOM%-%RANDOM%-%RANDOM%-%RANDOM%.vbs"'
            + "\n"
            + 'echo Set oWS = WScript.CreateObject("WScript.Shell") >> %SCRIPT%'
            + "\n"
            + f'echo sLinkFile = "{shortcut_path}" >> %SCRIPT%'
            + "\n"
            + "echo Set oLink = oWS.CreateShortcut(sLinkFile) >> %SCRIPT%"
            + "\n"
            + f'echo oLink.TargetPath = "{target_path}" >> %SCRIPT%'
            + "\n"
            + f'echo oLink.IconLocation = "{icon_path}" >> %SCRIPT%'
            + "\n"
            + "echo oLink.Save >> %SCRIPT%"
            + "\n"
            + "cscript /nologo %SCRIPT%"
            + "\n"
            + "del %SCRIPT%"
        )
        with open(shortcut_script_path, "w") as file:
            file.write(shortcut_script)

    logger.execute_command([shortcut_script_path])
    logger.log(f"Shortcut created: {shortcut_path} -> {target_path}")


def link_rampt(
    op_sys: str,
    program_path: str,
    name: str,
    out_folder: str = join(Path.home(), ".local", "bin"),
    local_only: bool = False,
):
    os.makedirs(out_folder, exist_ok=True)
    if "windows" in op_sys:
        shortcut_script_path = os.path.normpath(
            join(program_path, "..", "statics", "make_shortcut.bat")
        )
        icon_path = os.path.normpath(join(program_path, "..", "statics", "share", "rampt.ico"))
        shortcut_path = join(out_folder, f"{name}.lnk")
        create_shortcut_windows(
            shortcut_script_path=shortcut_script_path,
            target_path=program_path,
            shortcut_path=shortcut_path,
            icon_path=icon_path,
        )
    else:
        symlink_path = os.path.join(out_folder, name)
        create_symlink(target_file=program_path, symlink_path=symlink_path)
    add_to_path(op_sys=op_sys, path=out_folder, local_only=local_only)


class InstallerApp(tk.Tk):
    def __init__(self, root, local_only: bool = False, show_progress: bool = True):
        self.local_only = local_only
        self.op_sys = pf.system().lower()

        if "mac" in self.op_sys:
            standard_install_path = "/Application/"
        elif "windows" in self.op_sys:
            standard_install_path = Path.home()
        else:
            standard_install_path = os.path.join(str(Path.home()), "programs")

        self.primary_progressbar = None
        self.install_status = None

        self.install_path = standard_install_path
        self.license = project_license
        self.name = "rampt"
        self.urls = {
            "MSconvert": {
                "win64": "https://mc-tca-01.s3.us-west-2.amazonaws.com/ProteoWizard/bt83/3360938/pwiz-bin-windows-x86_64-vc143-release-3_0_25029_b4f97eb.tar.bz2",
                "win32": "https://mc-tca-01.s3.us-west-2.amazonaws.com/ProteoWizard/bt36/2440017/pwiz-bin-windows-x86-vc143-release-3_0_23129_dfd6c0a.tar.bz2",
                "mac": None,
                "linux": "https://mc-tca-01.s3.us-west-2.amazonaws.com/ProteoWizard/bt17/3362588/pwiz-bin-linux-x86_64-gcc7-release-3_0_25030_b4f97eb.tar.bz2",
            },
            "MZmine": {
                "win64": "https://github.com/mzmine/mzmine/releases/download/v4.5.0/mzmine_Windows_portable-4.5.0.zip",
                "win32": "https://github.com/mzmine/mzmine/releases/download/v4.5.0/mzmine_Windows_portable-4.5.0.zip",
                "mac": "https://github.com/mzmine/mzmine/releases/download/v4.5.0/mzmine_macOS_portable_academia-4.5.0.zip",
                "linux": "https://github.com/mzmine/mzmine/releases/download/v4.5.0/mzmine_Linux_portable-4.5.0.zip",
            },
            "Sirius": {
                "win64": "https://github.com/sirius-ms/sirius/releases/download/v6.1.1/sirius-6.1.1-win-x64.zip",
                "win32": "https://github.com/sirius-ms/sirius/releases/download/v6.1.1/sirius-6.1.1-win-x64.zip",
                "mac": "https://github.com/sirius-ms/sirius/releases/download/v6.1.1/sirius-6.1.1-macos-x64.zip",
                "linux": "https://github.com/sirius-ms/sirius/releases/download/v6.1.1/sirius-6.1.1-linux-x64.zip",
            },
        }

        ## TKINTER stuff
        self.root = root

        self.root.title("Installer")
        self.root.geometry("600x400")
        # Initialize variables
        self.current_page = 0

        self.install_path = tk.StringVar(value=self.install_path)  # Default installation directory

        self.accept_var = tk.BooleanVar()
        self.force = tk.BooleanVar()

        self.component_vars = {
            "MSconvert": tk.BooleanVar(value=True),
            "MZmine": tk.BooleanVar(value=True),
            "Sirius": tk.BooleanVar(value=True),
        }

        # List of pages
        self.pages = [
            self.create_component_page,
            self.create_license_page,
            self.create_installation_location_page,
            self.create_installation_page,
        ]

        self.show_progress = show_progress

        # Main frame for dynamic content
        self.main_frame = Frame(root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Navigation buttons
        self.nav_frame = Frame(root)
        self.nav_frame.pack(fill=tk.X, pady=10)

        self.prev_button = Button(
            self.nav_frame, text="Previous", command=self.previous_page, state=tk.DISABLED
        )
        self.prev_button.pack(side=tk.LEFT, padx=5)

        self.next_button = Button(self.nav_frame, text="Next", command=self.next_page)
        self.next_button.pack(side=tk.RIGHT, padx=5)

        # Load the first page
        self.load_page()

    def install_uv(self):
        logger.log("Installing uv")
        if not tool_available("uv"):
            if "windows" in self.op_sys:
                process = logger.execute_command(
                    [
                        "powershell",
                        "-ExecutionPolicy",
                        "ByPass",
                        "-c",
                        "irm https://astral.sh/uv/install.ps1 | iex",
                    ]
                )
            else:
                process = logger.execute_command(
                    ["wget", "-qO-", "https://astral.sh/uv/install.sh"], text=False
                )
                process = logger.execute_command(["sh"], stdin=process.stdout)
        add_to_local_path(join(Path.home(), ".local", "bin"))
        logger.log("Installed uv")

    def install_project(
        self, name: str, url: dict | str, install_path: str, hash_url_addendum: str = None
    ):
        local_bin = os.path.normpath(os.path.join(Path().home(), ".local", "bin"))
        # Hash check
        if hash_url_addendum:
            response = requests.get(url + hash_url_addendum)
            expected_hash = response.content
        else:
            expected_hash = None

        # Download and extraction
        install_path = join(install_path, name)
        download_extract(
            url=url, target_path=install_path, expected_hash=expected_hash, extraction_method="zip"
        )

        # UV action
        self.install_uv()
        logger.execute_command([f"{local_bin}/uv", "sync", "--no-dev"], cwd=install_path)

        if "windows" in self.op_sys:
            python_path = os.path.join(install_path, ".venv", "Scripts", "python")
            path_executable = join(install_path, f"{self.name}.bat")
            execution_script = f'"{python_path}" -m rampt %*'
            with open(path_executable, "w") as file:
                file.write(execution_script)
        else:
            python_path = os.path.join(install_path, ".venv", "bin", "python")
            path_executable = join(install_path, f"{self.name}.sh")
            execution_script = f'#!/usr/bin/sh\n"{python_path}" -m rampt'
            with open(path_executable, "w") as file:
                file.write(execution_script)

        logger.log(f"Python path: {python_path}")
        add_to_path(op_sys=self.op_sys, path=install_path, local_only=self.local_only)

        link_rampt(
            op_sys=self.op_sys,
            program_path=path_executable,
            name=self.name,
            out_folder=local_bin,
            local_only=self.local_only,
        )

        return os.path.abspath(install_path)

    def install_component(
        self,
        name: str,
        urls: dict | str,
        install_path: str,
        bin_paths: str = None,
        extraction_method: str = "zip",
        hash_url_addendum: str = None,
        command: str | list = None,
        force: bool = False,
    ):
        # Check for command availability
        path_to_tool = tool_available(command)

        if command and path_to_tool and not force:
            self.update_secondary_progressbar(
                step_message=f"Checked {name} availability on PATH. Tool already available.",
                install_name=name,
                total_steps=1,
                last_step=False,
            )
            return path_to_tool
        else:
            self.update_secondary_progressbar(
                step_message=f"Checked {name} availability on PATH",
                install_name=name,
                total_steps=4,
                last_step=False,
            )
            if isinstance(urls, dict):
                if "mac" in self.op_sys:
                    url = urls.get("mac")
                elif "windows" in self.op_sys:
                    if "64" in pf.architecture()[0]:
                        url = urls.get("win64")
                    else:
                        url = urls.get("win32")
                else:
                    url = urls.get("linux")
            else:
                url = urls

            # Warning,
            if not url:
                logger.warn(
                    f"{name} is not available for {self.op_sys}."
                    + "To use it, please  find a way to install and add it to PATH yourself."
                )
            self.update_secondary_progressbar(
                step_message=f"Fetched {name} URL",
                install_name=name,
                total_steps=4,
                last_step=False,
            )
            # Hash check
            if hash_url_addendum:
                response = requests.get(url + hash_url_addendum)
                expected_hash = response.content
            else:
                expected_hash = None

            # Download and extraction
            install_path = join(install_path, name)
            download_extract(
                url=url,
                target_path=install_path,
                expected_hash=expected_hash,
                extraction_method=extraction_method,
            )
            self.update_secondary_progressbar(
                step_message=f"Downloaded {name}.",
                install_name=name,
                total_steps=4,
                last_step=False,
            )

            if bin_paths:
                if isinstance(bin_paths, dict):
                    bin_path = bin_paths.get("*", None)
                    bin_paths_matches = [
                        value for key, value in bin_paths.items() if key in self.op_sys
                    ]
                    if bin_paths_matches:
                        bin_path = bin_paths_matches[0]
                else:
                    bin_path = bin_paths
                add_to_path(
                    op_sys=self.op_sys,
                    path=join(install_path, bin_path),
                    local_only=self.local_only,
                )
            self.update_secondary_progressbar(
                step_message=f"Added {name} to PATH.",
                install_name=name,
                total_steps=4,
                last_step=True,
            )

            return os.path.abspath(install_path)

    def install_components(self, components: list, force: bool = False, standalone: bool = False):
        urls = self.urls
        if not standalone:
            components = [self.name] + components
        for i, component in enumerate(components):
            logger.log(f"Installing {component}")
            if self.show_progress:
                self.install_status.insert(tk.END, f"Installing {component}:\n")
            match component:
                case self.name:
                    self.install_project(
                        name=self.name,
                        url="https://github.com/JosuaCarl/RAMPT/releases/latest/download/rampt.zip",
                        install_path=self.install_path,
                    )

                case "MSconvert":
                    self.install_component(
                        name=component,
                        urls=urls.get(component),
                        install_path=self.install_path,
                        extraction_method="tar.bz2",
                        bin_paths="",
                        command="msconvert",
                        force=force,
                    )

                case "MZmine":
                    self.install_component(
                        name=component,
                        urls=urls.get(component),
                        install_path=self.install_path,
                        bin_paths={"windows": "", "*": "bin"},
                        command=["mzmine", "mzmine_console"],
                        force=force,
                    )

                case "Sirius":
                    self.install_component(
                        name=component,
                        urls=urls.get(component),
                        install_path=self.install_path,
                        hash_url_addendum=".sha256",
                        bin_paths=join("sirius", "bin"),
                        command="sirius",
                        force=force,
                    )

            self.update_primary_progress(
                total_installs=len(components), last_iteration=i == len(components) - 1
            )

    # NAVIGATION
    def load_page(self):
        """
        Clears the main frame and loads the current page.
        """
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        self.pages[self.current_page]()

        # Update navigation button states
        self.prev_button.config(
            state=tk.NORMAL
            if self.current_page > 0 and self.current_page < len(self.pages) - 1
            else tk.DISABLED
        )
        self.next_button.config(
            text="Next" if self.current_page < len(self.pages) - 2 else "Install",
            state=tk.NORMAL if self.current_page < len(self.pages) - 1 else tk.DISABLED,
        )
        if self.current_page == len(self.pages) - 1:
            self.install()

    def next_page(self):
        """
        Handles navigation to the next page.
        """
        if self.accept_var.get() or self.current_page != 1:
            self.current_page += 1
            self.load_page()

    def previous_page(self):
        """Handles navigation to the previous page."""
        if self.current_page > 0:
            self.current_page -= 1
            self.load_page()

    # COMPONENTS
    def create_component_page(self):
        """Creates the component selection page."""
        Label(
            self.main_frame,
            text="Select optional components for installation",
            font=("Arial", 14, "bold"),
        ).pack(pady=10)

        Label(
            self.main_frame, text="Licenses of components can be inferred from the README at:"
        ).pack(pady=10, padx=10)
        lisence_label = Label(
            self.main_frame,
            text="https://github.com/JosuaCarl/RAMPT/blob/main/README.md",
            underline=True,
        )
        lisence_label.pack(pady=5, padx=10)
        lisence_label.bind(
            "<Button-1>",
            lambda e: webbrowser.open_new_tab(
                "https://github.com/JosuaCarl/RAMPT/blob/main/README.md"
            ),
        )

        for component, var in self.component_vars.items():
            Checkbutton(self.main_frame, text=component, variable=var).pack(
                anchor="w", padx=20, pady=0
            )

        Label(
            self.main_frame,
            text="If the component is not selected, it should be install by the user and accessible in PATH.",
        ).pack(pady=20)
        Label(
            self.main_frame,
            text="Due to changing URLS (especially for msconvert), success is not guaranteed.",
        ).pack(pady=20)

        Checkbutton(
            self.main_frame,
            text="Reinstall components, if already present ? (Not recommended)",
            variable=self.force,
        ).pack(anchor="w", pady=20, padx=10)

    # LISCENCE
    def change_accept(self):
        if self.accept_var.get():
            self.next_button["state"] = tk.NORMAL
        else:
            self.next_button["state"] = tk.DISABLED

    def create_license_page(self):
        """Creates the license agreement page."""
        Label(self.main_frame, text="License Agreement", font=("Arial", 14, "bold")).pack(pady=10)

        license_text = tk.Text(self.main_frame, height=10, wrap=tk.WORD)
        license_text.insert(tk.END, f"Please read the license agreement.\n\n{self.license}")
        license_text.config(state=tk.DISABLED)
        license_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        Checkbutton(
            self.main_frame,
            text="I accept the license agreement and the licenses of the selected dependencies.",
            variable=self.accept_var,
            command=self.change_accept,
        ).pack(pady=5)

    def create_installation_location_page(self):
        """Creates the installation location selection page."""
        Label(
            self.main_frame, text="Select Installation Location", font=("Arial", 14, "bold")
        ).pack(pady=10)

        # Display current installation directory
        entry = tk.Entry(self.main_frame, textvariable=self.install_path, width=40)
        entry.pack(pady=5, padx=10)

        # Button to browse for a directory
        browse_button = Button(self.main_frame, text="Browse", command=self.browse_directory)
        browse_button.pack(pady=5)

    def browse_directory(self):
        """Opens a file dialog to select the installation directory."""
        directory = filedialog.askdirectory(
            initialdir=self.install_path.get(), title="Select Installation Directory"
        )
        if directory:
            self.install_path.set(directory)

    def update_primary_progress(self, total_installs, last_iteration: bool = False):
        if self.show_progress:
            if self.primary_progressbar:
                self.primary_progressbar["value"] = self.primary_progressbar["value"] + (
                    100 / total_installs
                )
                if last_iteration:
                    self.primary_progressbar["value"] = 100
                    self.install_status.insert(tk.END, "Installation complete. yay!")

    def update_secondary_progressbar(
        self, step_message: str, install_name, total_steps, last_step: bool = False
    ):
        if self.show_progress:
            if self.secondary_progressbar:
                self.secondary_progressbar["value"] = self.secondary_progressbar["value"] + (
                    100 / total_steps
                )
            self.install_status.insert(tk.END, step_message + "\n")
            if last_step:
                self.secondary_progressbar["value"] = 100
                self.install_status.insert(tk.END, f"{install_name} installed.\n")

    def create_installation_page(self):
        Label(self.main_frame, text="Installation", font=("Arial", 14, "bold")).pack(pady=10)
        # Primary progress bar (overall progress)
        Label(root, text="Overall Progress:").pack(pady=(10, 0))
        self.primary_progressbar = Progressbar(root, length=300, mode="determinate")
        self.primary_progressbar.pack(pady=10)

        Label(root, text="Step Progress:").pack(pady=(10, 0))
        self.secondary_progressbar = Progressbar(root, length=300, mode="determinate")
        self.secondary_progressbar.pack(pady=10)

        frame = Frame(root)
        frame.pack(pady=10, fill=tk.BOTH, expand=True)

        # Scrollbar
        self.install_scrollbar = Scrollbar(frame, orient=tk.VERTICAL)

        # Scrollable text field
        self.install_status = tk.Text(
            frame, wrap=tk.WORD, yscrollcommand=self.install_scrollbar.set, height=10, width=40
        )
        self.install_status.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Configure scrollbar to work with text field
        self.install_scrollbar.config(command=self.install_status.yview)
        self.install_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def install(self):
        """Final installation process."""
        logger.log("Starting installation")
        self.install_status.insert(tk.END, "Starting installation:\n")

        selected_components = [name for name, var in self.component_vars.items() if var.get()]
        self.install_path = self.install_path.get()

        self.install_components(components=selected_components)
        logger.log("All done")


# Run the application
if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = InstallerApp(root)
        root.mainloop()
    except Exception as e:
        logger.error(e)
