#!/usr/bin/env python3
"""
Setup an installation of project.
"""

import sys
import os
from os.path import join
import warnings
import io
import shutil
import requests

from threading import Thread

import zipfile
import tarfile

import hashlib
import platform

import tkinter as tk
from tkinter import filedialog
from tkinter.ttk import Frame, Label, Button, Checkbutton, Progressbar


from rampt.helpers.types import StrPath


import toml

import platform as pf


op_sys = pf.system().lower()

if "mac" in op_sys:
	standard_installation_path = "/Application/"
elif "windows" in op_sys:
	standard_installation_path = os.getenv("ProgramFiles")
	standard_installation_path = os.getenv("ProgramFiles")
else:
	standard_installation_path = "/usr/local/lib"
	link_path = "/usr/local/bin"

sys.path.append(join(".."))

with open("LICENSE.txt") as license_file:
	license = license_file.read()

with open("pyproject.toml") as project_file:
	project = toml.load(project_file)["project"]


def create_symlink(target_file, symlink_path):
	"""
	Create a symbolic link pointing to the target file.

	:param target_file: The path to the file to be linked to (the target).
	:param symlink_path: The path for the symbolic link to be created.
	"""
	try:
		# Create the symbolic link
		os.symlink(target_file, symlink_path)
		print(f"Symbolic link created: {symlink_path} -> {target_file}")
	except FileExistsError:
		print(f"Error: The file '{symlink_path}' already exists. Cancelling.")
	except OSError as e:
		print(f"Error creating symbolic link: {e}")


def tool_available(executable: str) -> bool:
	"""
	Check whether `name` is on PATH.
	"""
	return shutil.which(executable) is not None


def calculate_file_hash(file: StrPath | io.BufferedReader, hashing_algorithm: str = "sha256"):
	if isinstance(file, StrPath):
		file = open(file, "rb")

	# Read the file in 64KB chunks to efficiently handle large files.
	hasher = hashlib.new(name=hashing_algorithm)
	data = True
	while data:
		data = file.read(65536)
		hasher.update(data)

	file.close()
	return hasher.hexdigest()


def verify_hash(downloaded_file: StrPath | io.BufferedReader, expected_hash: str):
	calculated_hash = calculate_file_hash(downloaded_file)
	return calculated_hash == expected_hash


def download_extract(
	url: str, target_path: StrPath, expected_hash: str = None, extraction_method: str = "zip"
):
	"""
	Download a compressed file and extract its contents to target_path.
	"""
	response = requests.get(url)
	if expected_hash is None or verify_hash(io.BytesIO(response.content), expected_hash):
		match extraction_method:
			case "zip":
				with zipfile.ZipFile(io.BytesIO(response.content)) as zip_file:
					zip_file.extractall(path=target_path)
			case "tar.bz2":
				with tarfile.open(fileobj=io.BytesIO(response.content)) as tar_file:
					tar_file.extractall(target_path)
	else:
		raise (ValueError("Wrong hashing value of file."))


