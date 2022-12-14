##############################################
############      IMPORTS         ############
##############################################

import os
import logging
import argparse
import json
import subprocess
import shutil
from tqdm import tqdm

logging.basicConfig(level=logging.INFO)
# Example: 5:22/5:35
frame_separator = "_"
time_separator = "/"
audio_track = 0
output_folder = "output"

##############################################
############      METHODS         ############
##############################################


def get_base_filename(filename: str):
    # Returns the exact basename of a file
    return os.path.splitext(os.path.basename(filename))[0]


def use_alphabet_only(string: str, characters: str):
    # Checks if a string uses only the given characters
    for char in string:
        if characters.find(char) == -1:
            return False
    return True


def frames_valid(frames: list):
    # will check for each frame if it using the specified alphabet only
    for frame in frames:
        # "start" and "end" of frame
        for sub_frame in frame:
            if not use_alphabet_only(frame[sub_frame], f"0123456789:{time_separator}{frame_separator}"):
                return False
    return True


def frame_str_to_obj(frame_str: str):
    # Returns a Dict object from a unique frame str
    frame = frame_str.split(time_separator)
    return {"start": frame[0], "end": frame[1]}


def cut_video(filename: str, frames: list, audio_track=0):
    # Cut the video following the example below:
    # ./ffmpeg -i "$file" -ss $timeframes[$i][0] -to $timeframes[$i][1]  -map_chapters -1 -map 0:v:0 -map 0:a:$audio_track "$filename-$i.mp4";
    frame_count = 0
    frame: dict

    # Sort by alphabetical order
    frames = sorted(frames, key=lambda frame: frame["start"])
    logging.debug(frames)

    command = ["ffmpeg", "-hide_banner", "-loglevel", "error"]

    for frame in frames:
        logging.debug(f"Treating frame {frame}...")
        command += ["-i", filename, "-ss", frame["start"], "-to", frame["end"], "-map_chapters",
                    "-1", "-map", "0:v:0", "-map", f"0:a:{audio_track}", f"{output_folder}/{get_base_filename(filename)}-{frame_count}.mp4"]
        frame_count += 1

    logging.debug(" ".join(command))
    # Execute command
    process = subprocess.Popen(command, shell=True)
    process.wait()


##############################################
############        MAIN          ############
##############################################
""" 3 cas possibles

    - On insère les frames une par une, pour chaque vidéo
    - On drop un json qui donne automatiquement les vidéos et les frames à couper
    - On insère la totalité des frames une fois pour chaque vidéo
"""

parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("-f", "--file", dest="file", type=str,
                    nargs="?", help="The text file containing the filenames and the frames to cut")
parser.add_argument("-a", "--audio", dest="audio", type=int,
                    nargs="?", default=0, help="The audio track of the file (to change language)")
parser.add_argument("-e", "--extension", dest="video_ext", type=str,
                    nargs="?", default="mp4", help="The file extension, if missing in file")
args = parser.parse_args()

# The mode is either 'json' reading, 'special_file' for various file content or 'video' reading
mode = "video"
current_filename = None
first = True

