
![logo_rampt](https://github.com/JosuaCarl/RAMPT/blob/main/statics/share/rampt.png?raw=true)

# RAMPT 
A "Raw to annotation metabolomics pipline tool"

## Features

| Feature                                       | Status |
|-----------------------------------------------|--------|
| Convert raw to community formats (.mz(X)ML)   | ✅      |
| MZmine batch file to find features            | ✅      |
| Formula, molecule, ... annotation with SIRIUS | ✅      |
| FBMN annotation with GNPS                     | ✅      |
| Summary in compact table                      | ✅      |
| Analysis through simple operations (z-score)  | ✅      |
| Dynamic visualization of data                 | ✅      |
| Adaptive analysis                             | 🛠️      |
| Adaptive visualization                        | 🛠️      |

For planned improvements, please refer to [Contribute.md](./Contribute.md).

## Installing
1. Download latest release for your platform [here](https://github.com/JosuaCarl/RAMPT/releases)
2. Run the installer
3. The program should be available on PATH


### Build from source
1. `git clone https://github.com/JosuaCarl/RAMPT.git`
2. `cd RAMPT`
3. Install uv [https://docs.astral.sh/uv/getting-started/installation/](https://docs.astral.sh/uv/getting-started/installation/)
4. `uv sync`
5. Run with `uv run python -m rampt`

Note, that this requires the following dependencies to be installed and availible on PATH:
- MZmine
- MSconvert
- Sirius

### Usage
For detailed information about usage, please refer to the [documentation](https://josuacarl.github.io/RAMPT/)

## Contributing
Please refer to [Contribute.md](./Contribute.md) for further information about how to contribute to the project.