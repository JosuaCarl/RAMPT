#!/usr/bin/env python3
"""
Test installation of project.
"""

from tests.common import *
from rampt.installer import *

platform = get_platform().lower()
filepath = get_internal_filepath(__file__)
out_path, mock_path, example_path, batch_path, installer_path = contruct_common_paths(filepath)
make_out(out_path)


urls = {
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


def test_create_symlink():
    if "windows" in platform:
        create_shortcut_windows(
            shortcut_script_path=join(out_path, "create_shorcut.bat"),
            target_path=join(mock_path, "empty_file"),
            shortcut_path=join(out_path, "empty_file.lnk"),
            icon_path=join(mock_path, "icon.ico"),
        )
        assert os.path.isfile(join(out_path, "empty_file.lnk"))
    else:
        create_symlink(join(mock_path, "empty_file"), join(out_path, "empty_file"))
        assert os.path.isfile(join(out_path, "empty_file"))


def test_tool_available():
    assert tool_available("python") or tool_available("python3")


def test_install_uv():
    clean_out(out_path)
    root = tk.Tk()
    installer = InstallerApp(root, local_only=True, show_progress=False)
    installer.install_uv()
    assert tool_available("uv")


def test_install_project():
    clean_out(out_path)
    root = tk.Tk()
    installer = InstallerApp(root, local_only=True, show_progress=False)
    name = "rampt"
    install_path = installer.install_project(
        name=name,
        url="https://github.com/JosuaCarl/RAMPT/releases/latest/download/rampt.zip",
        install_path=out_path,
    )

    assert install_path == join(out_path, name)
    assert os.path.isdir(join(out_path, name))
    assert tool_available(name.lower())


def test_install_msconvert(recwarn):
    clean_out(out_path)
    root = tk.Tk()
    installer = InstallerApp(root, local_only=True, show_progress=False)
    name = "MSconvert"

    install_path = installer.install_component(
        name=name,
        urls=urls.get(name),
        install_path=out_path,
        extraction_method="tar.bz2",
        bin_paths="",
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
    root = tk.Tk()
    installer = InstallerApp(root, local_only=True, show_progress=False)
    name = "MZmine"

    install_path = installer.install_component(
        name=name, urls=urls.get(name), install_path=out_path, bin_paths={"windows": "", "*": "bin"}
    )

    assert install_path == join(out_path, name)
    assert tool_available([name.lower(), f"{name.lower()}_console"])
    assert os.path.isdir(join(out_path, name))


def test_install_sirius():
    clean_out(out_path)
    root = tk.Tk()
    installer = InstallerApp(root, local_only=True, show_progress=False)
    name = "Sirius"

    install_path = installer.install_component(
        name=name, urls=urls.get(name), install_path=out_path, bin_paths=join("sirius", "bin")
    )

    assert install_path == join(out_path, name)
    assert tool_available(name.lower())
    assert os.path.isdir(join(out_path, name))


def test_install_components():
    clean_out(out_path)
    root = tk.Tk()
    installer = InstallerApp(root, local_only=True, show_progress=False)
    installer.install_path = out_path

    installer.install_components(["MSconvert", "MZmine", "Sirius"])

    assert tool_available("msconvert")
    assert tool_available(["mzmine", "mzmine_console"])
    assert tool_available("sirius")


def test_clean_out():
    clean_out(out_path)
