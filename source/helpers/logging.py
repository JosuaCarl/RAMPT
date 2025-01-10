#!/usr/bin/env python
"""
Make logging, warnings and error messages more consistent and expressive.
"""

import sys
import warnings
from datetime import datetime
from typing import Callable, Any

from icecream import ic

from source.helpers.types import StrPath


program_name = "m2s"


def get_now() -> str:
	return str(datetime.now().replace(microsecond=0))


def debug_msg(*args, **kwargs):
	"""
	Icecream debugging.
	"""
	ic(*args, **kwargs)


def log(
	message: str = "Info",
	program: str = program_name,
	minimum_verbosity: int = 0,
	verbosity: int = 0,
	*args,
	**kwargs,
):
	"""
	Print a log message.

	:param message: Message, defaults to "Info"
	:type message: str, optional
	:param program: Name of the program to report for, defaults to program_name
	:type program: str, optional
	:param minimum_verbosity: Minimum required verbosity to show message, defaults to 0
	:type minimum_verbosity: int, optional
	:param verbosity: Current verbosity setting, defaults to 0
	:type verbosity: int, optional
	"""
	if verbosity >= minimum_verbosity:
		print(
			f"[{get_now()}][{program}][INFO (V>={minimum_verbosity})]\t{message}", *args, **kwargs
		)


def warn(message: str = "Warning", program: str = program_name, *args, **kwargs):
	"""
	Print a warning.

	:param message: Warning message, defaults to "Warning"
	:type message: str, optional
	:param program: Name of the program to report for, defaults to program_name
	:type program: str, optional
	"""
	warnings.warn(f"[{get_now()}][{program}][WARNING]\t{message}", *args, **kwargs)


def error(
	message: str = "Error",
	error_type=ValueError,
	raise_error: bool = True,
	program: str = program_name,
	*args,
):
	"""
	Pass an error to raise at approporiate place, or raise.

	:param message: Error message, defaults to "Error"
	:type message: str, optional
	:param error_type: Error class
	:type error_type: Error
	:param program: Name of the program to report for, defaults to program_name
	:type program: str, optional
	"""
	if raise_error:
		raise error_type(f"[{get_now()}][{program}][ERROR]\t{message}", *args)
	else:
		return error_type(f"[{get_now()}][{program}][ERROR]\t{message}", *args)


class TeeStream:
	"""
	Tee a stream to print to a file and console output.
	"""

	def __init__(self, original_stream):
		"""
		Initalize Tee Stream.

		:param original_stream: Original stdout or stderr
		:type original_stream: Stream
		"""
		self.original_stream = original_stream
		self.log = []

	def write(self, data):
		"""
		Write to file and stream.

		:param data: Captured data
		:type data: Any
		"""
		self.original_stream.write(data)
		self.log.append(data)

	def flush(self):
		"""
		Flush the stream.
		"""
		self.original_stream.flush()


def capture_and_log(
	func: Callable, *args, log_path: StrPath = None, **kwargs
) -> tuple[list, list, Any]:
	"""
	Captures stdout and stderr, prints in real-time, and logs to files.

	:param func: Function to execute
	:type func: Callable
	:param *args: Arguments without keywords for the function
	:type *args: *args
	:param log_path: Path to logfile
	:type log_path: StrPath
	:param **kwargs: Keyword arguments
	:type **kwargs: **kwargs
	:return: Standard output and standard error
	:rtype: tuple[list, list, Any]
	"""
	# Save standard out & err
	original_stdout = sys.stdout
	original_stderr = sys.stderr

	# Replace with custom
	sys.stdout = TeeStream(original_stdout)
	sys.stderr = TeeStream(original_stderr)

	# Run method
	results = func(*args, **kwargs)

	# Save caputured output
	out = sys.stdout.log
	err = sys.stderr.log
	if log_path:
		with open(log_path, "w") as out_file:
			out_file.write(f"out:\n{''.join(out)}\n\n\nerr:\n{''.join(err)}")

	# Restore original
	sys.stdout = original_stdout
	sys.stderr = original_stderr

	return results, out, err
