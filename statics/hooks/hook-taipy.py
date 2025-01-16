# hook-pandas.py
from PyInstaller.utils.hooks import collect_all


datas = []
hiddenimports = []
binaries = []

data, binary, hiddenimport = collect_all("taipy")
datas += data
hiddenimports += hiddenimport
binaries += binary
