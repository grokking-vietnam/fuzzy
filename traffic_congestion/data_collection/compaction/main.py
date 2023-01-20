"""
Simple program to remove unused audio files and zip them to block.
"""

import glob
import io
import multiprocessing
import os
import shutil
import subprocess
import tarfile
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Pool
from typing import List

import ffmpeg
import yaml
from tqdm import tqdm


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def run_cmd(cmd: str) -> None:
    """Runs bash script."""
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
    while p.poll() is None:
        stdout = p.stdout.readline()
        print(stdout)


def to_mono_16khz(filepath: str) -> bool:
    """Converts audio file to mono channel and sampling rate 16khz."""
    try:
        ffmpeg.input(filepath).output(
            filepath.replace(".ts", "") + "_mono_16khz.aac",
            format="adts",
            ar=16000,
            ac=1,
        ).run(quiet=True, overwrite_output=True)
        os.remove(filepath)
    except Exception as ex:
        print(ex)
        if "ffmpeg error" in str(ex):
            os.remove(filepath)
    return True


def compress(output: str, filepaths: List[str]) -> None:
    """Compresses files into tar file."""

    def delete_file(filepath: str):
        os.remove(filepath)

    with tarfile.open(output, "w:gz") as archive:
        for filepath in filepaths:
            with io.BytesIO(open(filepath, "rb").read()) as f:
                info = tarfile.TarInfo(os.path.basename(filepath))
                f.seek(0, io.SEEK_END)
                info.size = f.tell()
                f.seek(0, io.SEEK_SET)
                archive.addfile(info, f)

    with ThreadPoolExecutor(100) as p:
        _ = [p.submit(delete_file, filepath) for filepath in filepaths]
    print("Done")


def move(folder: str):
    shutil.move(folder,
                "/".join(folder.split("/")[0:3] + folder.split("/")[4:]))


if __name__ == "__main__":
    with open("../radio_channels.yaml", "r") as fp:
        try:
            channels = yaml.safe_load(fp)
        except yaml.YAMLError as e:
            print(e)

    for channel in channels["channels"].keys():
        # Download data from GCS
        # if not os.path.exists(f"./radio-project/{channel}"):
        #     os.makedirs(f"./radio-project/{channel}")
        # run_cmd(
        #     cmd=f"gcloud storage cp -R gs://radio-project/{channel} ./radio-project/{channel}"
        # )

        # Convert to mono channel
        # filepaths = glob.glob(f"./radio-project/{channel}/{channel}/*/*/*/*.*")
        # converting_filepaths = [
        #     filepath for filepath in filepaths if "mono" not in filepath
        # ]
        # if len(converting_filepaths) > 0:
        #     for chunk in chunks(lst=converting_filepaths, n=10000):
        #         with Pool(multiprocessing.cpu_count() - 1) as p:
        #             _ = list(
        #                 tqdm(
        #                     p.imap(to_mono_16khz, chunk),
        #                     total=len(chunk),
        #                     desc=f"[{channel}] Converting audio",
        #                 )
        #             )

        # Compress files to 1 hour block
        # folders = glob.glob(f"./radio-project/{channel}/{channel}/*/*/*/")
        # if len(folders) > 0:
        #     for folder in folders:
        #         filepaths = glob.glob(folder + "*.aac")
        #         hours = [
        #             os.path.basename(filepath).split("_")[0] for filepath in filepaths
        #         ]
        #         distinct_hours = list(set(hours))
        #         compressing_filepaths = defaultdict(list)
        #         for i, hour in enumerate(hours):
        #             compressing_filepaths[hour].append(filepaths[i])
        #         for hour, filepaths in compressing_filepaths.items():
        #             compress(output=folder + hour + ".tar.gz", filepaths=filepaths)
        1 == 1