if __name__ == "__main__":

    # Check if ffmpeg exists
    if not shutil.which("ffmpeg") and not os.path.isfile("ffmpeg.exe"):
        logging.error(
            "Error! FFMPEG binary not found, please place it on working directory or in PATH variables.")
        exit()

    # Create the output folder if doesnt exist
    try:
        if len(os.listdir(output_folder)) > 0:
            logging.error(
                f"{output_folder} folder exists and is not empty, please remove its content before launching.")
            exit()
    except FileNotFoundError:
        os.mkdir(output_folder)

    # will store all data to process for FFMPEG
    video_per_frame = {}

    # First, check if audio_track changed from default
    audio_track = int(args.audio)
    if audio_track < 0:
        logging.error(
            "Error! Audio track index below 0, returning to default.")
        audio_track = 0

    # Premier cas : on spécifie un fichier JSON à lire
    # Example : [ {"file": "XXX", "frames": "YY:YY/ZZ:ZZ"} ]
    if args.file != None:
        try:
            with open(args.file, "r") as f:
                content = f.read()
        except:
            logging.error(f"Error! Could not read {args.file}. Exiting...")
            exit()

        # Putting back to 'json'
        mode = "json"
        json_content = None
        try:
            # Determining the mode (if readable and JSON loadable)
            content.encode("ascii")
            json_content = json.loads(content)
        except UnicodeDecodeError:
            mode = "video"
        except(json.JSONDecodeError, TypeError):
            mode = "special_file"

        # if json mode
        if mode == "json":
            for sub_json in json_content:
                # if 'file' and 'frames' key exist
                if sub_json["file"] != None and sub_json["frames"] != None:
                    video_per_frame[sub_json["file"]] = []
                    for frame in sub_json["frames"]:

                        # if multiple frames at one
                        if frame_separator in frame:
                            for sub_frame in frame.split(frame_separator):
                                video_per_frame[sub_json["file"]].append(
                                    sub_frame)
                        else:
                            video_per_frame[sub_json["file"]].append(frame)

                else:
                    # simply assign the json to the content
                    video_per_frame = json_content

            logging.info("JSON loaded, processing videos...")

    # if loading special file
    if mode == "special_file":
        lines = content.split("\n")
        current_video = None

        for line in lines:
            # if file not empty
            if len(line.replace(" ", "")) > 0:
                # we check if this line respresents a file

                # if no extension, try to add it
                if os.path.isfile(f"{line}.{args.video_ext}"):
                    line += f".{args.video_ext}"

                if os.path.isfile(line):
                    current_filename = line
                    video_per_frame[current_filename] = []
                elif use_alphabet_only(line, f"0123456789:{time_separator}{frame_separator}"):
                    # if valid frame cut
                    if frame_separator in line:
                        for frame_str in line.split(frame_separator):
                            video_per_frame[current_filename].append(
                                frame_str_to_obj(frame_str))
                    else:
                        video_per_frame[current_filename].append(
                            frame_str_to_obj(line))

        logging.info("File loaded, processing videos...")

    # if video reading mode
    if mode == "video":
        finish = False
        while not finish:

            # Select the filename
            valid_file = False
            while not valid_file:
                # Only ask if we didn't enter a file as parameter
                if not first or not args.file:
                    current_filename = input("Enter the video filename:\n>>> ")

                # if we stop entering file data
                if current_filename.lower() == "stop":
                    finish = True
                    break

                valid_file = os.path.isfile(current_filename)
                if not valid_file:
                    logging.error("Error! File not found!")

            # If 'stop' entered earlier
            if finish:
                break

            # Now that we entered the correct file, change the 'first' variable
            first = False

            video_per_frame[current_filename] = []

            # Manually specify each cut
            frame_array = []
            finished_entering_frames = False

            while not finished_entering_frames:
                frame_str = input(
                    f"Enter the frame to cut (stop to quit):\nxx:xx{time_separator}yy:yy{frame_separator}xx...\n>>> ")

                # If we want to stop
                if frame_str.lower() == "stop":
                    finished_entering_frames = True

                # If multiple frames inside
                elif frame_separator in frame_str:
                    for sub_frame_str in frame_str.split(frame_separator):
                        frame_array.append(frame_str_to_obj(sub_frame_str))

                # If only one frame
                elif time_separator in frame_str:
                    frame_array.append(frame_str_to_obj(frame_str))
                else:
                    logging.error("Wrong frame syntax, please retry")

            logging.info("Data saved, type 'stop' to keep on processing")
            video_per_frame[current_filename] = frame_array

        logging.info("Data loaded, processing videos...")

    # process videos
    for video_name in tqdm(video_per_frame, colour="red"):

        # if no extension, try to add it
        if os.path.isfile(f"{video_name}.{args.video_ext}"):
            video_name += f".{args.video_ext}"

        if not os.path.isfile(video_name):
            logging.error(
                f"File {video_name} not found, skipping")
        elif not frames_valid(video_per_frame[video_name]):
            logging.error(
                f"The frames of {video_name} are not valid, skipping...")
        else:
            cut_video(
                video_name, video_per_frame[video_name], audio_track)

    logging.info("Program ended")
