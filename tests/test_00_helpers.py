#!/usr/bin/env python
"""
Testing the helper functions.
"""

from tests.common import *
from source.rampt.helpers.general import *


platform = get_platform()
filepath = get_internal_filepath(__file__)
out_path, mock_path, example_path, batch_path = contruct_common_paths(filepath)
make_out(out_path)


# String operations
def test_change_case_str():
	assert change_case_str("abc", slice(1, 3), "upper") == "aBC"

	with pytest.raises(ValueError):
		change_case_str("abc", slice(1, 3), "lowa")


def test_Substring_class():
	# Test sting functionality
	assert Substring("Acb").lower() == "acb"

	# Test comparison matching
	assert Substring("Acb") == "A"
	assert Substring("Acb") == "b"


# List operations
def test_extend_list():
	# Empty list
	assert extend_list([], "x") == ["x"]

	# List with content
	assert extend_list(["w"], "x") == ["w", "x"]

	# Extension of empty list with list
	assert extend_list([], ["x"]) == ["x"]

	# Extension of list with content with list
	assert extend_list(["w"], ["x"]) == ["w", "x"]

	# Extension of list with content with empty list
	assert extend_list(["w"], []) == ["w"]


def test_to_list():
	# Empty case
	assert to_list([]) == []

	# Filled case
	assert to_list(["x"]) == ["x"]

	# Raw case
	assert to_list("x") == ["x"]
	assert to_list(1.0) == [1.0]

	# Multi-filled case
	assert to_list(["w", "x"]) == ["w", "x"]


# Directory operations
def test_make_new_dir():
	clean_out(out_path)

	assert not make_new_dir(out_path)

	assert make_new_dir(join(out_path, "test"))
	assert os.path.isdir(join(out_path, "test"))


def test_get_directory():
	# Existent directory
	assert get_directory(out_path) == out_path

	# Newly created directory
	make_new_dir(join(out_path, "test"))
	assert get_directory(join(out_path, "test")) == join(out_path, "test")

	# Fictional last entry
	assert get_directory(join(out_path, "fictional")) == out_path

	# Real last file enry
	with open(join(out_path, "real.txt"), "w"):
		pass
	assert os.path.isfile(join(out_path, "real.txt"))
	assert get_directory(join(out_path, "real.txt")) == out_path


# File operations
def test_open_last_n_line():
	assert open_last_n_line(filepath=join(mock_path, "example_text.txt"), n=1) == "Didididididididi"
	assert open_last_n_line(filepath=join(mock_path, "example_text.txt"), n=2).startswith(
		"Huhuhuhuhu"
	)
	with pytest.raises(OSError):
		open_last_n_line(filepath=join(mock_path, "example_text.txt"), n=5)


def test_open_last_line_with_content():
	assert (
		open_last_line_with_content(filepath=join(mock_path, "example_text.txt"))
		== "Didididididididi"
	)
	with pytest.raises(ValueError):
		open_last_line_with_content(filepath=join(mock_path, "empty_file"))
	with pytest.raises(ValueError):
		open_last_line_with_content(filepath=join(mock_path, "empty_text.txt"))


def test_replace_file_ending():
	assert replace_file_ending(os.path.join("a", "b..", "c.anaconda"), "conda") == os.path.join(
		"a", "b..", "c.conda"
	)


# Path nester
def mock_path_nester():
	path_nester = Path_Nester()

	result = path_nester.update_nested_paths(new_paths=["/a/c", "/a/b"])
	expected = [
		{
			"id": "1",
			"label": "a",
			"children": [
				{"id": "2", "label": os.path.normpath("/a/c"), "children": []},
				{"id": "4", "label": os.path.normpath("/a/b"), "children": []},
			],
		}
	]
	assert result == expected

	path_nester.update_nested_paths(new_paths="/a/d")
	expected[0].get("children").append(
		{"id": "6", "label": os.path.normpath("/a/d"), "children": []}
	)
	assert result == expected

	path_nester.update_nested_paths(new_paths="/a/c")
	assert result == expected

	path_nester.update_nested_paths(new_paths="/b")
	expected.append({"id": "9", "label": os.path.normpath("/b"), "children": []})
	assert result == expected


# CMD
def test_execute_verbose_command():
	clean_out(out_path)
	execute_verbose_command("echo test4", verbosity=1)
	assert not os.path.isfile(join(out_path, "text.txt"))

	execute_verbose_command(f"echo test > {join( out_path, "text.txt")}", verbosity=3)
	assert os.path.isfile(join(out_path, "text.txt"))
	with open(join(out_path, "text.txt"), "r") as f:
		text = f.read()
		assert text.strip() == "test"

	execute_verbose_command(f"echo test2 > {join( out_path, "text.txt")}", verbosity=1)
	with open(join(out_path, "text.txt"), "r") as f:
		text = f.read()
		assert text.strip() == "test2"

	execute_verbose_command("echo test3", verbosity=1, log_path=join(out_path, "text.txt"))
	with open(join(out_path, "text.txt"), "r") as f:
		text = f.read()
		assert text.replace("\n", "") == "out:test3err:None"


# Parallel scheduling
def test_compute_scheduled():
	futures = [
		(dask.delayed(str.lower))("Acb"),
		(dask.delayed(str.lower))("AcB"),
		(dask.delayed(str.lower))("acb"),
		(dask.delayed(str.lower))("ACB"),
	]
	expected_return = ["acb"] * 4

	# One worker
	results = compute_scheduled(futures, num_workers=1)
	assert results[0] == expected_return

	# Two workers
	results = compute_scheduled(futures, num_workers=2, scheduler="threads")
	assert results[0] == expected_return

	# Eight workers
	results = compute_scheduled(futures, num_workers=4, scheduler="processes")
	assert results[0] == expected_return


# Class handling
def test_get_attribute_recursive():
	class Object(object):
		pass

	o, b, j, e, c, t = [Object()] * 6
	t = 1
	c.t = t
	e.c = c
	j.e = e
	b.j = j
	o.b = b

	assert get_attribute_recursive(o, "b.j.e.c.t") == 1
	assert get_attribute_recursive(o, "b.j.e.c.z", 2) == 2
	assert get_attribute_recursive(o, "b.j.z.c.t", 2) == 2
	try:
		get_attribute_recursive(o, "b.j.z.c.t")
	except AttributeError as ae:
		assert str(ae) == r"'Object' object has no attribute 'z'"


def test_set_attribute_recursive():
	class Object(object):
		pass

	o, b, j, e, c, t = [Object()] * 6
	setattr(c, "t", t)
	setattr(e, "c", c)
	setattr(j, "e", e)
	setattr(b, "j", j)
	setattr(o, "b", b)

	set_attribute_recursive(o, "b.j.e.c.t", 2)
	assert get_attribute_recursive(o, "b.j.e.c.t") == 2


# Webrequests
def test_check_for_str_request():
	url = "https://api.openstreetmap.org/api/0.6/relation/10000000/full.json"
	assert check_for_str_request(
		url=url, query='"version":"0.6"', retries=10, allowed_fails=3, retry_time=1.0, timeout=5
	)
	assert not check_for_str_request(
		url=url, query='"version":"0.sad"', retries=10, allowed_fails=3, retry_time=1.0, timeout=5
	)


def test_clear_out():
	clean_out(out_path)
