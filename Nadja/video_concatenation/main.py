
from functions import *

# #####################################################################
# User input
# #####################################################################
path_to_main_folder = Path(r"G:\SleepVideos\stitch\panama\SleepVideos")
path_to_output_folder = path_to_main_folder.joinpath("StitchedSleepVideos")
framerate = 30  # HZ
overwrite = True

FH_string = '2024*'
FH_string = '2024-01-11_Neotama_sp001_female'

experiment_paths = list(path_to_main_folder.glob(FH_string))  # get list of all paths starting with '2024'
for experiment_path in experiment_paths:
    # Paths and names
    experiment_name = experiment_path.stem
    path_to_output_folder.mkdir(exist_ok=True, parents=True)
    concat_path = path_to_output_folder.joinpath(f'{experiment_name}.mp4')
    print(f'{experiment_name}')

    # Check if concatenated file already exists
    if concat_path.exists() and not overwrite:
        print('\t\033[96mConcatenated file already exists\033[0m')
        continue

    # convert_files(experiment_path, overwrite)
    concatenate_files(experiment_path, concat_path, overwrite)
    #delete_part_files(experiment_path)

