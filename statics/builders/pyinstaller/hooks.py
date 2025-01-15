# hook-pandas.py
from PyInstaller.utils.hooks import collect_data_files

# Collect all data files in the pandas module directory
datas = []
datas += collect_data_files('taipy')
