<div align="center">
  <a href="https://github.com/JosuaCarl/RAMPT" target="_blank">
  <picture>
    <img alt="Taipy" src="https://github.com/JosuaCarl/RAMPT/blob/main/statics/share/rampt.png?raw=true" width="200" />
  </picture>
  </a>
</div>

# RAMPT 
A "Raw to annotation metabolomics pipline tool"

## Features

| Feature                                       | Status |
|-----------------------------------------------|--------|
| Convert raw to community formats (.mz(X)ML)   | ✅     |
| MZmine batch file to find features            | ✅     |
| Formula, molecule, ... annotation with SIRIUS | ✅     |
| FBMN annotation with GNPS                     | ✅     |
| Summary in compact table                      | ✅     |
| Analysis through simple operations (z-score)  | ✅     |
| Dynamic visualization of data                 | ✅     |
| Adaptive analysis                             | 🛠️     |
| Adaptive visualization                        | 🛠️     |
| Release as a python package                   | 🛞     |

For planned improvements, please refer to [Contribute.md](./Contribute.md).

## Installing
1. Download latest release for your platform [here](https://github.com/JosuaCarl/RAMPT/releases)
2. Run the installer
3. The program should be available on PATH


### Build from source

#### Prerequisites:
- Install [git](https://git-scm.com/downloads)
- Install [uv](https://docs.astral.sh/uv/getting-started/installation/)

```sh
git clone https://github.com/JosuaCarl/RAMPT.git
cd RAMPT
uv sync
```

Run with `uv run python -m rampt`

Note that for the following dependencies are required to be installed and availible on PATH for functionality:
- [MZmine](https://mzio.io/mzmine-news/)
- [MSconvert/ProteoWizard](https://proteowizard.sourceforge.io/)
- [Sirius](https://bio.informatik.uni-jena.de/software/sirius/)

### Usage
In principle you need two things for RAMPT to be able to run a complete pipeline:
1. A batch file form MZmine
2. Data upon which to perform the pipeline

If those two are entered, you can execute the steps in the scenario one-by-one or as a whole.

After this, you may go to the Analysis tab (up top) and look at your data.

You can always look at the detailed documentation of methods

For detailed information about usage, please refer to the [Manual](./Manual.md)

### Documentation
For module documentation and more please refer to [https://josuacarl.github.io/RAMPT/](https://josuacarl.github.io/RAMPT/)

## Contributing
Please refer to [Contribute.md](./Contribute.md) for further information about how to contribute to the project.

## Licenses of dependencies
### Major programs
| Name                          | Version        | License                                                                                             |
|-------------------------------|----------------|-----------------------------------------------------------------------------------------------------|
| MSconvert / Proteowizard      | 24.8.1         | Apache License (https://proteowizard.sourceforge.io/licenses.html)                                  |
| MZmine                        | 4.4.3          | MIT License    (https://github.com/mzmine/mzmine/blob/master/LICENSE.txt)                           |
| GNPS                          | 30             | CC0(Database entries) + Custom (https://github.com/CCMS-UCSD/GNPS_Workflows/blob/master/LICENSE)    |
| Sirius                        | 6.0.6          | GNU Affero General Public License v3. (https://github.com/sirius-ms/sirius/blob/stable/LICENSE.txt) |

### Package dependencies
| Name                          | Version        | License                                                                                             |
|-------------------------------|----------------|-----------------------------------------------------------------------------------------------------|
| Automat                       | 24.8.1         | MIT License                                                                                         |
| Eel                           | 0.18.1         | MIT License                                                                                         |
| Flask                         | 3.1.0          | BSD License                                                                                         |
| Flask-Cors                    | 5.0.0          | MIT License                                                                                         |
| Flask-RESTful                 | 0.3.10         | BSD License                                                                                         |
| Flask-SocketIO                | 5.4.1          | MIT License                                                                                         |
| Jinja2                        | 3.1.5          | BSD License                                                                                         |
| Markdown                      | 3.6            | BSD License                                                                                         |
| MarkupSafe                    | 3.0.2          | BSD License                                                                                         |
| PyYAML                        | 6.0.2          | MIT License                                                                                         |
| Pygments                      | 2.19.1         | BSD License                                                                                         |
| SQLAlchemy                    | 2.0.30         | MIT License                                                                                         |
| Send2Trash                    | 1.8.3          | BSD License                                                                                         |
| Sphinx                        | 7.4.7          | BSD License                                                                                         |
| Twisted                       | 24.7.0         | MIT License                                                                                         |
| Werkzeug                      | 3.1.3          | BSD License                                                                                         |
| accessible-pygments           | 0.0.5          | BSD License                                                                                         |
| alabaster                     | 0.7.16         | BSD License                                                                                         |
| altgraph                      | 0.17.4         | MIT License                                                                                         |
| aniso8601                     | 9.0.1          | BSD License                                                                                         |
| anyio                         | 4.8.0          | MIT License                                                                                         |
| apispec                       | 6.6.1          | MIT License                                                                                         |
| apispec-webframeworks         | 1.1.0          | MIT License                                                                                         |
| argon2-cffi                   | 23.1.0         | MIT License                                                                                         |
| argon2-cffi-bindings          | 21.2.0         | MIT License                                                                                         |
| argparse                      | 1.4.0          | Python Software Foundation License                                                                  |
| arrow                         | 1.3.0          | Apache Software License                                                                             |
| asttokens                     | 3.0.0          | Apache 2.0                                                                                          |
| async-lru                     | 2.0.4          | MIT License                                                                                         |
| attrs                         | 24.3.0         | UNKNOWN                                                                                             |
| auto-py-to-exe                | 2.45.1         | MIT License                                                                                         |
| babel                         | 2.16.0         | BSD License                                                                                         |
| beautifulsoup4                | 4.12.3         | MIT License                                                                                         |
| bidict                        | 0.23.1         | Mozilla Public License 2.0 (MPL 2.0)                                                                |
| binaryornot                   | 0.4.4          | BSD License                                                                                         |
| bleach                        | 6.2.0          | Apache Software License                                                                             |
| blinker                       | 1.9.0          | MIT License                                                                                         |
| boto3                         | 1.34.113       | Apache Software License                                                                             |
| botocore                      | 1.34.162       | Apache Software License                                                                             |
| bottle                        | 0.13.2         | MIT License                                                                                         |
| bottle-websocket              | 0.2.9          | MIT License                                                                                         |
| certifi                       | 2024.12.14     | Mozilla Public License 2.0 (MPL 2.0)                                                                |
| cffi                          | 1.17.1         | MIT License                                                                                         |
| chardet                       | 5.2.0          | GNU Lesser General Public License v2 or later (LGPLv2+)                                             |
| charset-normalizer            | 3.3.2          | MIT License                                                                                         |
| click                         | 8.1.8          | BSD License                                                                                         |
| cloudpickle                   | 3.1.0          | BSD License                                                                                         |
| colorama                      | 0.4.6          | BSD License                                                                                         |
| comm                          | 0.2.2          | BSD License                                                                                         |
| constantly                    | 23.10.4        | MIT License                                                                                         |
| contourpy                     | 1.3.1          | BSD License                                                                                         |
| cookiecutter                  | 2.6.0          | BSD License                                                                                         |
| cycler                        | 0.12.1         | BSD License                                                                                         |
| dask                          | 2024.12.1      | BSD License                                                                                         |
| debugpy                       | 1.8.11         | MIT License                                                                                         |
| decorator                     | 5.1.1          | BSD License                                                                                         |
| deepdiff                      | 7.0.1          | MIT License                                                                                         |
| defusedxml                    | 0.7.1          | Python Software Foundation License                                                                  |
| dnspython                     | 2.7.0          | ISC License (ISCL)                                                                                  |
| docutils                      | 0.21.2         | BSD License; GNU General Public License (GPL); Public Domain; Python Software Foundation License    |
| et_xmlfile                    | 2.0.0          | MIT License                                                                                         |
| executing                     | 2.1.0          | MIT License                                                                                         |
| fastjsonschema                | 2.21.1         | BSD License                                                                                         |
| fonttools                     | 4.55.3         | MIT License                                                                                         |
| fqdn                          | 1.5.1          | Mozilla Public License 2.0 (MPL 2.0)                                                                |
| fsspec                        | 2024.12.0      | BSD License                                                                                         |
| future                        | 1.0.0          | MIT License                                                                                         |
| gevent                        | 24.11.1        | MIT License                                                                                         |
| gevent-websocket              | 0.10.1         | Copyright 2011-2017 Jeffrey Gelens <jeffrey@noppo.pro>                                              |
| gitignore_parser              | 0.1.11         | MIT License                                                                                         |
| greenlet                      | 3.1.1          | MIT License                                                                                         |
| h11                           | 0.14.0         | MIT License                                                                                         |
| httpcore                      | 1.0.7          | BSD License                                                                                         |
| httpx                         | 0.28.1         | BSD License                                                                                         |
| hyperlink                     | 21.0.0         | MIT License                                                                                         |
| icecream                      | 2.1.3          | MIT License                                                                                         |
| idna                          | 3.10           | BSD License                                                                                         |
| imagesize                     | 1.4.1          | MIT License                                                                                         |
| incremental                   | 24.7.2         | MIT License                                                                                         |
| iniconfig                     | 2.0.0          | MIT License                                                                                         |
| ipykernel                     | 6.29.5         | BSD License                                                                                         |
| ipython                       | 8.31.0         | BSD License                                                                                         |
| ipywidgets                    | 8.1.5          | BSD License                                                                                         |
| isoduration                   | 20.11.0        | ISC License (ISCL)                                                                                  |
| itsdangerous                  | 2.2.0          | BSD License                                                                                         |
| jedi                          | 0.19.2         | MIT License                                                                                         |
| jmespath                      | 1.0.1          | MIT License                                                                                         |
| json5                         | 0.10.0         | Apache Software License                                                                             |
| jsonpointer                   | 3.0.0          | BSD License                                                                                         |
| jsonschema                    | 4.23.0         | MIT License                                                                                         |
| jsonschema-specifications     | 2024.10.1      | MIT License                                                                                         |
| jupyter                       | 1.1.1          | BSD License                                                                                         |
| jupyter-console               | 6.6.3          | BSD License                                                                                         |
| jupyter-events                | 0.11.0         | BSD License                                                                                         |
| jupyter-lsp                   | 2.2.5          | BSD License                                                                                         |
| jupyter_client                | 8.6.3          | BSD License                                                                                         |
| jupyter_core                  | 5.7.2          | BSD License                                                                                         |
| jupyter_server                | 2.15.0         | BSD License                                                                                         |
| jupyter_server_terminals      | 0.5.3          | BSD License                                                                                         |
| jupyterlab                    | 4.3.4          | BSD License                                                                                         |
| jupyterlab_pygments           | 0.3.0          | BSD License                                                                                         |
| jupyterlab_server             | 2.27.3         | BSD License                                                                                         |
| jupyterlab_widgets            | 3.0.13         | BSD License                                                                                         |
| kiwisolver                    | 1.4.8          | BSD License                                                                                         |
| kthread                       | 0.2.3          | MIT License                                                                                         |
| locket                        | 1.0.0          | BSD License                                                                                         |
| lxml                          | 5.3.0          | BSD License                                                                                         |
| markdown-it-py                | 3.0.0          | MIT License                                                                                         |
| marshmallow                   | 3.21.2         | MIT License                                                                                         |
| matplotlib                    | 3.10.0         | Python Software Foundation License                                                                  |
| matplotlib-inline             | 0.1.7          | BSD License                                                                                         |
| mdurl                         | 0.1.2          | MIT License                                                                                         |
| mistune                       | 3.1.0          | BSD License                                                                                         |
| multipledispatch              | 1.0.0          | BSD                                                                                                 |
| nbclient                      | 0.10.2         | BSD License                                                                                         |
| nbconvert                     | 7.16.5         | BSD License                                                                                         |
| nbformat                      | 5.10.4         | BSD License                                                                                         |
| nest-asyncio                  | 1.6.0          | BSD License                                                                                         |
| networkx                      | 3.3            | BSD License                                                                                         |
| notebook                      | 7.3.2          | BSD License                                                                                         |
| notebook_shim                 | 0.2.4          | BSD License                                                                                         |
| numpy                         | 1.26.4         | BSD License                                                                                         |
| openpyxl                      | 3.1.2          | MIT License                                                                                         |
| ordered-set                   | 4.1.0          | MIT License                                                                                         |
| overrides                     | 7.7.0          | Apache License, Version 2.0                                                                         |
| packaging                     | 24.2           | Apache Software License; BSD License                                                                |
| pandas                        | 2.2.2          | BSD License                                                                                         |
| pandocfilters                 | 1.5.1          | BSD License                                                                                         |
| parso                         | 0.8.4          | MIT License                                                                                         |
| partd                         | 1.4.2          | BSD                                                                                                 |
| passlib                       | 1.7.4          | BSD                                                                                                 |
| patsy                         | 1.0.1          | BSD License                                                                                         |
| pexpect                       | 4.9.0          | ISC License (ISCL)                                                                                  |
| pillow                        | 11.1.0         | CMU License (MIT-CMU)                                                                               |
| platformdirs                  | 4.3.6          | MIT License                                                                                         |
| plotly                        | 5.24.1         | MIT License                                                                                         |
| pluggy                        | 1.5.0          | MIT License                                                                                         |
| prometheus_client             | 0.21.1         | Apache Software License                                                                             |
| prompt_toolkit                | 3.0.48         | BSD License                                                                                         |
| psutil                        | 6.1.1          | BSD License                                                                                         |
| ptyprocess                    | 0.7.0          | ISC License (ISCL)                                                                                  |
| pure_eval                     | 0.2.3          | MIT License                                                                                         |
| pyarrow                       | 17.0.0         | Apache Software License                                                                             |
| pycparser                     | 2.22           | BSD License                                                                                         |
| pydata-sphinx-theme           | 0.16.1         | BSD License                                                                                         |
| pyinstaller                   | 6.11.1         | GNU General Public License v2 (GPLv2)                                                               |
| pyinstaller-hooks-contrib     | 2024.11        | Apache Software License; GNU General Public License v2 (GPLv2)                                      |
| pymongo                       | 4.7.2          | Apache Software License                                                                             |
| pyopenms                      | 3.2.0          | BSD License                                                                                         |
| pyparsing                     | 3.2.1          | MIT License                                                                                         |
| pytest                        | 8.3.4          | MIT License                                                                                         |
| python-dateutil               | 2.9.0.post0    | Apache Software License; BSD License                                                                |
| python-dotenv                 | 1.0.1          | BSD License                                                                                         |
| python-engineio               | 4.11.2         | MIT License                                                                                         |
| python-json-logger            | 3.2.1          | BSD License                                                                                         |
| python-slugify                | 8.0.4          | MIT License                                                                                         |
| python-socketio               | 5.12.1         | MIT License                                                                                         |
| pytz                          | 2024.1         | MIT License                                                                                         |
| pyzmq                         | 26.2.0         | BSD License                                                                                         |
| referencing                   | 0.35.1         | MIT License                                                                                         |
| regex                         | 2024.11.6      | Apache Software License                                                                             |
| requests                      | 2.32.3         | Apache Software License                                                                             |
| rfc3339-validator             | 0.1.4          | MIT License                                                                                         |
| rfc3986-validator             | 0.1.1          | MIT License                                                                                         |
| rich                          | 13.9.4         | MIT License                                                                                         |
| rpds-py                       | 0.22.3         | MIT License                                                                                         |
| ruamel.yaml                   | 0.18.10        | MIT License                                                                                         |
| ruamel.yaml.clib              | 0.2.12         | MIT License                                                                                         |
| ruff                          | 0.8.6          | MIT License                                                                                         |
| s3transfer                    | 0.10.4         | Apache Software License                                                                             |
| scipy                         | 1.15.0         | BSD License                                                                                         |
| seaborn                       | 0.13.2         | BSD License                                                                                         |
| simple-websocket              | 1.0.0          | MIT License                                                                                         |
| six                           | 1.17.0         | MIT License                                                                                         |
| sniffio                       | 1.3.1          | Apache Software License; MIT License                                                                |
| snowballstemmer               | 2.2.0          | BSD License                                                                                         |
| soupsieve                     | 2.6            | MIT License                                                                                         |
| sphinxcontrib-applehelp       | 2.0.0          | BSD License                                                                                         |
| sphinxcontrib-devhelp         | 2.0.0          | BSD License                                                                                         |
| sphinxcontrib-htmlhelp        | 2.1.0          | BSD License                                                                                         |
| sphinxcontrib-jsmath          | 1.0.1          | BSD License                                                                                         |
| sphinxcontrib-qthelp          | 2.0.0          | BSD License                                                                                         |
| sphinxcontrib-serializinghtml | 2.0.0          | BSD License                                                                                         |
| stack-data                    | 0.6.3          | MIT License                                                                                         |
| statsmodels                   | 0.14.4         | BSD License                                                                                         |
| taipy                         | 4.0.2          | Apache Software License                                                                             |
| taipy-common                  | 4.0.2          | Apache Software License                                                                             |
| taipy-core                    | 4.0.2          | Apache Software License                                                                             |
| taipy-gui                     | 4.0.2          | Apache Software License                                                                             |
| taipy-rest                    | 4.0.2          | Apache Software License                                                                             |
| taipy-templates               | 4.0.2          | Apache Software License                                                                             |
| tee-subprocess                | 1.2.0          | MIT                                                                                                 |
| tenacity                      | 9.0.0          | Apache Software License                                                                             |
| terminado                     | 0.18.1         | BSD License                                                                                         |
| text-unidecode                | 1.3            | Artistic License; GNU General Public License (GPL); GNU General Public License v2 or later (GPLv2+) |
| tinycss2                      | 1.4.0          | BSD License                                                                                         |
| toml                          | 0.10.2         | MIT License                                                                                         |
| toolz                         | 1.0.0          | BSD License                                                                                         |
| tornado                       | 6.4.2          | Apache Software License                                                                             |
| tqdm                          | 4.67.1         | MIT License; Mozilla Public License 2.0 (MPL 2.0)                                                   |
| traitlets                     | 5.14.3         | BSD License                                                                                         |
| types-python-dateutil         | 2.9.0.20241206 | Apache Software License                                                                             |
| typing_extensions             | 4.12.2         | Python Software Foundation License                                                                  |
| tzdata                        | 2024.2         | Apache Software License                                                                             |
| tzlocal                       | 5.2            | MIT License                                                                                         |
| uri-template                  | 1.3.0          | MIT License                                                                                         |
| urllib3                       | 2.3.0          | MIT License                                                                                         |
| watchdog                      | 4.0.1          | Apache Software License                                                                             |
| webcolors                     | 24.11.1        | BSD License                                                                                         |
| webencodings                  | 0.5.1          | BSD License                                                                                         |
| websocket-client              | 1.8.0          | Apache Software License                                                                             |
| widgetsnbextension            | 4.0.13         | BSD License                                                                                         |
| wsproto                       | 1.2.0          | MIT License                                                                                         |
| zope.event                    | 5.0            | Zope Public License                                                                                 |
| zope.interface                | 7.2            | Zope Public License                                                                                 |