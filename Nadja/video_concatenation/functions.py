
from contextlib import contextmanager
from datetime import datetime, timedelta
import ffmpeg
import dateutil.parser as parser
import sys
import os
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import cv2


@contextmanager
def get_video_capture(path):
    '''Context manager to ensure VideoCapture result is always released.'''
    cap = cv2.VideoCapture(str(path))
    try:
        yield cap
    finally:
        cap.release()


@contextmanager
def get_video_writer(path, *args):
    out = cv2.VideoWriter(str(path), *args)
    try:
        yield out
    finally:
        out.release()


def get_black_frame(height, width):
    return np.zeros((height, width, 3))


def convert_files(experiment_path: Path, overwrite: bool, fourcc: int = cv2.VideoWriter_fourcc(*'mp4v')):
    print(f'\tSTART CONVERSION')
    # Get list of all paths to MOV files
    mov_paths = sorted(experiment_path.glob('*.MOV'))
    # Loop over movie files
    for mov_num, mov_path in enumerate(mov_paths):
        print(f"\t{mov_num + 1: 3d}/{len(mov_paths)}\t{mov_path}", end='\r')
        file_stem = mov_path.stem
        input_path = str(mov_path)
        output_path = experiment_path.joinpath(f'part_{file_stem}.mp4')

        if output_path.exists() and not overwrite:
            print(f' \033[96mFile already converted\033[0m')
            continue

        cap = cv2.VideoCapture(input_path)
        if not cap.isOpened():
            print(f" \033[93mcould not open {mov_path}\033[0m")
            continue

        # Extract metadata
        # creation_time = os.path.getctime(mov_path)  # seconds
        total_frame_numbers = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = 30  # cap.get(cv2.CAP_PROP_FPS)

        # Create VideoWriter
        out = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))

        frame_number = 0
        while cap.isOpened():
            # Read video by read() function, extract and return the frame
            res, frame = cap.read()
            if not res:
                # Close VideoCapture
                break

            # Put current DateTime on each frame
            # frame_time = creation_time + frame_number / fps
            # time_stamp = datetime.utcfromtimestamp(frame_time).strftime('%Y-%m-%d %H:%M:%S.%f')
            # text = f'{frame_number: 5.0f}: {frame_number / fps: 5.0f}s'
            # font = cv2.FONT_HERSHEY_PLAIN
            # cv2.putText(
                #     frame,
                #     text,
                #     (0, height),
            #     font, 2, (255, 255, 255), 2, cv2.LINE_AA)

            # Write to VideoConverter
            print(f"\t{mov_num + 1: 3d}/{len(mov_paths)}\t{mov_path} (frame {frame_number: 7d}/{total_frame_numbers})", end='\r')
            out.write(frame)
            frame_number += 1
        cap.release()

        # Save video
        out.release()

        # close open windows
        cv2.destroyAllWindows()

        # Final print output
        print(f'\t{mov_num + 1: 3d}/{len(mov_paths)}\t{mov_path} \033[92mdone\033[0m', end='\r')
    print('\t\033[92mConversion done\033[0m')


def concatenate_files(experiment_path: Path, concat_path: Path, overwrite: bool, fourcc: int = cv2.VideoWriter_fourcc(*'mp4v')):
    print(f'\tSTART CONCATENATION')
    # Get paths
    mov_paths = sorted(experiment_path.glob('*.MOV'))  # sorted required to get files in ascending order
    mp4_paths = sorted((experiment_path.glob('part_*.mp4')))  # sorted required to get first video for absolute time

    # Check if mp4_paths is empty
    if not mp4_paths:
        print("No MP4 files found. Aborting concatenation.")
        return

    # Get width, height, fps by opening first video
    with get_video_capture(str(mp4_paths[0])) as cap:
        cap = cv2.VideoCapture(str(mp4_paths[0]))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)

    # Create output VideoWriter
    if concat_path.exists() and not overwrite:
        print(f'\t\t\033[96mConcatenated file already exists\033[0m')
        return

    with get_video_writer(str(concat_path), fourcc, fps, (width, height)) as out:
        # out = cv2.VideoWriter(str(concat_path), fourcc, fps, (width, height))

        # Loop over movie files
        prev_mov_end_time = None
        for mov_num, mov_path in enumerate(mov_paths):
            mp4_path = mov_path.parent.joinpath('part_' + mov_path.stem + '.mp4')
            print(f"\t{mov_num + 1: 3d}/{len(mp4_paths)}\t{mp4_path.name}")

            # Calculate the duration of this movie
            # _cap = cv2.VideoCapture(str(mp4_path))
            # total_frame_numbers = int(_cap.get(cv2.CAP_PROP_FRAME_COUNT))
            # _cap.release()
            with get_video_capture(str(mp4_path)) as cap:
                total_frame_numbers = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            curr_duration = timedelta(seconds=total_frame_numbers / fps)  # seconds

            # Get start and end time of this movie based on mov_path
            mov_start_time = datetime.fromtimestamp(os.path.getmtime(mov_path))
            mov_end_time = mov_start_time + curr_duration
            print(
                f'\t\t\tprev_mov_end_time:', prev_mov_end_time,
                f'\n\t\t\tmov_start_time:   ', mov_start_time,
                f'\n\t\t\tmov_end_time:     ', mov_end_time,
                f'\n\t\t\tcurr_duration:    ', curr_duration,
            )

            # Add black frames to fill gap between videos
            while prev_mov_end_time and mov_start_time > prev_mov_end_time:
                prev_mov_end_time += timedelta(seconds=1 / fps)  # Update time with one frame
                # print('Add black frame at', prev_mov_end_time)

                # Add black frame
                frame = get_black_frame(height, width)

                # Add timestamp to frame
                timestamp = prev_mov_end_time  # Calculate timestamp
                text = timestamp.strftime('%Y-%m-%d %H:%M:%S')
                cv2.putText(
                    frame,
                    text,
                    (10, height - 30),
                    cv2.FONT_HERSHEY_PLAIN, 1, (255, 255, 255), 1, cv2.LINE_AA)

                out.write(frame)

            # Add frames with timestamp
            with get_video_capture(str(mp4_path)) as curr_cap:
                # curr_cap = cv2.VideoCapture(str(mp4_path))
                frame_number = 0
                while curr_cap.isOpened():
                    res, frame = curr_cap.read()
                    if not res:
                        break

                    # Add timestamp to frame
                    timestamp = mov_start_time + timedelta(seconds=(frame_number / fps))  # Calculate timestamp
                    text = timestamp.strftime('%Y-%m-%d %H:%M:%S')
                    cv2.putText(
                        frame,
                        text,
                        (10, height - 30),
                        cv2.FONT_HERSHEY_PLAIN, 3, (255, 255, 255), 1, cv2.LINE_AA)

                    # Write the frame
                    out.write(frame)
                    frame_number += 1

                # curr_cap.release()

            # Update previous end time
            prev_mov_end_time = mov_end_time

    # After we have concatenated all files, we can save the video
    # out.release()

    # Final print statement
    print('\t\033[92mConcatenation done\033[0m')


def delete_part_files(experiment_path: Path, ):
    glob_string = 'part_*.mp4'
    part_files = list(experiment_path.glob(glob_string))
    print(f'\tDeleting files with {glob_string}')
    # Loop over movie files
    for mov_num, part_file in enumerate(part_files):
        try:
            part_file.unlink()
        except PermissionError as e:
            print(e)


