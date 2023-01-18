"""
Simple program to remove unused audio files and zip them to block.
"""

import glob
import multiprocessing
import os
import subprocess
from multiprocessing import Pool

import ffmpeg
import yaml
from tqdm.auto import tqdm


def run_cmd(cmd: str) -> None:
    """Runs bash script."""
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
    while p.poll() is None:
        stdout = p.stdout.readline()
        print(stdout)


def to_mono_16khz(filename: str) -> None:
    """Converts audio file to mono channel and sampling rate 16khz."""
    ffmpeg.input(filename).output(filename.replace(".aac", "") +
                                  "_mono_16khz.aac",
                                  format="adts",
                                  ar=16000,
                                  ac=1).run(quiet=True, overwrite_output=True)
    os.remove(filename)


if __name__ == "__main__":
    with open("radio_channels.yaml", "r") as fp:
        try:
            channels = yaml.safe_load(fp)
        except yaml.YAMLError as e:
            print(e)

    for channel in channels["channels"].keys():
        os.makedirs(f"compaction/radio-project/{channel}")
        run_cmd(
            cmd=
            f"gcloud storage cp -R gs://radio-project/{channel} compaction/radio-project/{channel}"
        )

        filenames = glob.glob(
            f"compaction/radio-project/{channel}/{channel}/*/*/*/*.aac")
        compressing_filenames = [
            filename for filename in filenames if "mono" not in filename
        ]
        with Pool(multiprocessing.cpu_count() - 1) as p:
            _ = list(
                tqdm(
                    p.imap(to_mono_16khz, compressing_filenames),
                    total=len(compressing_filenames),
                ))
