import os
import platform
from tqdm import tqdm
import dask.multiprocessing

start = "D:" if platform.system() == "Windows" else "/mnt/d"

 

def convert_folder(folder):
    os.system( f'msconvert --mzML --64 --zlib -o {os.path.join(folder, "ConvertedData")} {os.path.join(folder, "RawData", "*")}' )

def convert_folders(root_folder):
    for folder in tqdm(os.listdir(root_folder)):
        folder = os.path.join(root_folder, folder)
        if len(os.listdir(os.path.join(folder, "RawData"))) != len(os.listdir(os.path.join(folder, "ConvertedData"))):
            convert_folder(folder)

def convert_file(folder, file):
    os.system( f'msconvert --mzML --64 --zlib -o {os.path.join(folder, "ConvertedData")} {os.path.join(folder, "RawData", file)}' )

def convert_files(root_folder):
    for folder in tqdm(os.listdir(root_folder)):
        folder = os.path.join(root_folder, folder)
        for file in tqdm(os.listdir(os.path.join(folder, "RawData")), desc=folder):
            target_path = os.path.join(folder, "ConvertedData", f'{".".join(file.split(".")[:-1])}.mzML')
            if (not os.path.isfile(target_path)) or os.path.getsize(target_path) < 1e8 :
                print(f'Converting {target_path}')
                convert_file(folder, file)

                

 
dask.config.set(scheduler='processes', num_workers = n_workers)
futures = [ dask.delayed(tune_train_single_model_sklearn)( X, ys[org], labels[i], classifier, configuration_space, n_trials,
                                                               source, name, algorithm_name, outdir, fold, verbosity )
                for i, org in enumerate(tqdm(ys.columns))  
              ]
dask.compute(futures)