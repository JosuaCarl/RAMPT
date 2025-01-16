#!/usr/bin/env python3
"""
Test installation of project.
"""

from tests.common import *
from rampt.installer import *

platform = get_platform()
filepath = get_internal_filepath(__file__)
out_path, mock_path, example_path, batch_path, installer_path = contruct_common_paths(filepath)
make_out(out_path)


urls = {
    "MSconvert": {
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
    "Sirius": {
        "win64": "https://github.com/sirius-ms/sirius/releases/download/v6.0.7/sirius-6.0.7-win64.zip",
        "win32": "https://github.com/sirius-ms/sirius/releases/download/v6.0.7/sirius-6.0.7-win64.zip",
        "mac": "https://github.com/sirius-ms/sirius/releases/download/v6.0.7/sirius-6.0.7-osx64.zip",
        "linux": "https://github.com/sirius-ms/sirius/releases/download/v6.0.7/sirius-6.0.7-linux64.zip",
    },
}


def test_create_symlink():
    create_symlink(join(mock_path, "empty_file"), join(out_path, "empty_file"))
    assert os.path.isfile(join(out_path, "empty_file"))


def test_tool_available():
    assert tool_available("which")


def test_install_uv():
    clean_out(out_path)
    installer = Installer()
    installer.install_uv()


def test_install_project():
    clean_out(out_path)
    installer = Installer()
    name = "rampt"

    installer.install_uv()

    install_path = installer.install_component(
        name=name,
        urls="https://codeload.github.com/JosuaCarl/mine2sirius_pipe/zip/refs/heads/main",
        install_path=out_path,
    )

    subprocess.Popen(["uv", "sync", "--no-dev"], cwd=install_path)
    
    assert install_path == join(out_path, name)
    assert os.path.isdir(join(out_path, name))
    
    python_path = join(install_path, ".venv", "bin", "python")
    if "windows" in installer.op_sys:
        path_executable = join(install_path, f"{installer.name}.bat")
        execution_script = f'@echo off\n"{python_path}" -m module %*'
        with open(path_executable, "w") as file:
            file.write(execution_script)
    else:
        path_executable = join(install_path, installer.name)
        execution_script = f'#!/usr/bin/sh\n"{python_path}" -m module'
        with open(path_executable, "w") as file:
            file.write(execution_script)

    register_program(
        op_sys=installer.op_sys, program_path=path_executable, name=installer.name
    )

    assert tool_available(name.lower())


def test_install_msconvert(recwarn):
    clean_out(out_path)
    installer = Installer()
    name = "MSconvert"

    install_path = installer.install_component(
        name=name,
        urls=urls.get(name),
        install_path=out_path,
        extraction_method="tar.bz2",
        bin_path="",
    )

    if "mac" in installer.op_sys:
        assert len(recwarn) == 1
        user_warning = (
            f"{name} is not available for {installer.op_sys}."
            + "To use it, please  find a way to install and add it to PATH yourself."
        )
        assert recwarn[0].message.args[0].endswith(user_warning)
    else:
        assert install_path == join(out_path, name)
        assert tool_available(name.lower())
        assert os.path.isdir(join(out_path, name))


def test_install_mzmine():
    clean_out(out_path)
    installer = Installer()
    name = "MZmine"

    install_path = installer.install_component(
        name=name, urls=urls.get(name), install_path=out_path, bin_path="bin"
    )

    assert install_path == join(out_path, name)
    assert tool_available(name.lower())
    assert os.path.isdir(join(out_path, name))


def test_install_sirius():
    clean_out(out_path)
    installer = Installer()
    name = "Sirius"

    install_path = installer.install_component(
        name=name, urls=urls.get(name), install_path=out_path, bin_path=join("sirius", "bin")
    )

    assert install_path == join(out_path, name)
    assert tool_available(name.lower())
    assert os.path.isdir(join(out_path, name))


def test_install_components():
    clean_out(out_path)
    installer = Installer()
    installer.install_path = out_path

    installer.install_components(["MSconvert", "MZmine", "Sirius"])

    assert tool_available("msconvert")
    assert tool_available("mzmine")
    assert tool_available("sirius")


def test_clean_out():
    clean_out(out_path)
