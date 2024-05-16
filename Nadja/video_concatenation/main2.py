
from functions import *

# #####################################################################
# User input
# #####################################################################
path_to_main_folder = Path(r"G:\SleepVideos\Portia fimbriata\Ontogenetic change of sleep phases\Not stitched yet")
path_to_output_folder = path_to_main_folder.joinpath("StitchedSleepVideos")
framerate = 30  # HZ
overwrite = False

FH_string = 'FH*'

folder_paths = list(path_to_main_folder.glob(FH_string))  # get list of all paths starting with 'FH'
for folder_path in folder_paths:
    # Get list of all paths in folder
    experiment_paths = list(folder_path.glob('*'))
    for experiment_path in experiment_paths:
        # Paths and names
        experiment_name = experiment_path.stem
        path_to_output_folder.mkdir(exist_ok=True, parents=True)
        concat_path = path_to_output_folder.joinpath(f'{folder_path.stem}_{experiment_name}.mp4')
        print(f'{folder_path.stem} {experiment_name}')

        # Check if concatenated file already exists
        if concat_path.exists() and not overwrite:
            print('\t\033[96mConcatenated file already exists\033[0m')
            continue

        convert_files(experiment_path, overwrite)
        concatenate_files(experiment_path, concat_path, overwrite)
        delete_part_files(experiment_path)

