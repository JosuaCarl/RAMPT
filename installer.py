#!/usr/bin/env python3
"""
Setup an installation of mine2sirius.
"""

import io
import shutil
import requests

import zipfile
import tarfile

import hashlib
import platform

import tkinter as tk

from source.helpers.types import StrPath


msconvert_sources = {
	"linux": "https://mc-tca-01.s3.us-west-2.amazonaws.com/ProteoWizard/bt17/3321018/pwiz-bin-linux-x86_64-gcc7-release-3_0_24358_b21b512.tar.bz2",
	"macos": "https://mc-tca-01.s3.us-west-2.amazonaws.com/ProteoWizard/bt17/3321018/pwiz-bin-linux-x86_64-gcc7-release-3_0_24358_b21b512.tar.bz2",
	"windows": "https://mc-tca-01.s3.us-west-2.amazonaws.com/ProteoWizard/bt83/3320358/pwiz-bin-windows-x86_64-vc143-release-3_0_24357_5948bd0.tar.bz2",
}

mzmine_sources = {
	"linux": "https://github.com/mzmine/mzmine/releases/download/v4.4.3/mzmine_Linux_portable-4.4.3.zip",
	"macos": "https://github.com/mzmine/mzmine/releases/download/v4.4.3/mzmine_macOS_portable_academia-4.4.3.zip",
	"windows": "https://github.com/mzmine/mzmine/releases/download/v4.4.3/mzmine_Windows_portable-4.4.3.zip",
}

sirius_source = {
	"linux": "https://github.com/sirius-ms/sirius/releases/download/v6.0.7/sirius-6.0.7-linux64.zip",
	"macos": "https://github.com/sirius-ms/sirius/releases/download/v6.0.7/sirius-6.0.7-osx64.zip",
	"windows": "https://github.com/sirius-ms/sirius/releases/download/v6.0.7/sirius-6.0.7-win64.zip",
}


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


def make_window():
	window = tk.Tk()

	window.geometry("800x500")
	window.title("mine2sirius installer")

	window

	window.mainloop()


def main():
	# TODO: TKinter installer (ask for installation + give LISENCES)
	install_msconvert = False
	# msconvert_outpath = ".."
	# install_mzmine = False
	# install_sirius = False

	# TODO: Install 3rd party dependencies
	system = platform.system()
	match system.lower():
		case "windows":
			pass
		case "macos":
			pass
		case "linux":
			if install_msconvert and not tool_available(executable="msconvert"):
				download_extract(msconvert_sources)
		case _:
			raise (
				SystemError(
					f"System {system} not known. Only Windows, MacOS and Linux are supported."
				)
			)

	# TODO: Install python dependencies


if __name__ == "__main__":
	main()
