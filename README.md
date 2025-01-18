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

## Contributing
Please refer to [Contribute.md](./Contribute.md) for further information about how to contribute to the project.