class InstallerApp(tk.Tk):
	def __init__(self, root):
		self.root = root

		self.root.title("Installer")
		self.root.geometry("600x400")
		# Initialize variables
		self.current_page = 0

		self.install_dir = tk.StringVar(
			value=join(standard_installation_path, project["name"])
		)  # Default installation directory

		self.accept_var = tk.BooleanVar()
		self.force = tk.BooleanVar()

		self.component_vars = {
			"MSconvert": tk.BooleanVar(value=True),
			"MZmine": tk.BooleanVar(value=False),
			"SIRIUS": tk.BooleanVar(value=False),
		}

		# List of pages
		self.pages = [
			self.create_license_page,
			self.create_component_page,
			self.create_installation_location_page,
		]

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

	def load_page(self):
		"""
		Clears the main frame and loads the current page.
		"""
		for widget in self.main_frame.winfo_children():
			widget.destroy()
		self.pages[self.current_page]()

		# Update navigation button states
		self.prev_button.config(state=tk.NORMAL if self.current_page > 0 else tk.DISABLED)
		self.next_button.config(
			text="Install" if self.current_page == len(self.pages) - 1 else "Next"
		)

	def next_page(self):
		"""
		Handles navigation to the next page.
		"""
		if self.current_page == 0 and self.accept_var.get() or self.current_page > 0:
			if self.current_page < len(self.pages) - 1:
				self.current_page += 1
				self.load_page()
			else:
				self.install()

	def previous_page(self):
		"""Handles navigation to the previous page."""
		if self.current_page > 0:
			self.current_page -= 1
			self.load_page()

	def change_accept(self):
		if self.accept_var.get():
			self.next_button["state"] = tk.NORMAL
		else:
			self.next_button["state"] = tk.DISABLED

	def create_license_page(self):
		"""Creates the license agreement page."""
		Label(self.main_frame, text="License Agreement", font=("Arial", 14, "bold")).pack(pady=10)

		license_text = tk.Text(self.main_frame, height=10, wrap=tk.WORD)
		license_text.insert(tk.END, f"Please read the license agreement.\n\n{license}")
		license_text.config(state=tk.DISABLED)
		license_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

		Checkbutton(
			self.main_frame,
			text="I accept the license agreement",
			variable=self.accept_var,
			command=self.change_accept,
		).pack(pady=5)

	def create_component_page(self):
		"""Creates the component selection page."""
		Label(
			self.main_frame,
			text="Select optional components for installation",
			font=("Arial", 14, "bold"),
		).pack(pady=10)

		for component, var in self.component_vars.items():
			Checkbutton(self.main_frame, text=component, variable=var).pack(anchor="w", padx=20)

		Label(
			self.main_frame,
			text="If the component is not selected, it should be install by the user and accessible in PATH.",
			font=("Arial", 14, "bold"),
		).pack(pady=10)

		Checkbutton(
			self.main_frame, text="Force installation of components", variable=self.force
		).pack(anchor="w", pady=20)

	def create_installation_location_page(self):
		"""Creates the installation location selection page."""
		Label(
			self.main_frame, text="Select Installation Location", font=("Arial", 14, "bold")
		).pack(pady=10)

		# Display current installation directory
		entry = tk.Entry(self.main_frame, textvariable=self.install_dir, width=40)
		entry.pack(pady=5, padx=10)

		# Button to browse for a directory
		browse_button = Button(self.main_frame, text="Browse", command=self.browse_directory)
		browse_button.pack(pady=5)

	def browse_directory(self):
		"""Opens a file dialog to select the installation directory."""
		directory = filedialog.askdirectory(
			initialdir=self.install_dir.get(), title="Select Installation Directory"
		)
		if directory:
			self.install_dir.set(join(directory, project["name"]))

	def install_component(self, name: str, command: str, urls: dict, hash_url_addendum: StrPath):
		# Check for
		if not tool_available(command) or self.force.get():
			if "mac" in op_sys:
				url = urls.get("mac")
			elif "windows" in op_sys:
				if "64" in pf.architecture()[0]:
					url = urls.get("win64")
				else:
					url = urls.get("win32")
			else:
				url = urls.get("linux")

			# Warning,
			if not url:
				warnings.warn(
					UserWarning(
						f"{name} is not available for {op_sys}. Either find a way to install, skip step (may be slower)."
					)
				)

			# Hash check
			if hash_url_addendum:
				response = requests.get(url + hash_url_addendum)
				expected_hash = response.content

			# Download and extraction
			install_path = join(self.install_dir.get(), "msconvert")
			download_extract(
				url=url,
				target_path=install_path,
				expected_hash=expected_hash,
				extraction_method="tar.bz2",
			)

			# TODO: CONTINUE HERE (Linking to PATH or /usr/local/bin)
			link_path = join(self.install_dir.get(), "msconvert")
			link_path

	def install_components(self, components):
		super().__init__()
		# Progress bar
		self.progress_label = tk.Label(self, text="Installing components...")
		self.progress_label.pack(pady=10)

		self.progress = Progressbar(self, orient="horizontal", length=300, mode="determinate")
		self.progress.pack(pady=20)

		# TODO: Add second progress bar for individual progress

		urls = {
			"msconvert": {
				"win64": "https://mc-tca-01.s3.us-west-2.amazonaws.com/ProteoWizard/bt83/3339046/pwiz-bin-windows-x86_64-vc143-release-3_0_25011_8ace8f0.tar.bz2",
				"win32": "https://mc-tca-01.s3.us-west-2.amazonaws.com/ProteoWizard/bt36/2440017/pwiz-bin-windows-x86-vc143-release-3_0_23129_dfd6c0a.tar.bz2",
				"mac": None,
				"linux": "https://mc-tca-01.s3.us-west-2.amazonaws.com/ProteoWizard/bt17/3339048/pwiz-bin-linux-x86_64-gcc7-release-3_0_25011_8ace8f0.tar.bz2",
			},
			"MZmine": {
				"win64": "https://github.com/mzmine/mzmine/releases/download/v4.4.3/mzmine_Windows_portable-4.4.3.zip",
				"win32": "https://github.com/mzmine/mzmine/releases/download/v4.4.3/mzmine_Windows_portable-4.4.3.zip",
				"mac": "https://github.com/mzmine/mzmine/releases/download/v4.4.3/mzmine_macOS_portable_academia-4.4.3.zip",
				"linux": "https://github.com/mzmine/mzmine/releases/download/v4.4.3/mzmine_Linux_portable-4.4.3.zip",
			},
			"SIRIUS": {
				"win64": "https://github.com/sirius-ms/sirius/releases/download/v6.0.7/sirius-6.0.7-win64.zip",
				"win32": "https://github.com/sirius-ms/sirius/releases/download/v6.0.7/sirius-6.0.7-win64.zip",
				"mac": "https://github.com/sirius-ms/sirius/releases/download/v6.0.7/sirius-6.0.7-osx64.zip",
				"linux": "https://github.com/sirius-ms/sirius/releases/download/v6.0.7/sirius-6.0.7-linux64.zip",
			},
		}

		for i, component in enumerate([project.get("name")] + components, 1):
			match component:
				case "MSconvert":
					self.install_component(
						name=component, command="msconvert", urls=urls.get(component)
					)
				case "MZmine":
					self.install_component(
						name="MZmine", command="mzmine", urls=urls.get(component)
					)
				case "SIRIUS":
					self.install_component(
						name="SIRIUS",
						command="sirius",
						urls=urls.get(component),
						hash_url_addendum=".sha256",
					)
				case project.get("Name"):
					pass

			self.progress["value"] = (i / len(components)) * 100
			self.progress_label.config(text=f"Installing {component}...")
			self.update_idletasks()

		self.progress_label.config(text="Installation complete!")

	def install(self):
		"""Final installation process."""
		selected_components = [name for name, var in self.component_vars.items() if var.get()]

		Thread(target=self.install_components, args=selected_components).start()

		self.root.quit()


def main():
	system = platform.system()
	if system.lower() not in ["windows", "macos", "linux"]:
		warnings.warn(
			f"System {system} not known. Only Windows, MacOS and Linux are supported."
			+ "This will result in a linux-like installation attempt."
		)
	root = tk.Tk()
	app = InstallerApp(root)
	app.root.mainloop()


if __name__ == "__main__":
	main()
