# Video-cutter

Python script using ffmpeg binary to cut video files.

# How to use

There are two different ways to cut files:
- With no option provided, you can manually type the video filename and the frames to cut
- You can provide a text filename with the information syntaxed like [a relative link](example.txt)

usage: video_cutter.py [-h] [-f [FILE]] [-a [AUDIO]] [-e [VIDEO_EXT]]

options:
  -h, --help            show this help message and exit
  -f [FILE], --file [FILE]
                        The text file containing the filenames and the frames to cut (default: None)
  -a [AUDIO], --audio [AUDIO]
                        The audio track of the file (to change language) (default: 0)
  -e [VIDEO_EXT], --extension [VIDEO_EXT]
                        The file extension, if missing in file (default: mp4)