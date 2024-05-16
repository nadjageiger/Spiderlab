
from datetime import datetime
import ffmpeg
import dateutil.parser as parser
import sys
import os
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import cv2

# #####################################################################
# User input
# #####################################################################
path_to_main_folder = Path(r"G:\SleepVideos\Portia fimbriata\Ontogenetic change of sleep phases")
framerate = 30  # HZ
overwrite = False

# #####################################################################
# Actual code
# #####################################################################
fourcc = cv2.VideoWriter_fourcc(*'XVID')

# seconds converts a time to seconds since midnight
def seconds(time):
    return (time.hour * 60 + time.minute) * 60 + time.second

# # Delete all mp4 files
# for p in path_to_main_folder.glob('FH*/**/part_*.mp4'):
#     try:
#         p.unlink()
#     except Exception as e:
#         print(p, e)

folder_paths = [list(path_to_main_folder.glob('FH*'))[0]]  # get list of all paths starting with 'FH'
for folder_path in folder_paths:
    # Get list of all paths in folder
    experiment_paths = [list(folder_path.glob('*'))[0]]
    for experiment_path in experiment_paths:
        experiment_name = experiment_path.stem
        print(f'{folder_path.stem} {experiment_name}')

        # #####################################################################
        # Check if concatenated file already exists
        # #####################################################################
        concat_path = experiment_path.joinpath(f'{experiment_name}.mp4')
        if concat_path.exists() and not overwrite:
            print('\tConcatenated file already exists')
            continue

        # #####################################################################
        # Convert file to mp4 and add timestamp
        # #####################################################################
        print(f'\tSTART CONVERSION')
        # Get list of all paths to MOV files
        mov_paths = list(experiment_path.glob('*.MOV'))
        # Loop over movie files
        for mov_num, mov_path in enumerate(mov_paths):
            print(f"\t{mov_num: 3d}/{len(mov_paths)}\t{mov_path}")
            file_stem = mov_path.stem
            input_path = str(mov_path)
            output_path = experiment_path.joinpath(f'part_{file_stem}.mp4')

            if output_path.exists() and not overwrite:
                print(f'\t\tFile already converted')
                continue

            cap = cv2.VideoCapture(input_path)
            if not cap.isOpened():
                print("could not open :", mov_path)
                continue

            # Extract metadata
            creation_time = os.path.getmtime(mov_path)  # seconds
            total_frame_numbers = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = 30  # cap.get(cv2.CAP_PROP_FPS)
            # print(f'\t\tCreated    {datetime.utcfromtimestamp(creation_time).strftime("%Y-%m-%d %H:%M:%S")}')
            # print(f'\t\tFPS        {fps} Hz')

            out = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))

            for frame_number in range(total_frame_numbers):
                # if frame_number > 100:
                #     break

                frame_time = creation_time + frame_number / fps
                time_stamp = datetime.utcfromtimestamp(frame_time).strftime('%Y-%m-%d %H:%M:%S.%f')
                print(f'\t{mov_num: 3d}/{len(mov_paths)}\t{mov_path} Converting frame {frame_number: 7d}/{total_frame_numbers} ({time_stamp})', end='\r')

                # Read video by read() function, extract and return the frame
                ret, img = cap.read()

                # Put current DateTime on each frame
                font = cv2.FONT_HERSHEY_PLAIN
                cv2.putText(
                    img,
                    time_stamp,
                    (0, height),
                    font, 2, (255, 255, 255), 2, cv2.LINE_AA)

                out.write(img)
            cap.release()
            out.release()
            # Stop overwriting last frame
            print(f'\t{mov_num: 3d}/{len(mov_paths)}\t{mov_path} Converting frame {frame_number: 7d}/{total_frame_numbers} ({time_stamp})')

            # close open windows
            cv2.destroyAllWindows()

        # #####################################################################
        # Concatenate files
        # #####################################################################
        def print_time(name, timestamp):
            return print(f'{name}:\t\t', datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S.%f'))

        # Get paths
        mov_paths = sorted(experiment_path.glob('*.MOV'))
        mp4_paths = sorted((experiment_path.glob('part_*.mp4')))  # sorted required to get first video for absolute time

        print(f'\tSTART CONCATENATION\n'
              f'\t\tDestination: {output_path}')

        # Get state date from first file
        abs_time = os.path.getmtime(mov_paths[0])  # seconds

        # Get metadata by opening first video
        cap = cv2.VideoCapture(str(mp4_paths[0]))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = 30  # cap.get(cv2.CAP_PROP_FPS)
        cap.release()

        # Create output VideoWriter
        if concat_path.exists() and not overwrite:
            print(f'\t\tConcatenated file already exists')
            continue
        out = cv2.VideoWriter(str(concat_path), 'mp4v', fps, (width, height))

        # Loop over movie files
        for mov_num, mov_path in enumerate(mov_paths):
            print(f"\t{mov_num: 3d}/{len(mp4_paths)}\t{mov_path.stem}")
            mp4_path = mov_path.parent.joinpath('part_' + mov_path.stem + '.mp4')

            # Extract start and end date from original file
            curr_start_time = os.path.getmtime(mov_path)  # seconds
            _cap = cv2.VideoCapture(str(mp4_path))
            curr_total_frame_numbers = int(_cap.get(cv2.CAP_PROP_FRAME_COUNT))
            _cap.release()

            curr_duration = curr_total_frame_numbers / fps  # seconds
            curr_end_time = curr_start_time + curr_duration  # seconds

            duration_difference = curr_start_time - abs_time

            # print_time('\t\tabs_time            ', abs_time)
            # print_time('\t\tcurr_start_time     ', curr_start_time)
            # print_time('\t\tcurr_duration       ', curr_duration)
            # print_time('\t\tcurr_end_time       ', curr_end_time)
            # print_time('\t\tduration_difference ', duration_difference)

            for frame_number in range(int(duration_difference*fps)):
                # if frame_number > 100:
                #     continue
                # Write black frame
                black_frame = np.zeros((height, width, 3))
                # Put current DateTime on each frame
                frame_time = abs_time + frame_number / fps
                time_stamp = datetime.utcfromtimestamp(frame_time).strftime('%Y-%m-%d %H:%M:%S.%f')
                out.write(black_frame)

            # Add current frames
            curr_cap = cv2.VideoCapture(str(mp4_path))
            while curr_cap.isOpened():
                # Get return value and curr frame of curr video
                res, frame = curr_cap.read()
                if not res:
                    break
                # Write the frame
                out.write(frame)
            curr_cap.release()
            abs_time = curr_end_time

        # Save the video
        out.release()

        # #####################################################################
        # Delete part_ files
        # #####################################################################
        part_files = experiment_path.glob('part_*.mp4')
        # Loop over movie files
        for mov_num, part_file in enumerate(part_files):
            try:
                part_file.unlink()
                print(f"\t{mov_num: 3d}/{len(mp4_paths)}\t{part_file.name} deleted")
            except PermissionError as e:
                print(e)

        print('DONE :)')

