load("info.bzl", "name", "version", "description", "authors")

# Read data from pyproject.toml
def get_project_info():
    project_info = {
        "name": name,
        "version": version,
        "description": description,
        "authors": authors,
        }

    return project_info


# Define the Python distribution
def make_executable():
    project_info = get_project_info()
    
    # Add dependencies from requirements.txt or pyproject.toml
    distribution = default_python_distribution()

    # Change settings for advanced options
    policy = distribution.make_python_packaging_policy()
    python_config = distribution.make_python_interpreter_config()


    exe = distribution.to_python_executable(
        name=project_info.get("name"),
        packaging_policy=policy,
        config=python_config,
    )

    exe.read_virtualenv(
        ".venv"
    )

    return exe



def make_embedded_resources(exe):
    return exe.to_embedded_resources()

def make_install(exe):
    # Create an object that represents our installed application file layout.
    files = FileManifest()

    # Add the generated executable to our install layout in the root directory.
    files.add_python_resource(".", exe)

    return files


def make_msi(exe):
    # See the full docs for more. But this will convert your Python executable
    # into a `WiXMSIBuilder` Starlark type, which will be converted to a Windows
    # .msi installer when it is built.

    project_info = get_project_info()

    return exe.to_wix_msi_builder(
        # Simple identifier of your app.
        project_info["name"],
        # The name of your application.
        project_info["description"],
        # The version of your application.
        project_info["version"],
        # The author/manufacturer of your application.
        ", ".join([author["name"] for author in project_info["authors"]])
    )

register_target("exe", make_executable)
register_target("resources", make_embedded_resources, depends=["exe"], default_build_script=True)
register_target("install", make_install, depends=["exe"], default=True)
register_target("msi_installer", make_msi, depends=["exe"])

# Resolve whatever targets the invoker of this configuration file is requesting
# be resolved.
resolve_targets()