import datetime
import json
import logging
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from pathlib import Path

import click
import ffmpeg
import m3u8
from requests import get

sys.path.append(
    Path(__file__).parent.absolute().as_posix())  # Add radio/ to root path

from compaction import main as compaction_main
from utils.aws import list_blob, write_buf_to_s3
from utils.notification import telebot_send_message

# Set representing chunks that we have already downloaded
dlset = set()

# Download Pool
dlpool = ThreadPoolExecutor(max_workers=4)

# Logger
logger = logging.getLogger("fetch_hls_stream")

# AWS
BUCKET_NAME = "radio-project"

# Running hours
RUNNING_HOURS = range(6, 22)


def setuplog(verbose):
    """Configs the log output of fetch_hls_stream"""
    log_msg_format = "%(asctime)s :: %(levelname)5s ::  %(name)10s :: %(message)s"
    log_date_format = "%Y-%m-%d %H:%M:%S"
    logging.basicConfig(format=log_msg_format, datefmt=log_date_format)
    if verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)


def to_alert(bucket_name: str,
             output_dir: str,
             interval: int,
             running_hours=range(6, 22)) -> bool:
    """Fetches the latest timestamp of data and decides to
    alert or not."""
    date = datetime.datetime.utcnow().strftime("%Y/%m/%d")
    prefix = os.path.join(output_dir, date)
    latest_timestamp = max([
        blob.last_modified
        for blob in list_blob(bucket_name=bucket_name, prefix=prefix)
    ])
    return (
        (datetime.datetime.utcnow().timestamp() - latest_timestamp.timestamp())
        > interval) & (datetime.datetime.utcnow().hour in running_hours)


def download_file_and_upload_to_aws(uri, output_dir, filename) -> None:
    """Download a ts audio and save on the output_dir as the following file:
    output_dir/date_filename"""
    try:
        date = datetime.datetime.utcnow().strftime("%Y/%m/%d/%H_%M_%S")
        fpath = os.path.join(
            output_dir,
            date + "_" + filename.split(".")[0] + "_mono_16khz.aac")

        logger.info("DOWNLOADING FILE: " + uri)
        response = get(uri, verify=False)

        # Convert audio to mono channel and 16 kHz
        if not os.path.exists("/home/radio/tmp"):
            os.makedirs("/home/radio/tmp")
        with open(os.path.join("/home/radio/tmp", filename), "wb") as fp:
            fp.write(response.content)

        audio, _ = (ffmpeg.input(os.path.join(
            "/home/radio/tmp",
            filename)).output("-", format="adts", ar=16000,
                              ac=1).run(cmd="/home/radio/johnvansickle/ffmpeg",
                                        capture_stdout=True))

        write_buf_to_s3(contents=audio,
                        bucket_name=BUCKET_NAME,
                        object_name=fpath)

        os.remove(os.path.join("/home/radio/tmp", filename))

        logger.debug("FINISHED WRITING " + uri + " TO S3: " + fpath)

        # Comment all the code in the try block and
        # raise a Exception here to test the alert.
        # raise Exception("Fake exception!")
    except Exception as ex:
        logger.exception(ex)

        # Re-raise exception to catch it from outside
        raise Exception(f"Cannot download file and upload to S3 due to: {ex}")


@click.command()
@click.option("--url",
              default=os.getenv("M3U8_URL"),
              help="URL to HLS m3u8 playlist")
@click.option("--freq",
              default=10,
              help="Frequency for downloading the HLS m3u8 stream")
@click.option("--output",
              default=os.getenv("OUTPUT_DIR"),
              help="Output directory for audio files")
@click.option("--verbose", is_flag=True, help="Verbose")
@click.option("--alert",
              default=os.getenv("ALERT"),
              help="Alert interval in minute")
def fetch_hls_stream(url, freq, output, verbose, alert):
    """Fetches a HLS stream by periodically retrieving the m3u8 url for new
    playlist audio files every freq seconds. For each segment that exists,
    it downloads them to the output directory as a AAC audio file."""

    try:
        setuplog(verbose)

        if not os.path.exists(output):
            os.makedirs(output)

        while True:
            if (datetime.datetime.utcnow() +
                    datetime.timedelta(hours=7)).hour in RUNNING_HOURS:
                # Retrieve the main m3u8 dynamic playlist file
                dynamic_playlist = m3u8.load(url, verify_ssl=False)
                if len(dynamic_playlist.playlists) > 0:
                    # Retrieve the real m3u8 playlist file from the dynamic one
                    for playlist in dynamic_playlist.playlists:
                        # Check if we have each segment in the playlist file
                        playlist_data = m3u8.load(playlist.absolute_uri,
                                                  verify_ssl=False)

                        for audio_segment in playlist_data.segments:
                            # Since the playlist changes names dynamically we use the
                            # last part of the uri (vfname) to identify segments
                            audio_uri = audio_segment.absolute_uri
                            audio_fname = audio_uri.split("_")[-1]

                            if audio_fname not in dlset:
                                dlset.add(audio_fname)
                                task = dlpool.submit(
                                    download_file_and_upload_to_aws,
                                    audio_uri,
                                    output,
                                    audio_fname,
                                )

                                # Exception handling outside the task submit()
                                # => the task has to raise Exception first.
                                _ = task.result()
                elif len(dynamic_playlist.segments) > 0:
                    # Dynamic playlist file is also a playlist
                    playlist_data = deepcopy(dynamic_playlist)

                    for audio_segment in playlist_data.segments:
                        # Since the playlist changes names dynamically we use the
                        # last part of the uri (vfname) to identify segments
                        audio_uri = audio_segment.absolute_uri
                        audio_fname = audio_uri.split("/")[-1]

                        if audio_fname not in dlset:
                            dlset.add(audio_fname)
                            task = dlpool.submit(
                                download_file_and_upload_to_aws,
                                audio_uri,
                                output,
                                audio_fname,
                            )

                            # Exception handling outside the task submit()
                            # => the task has to raise Exception first.
                            _ = task.result()
            else:
                # Run compaction to reduce size and upload to AWS S3
                today = datetime.datetime.utcnow().strftime("%Y%m%d")
                if not os.path.exists(f"./{output}.cache.json"):
                    with open(f"./{output}.cache.json", "w",
                              encoding="utf-8") as f:
                        json.dump(
                            {today: False},
                            f,
                            ensure_ascii=False,
                            indent=4,
                        )
                completion_flag = json.load(open(f"./{output}.cache.json",
                                                 "r"))
                if not completion_flag.get(today, False):
                    compaction_main(channel=output,
                                    running_hours=RUNNING_HOURS)
                    completion_flag[today] = True
                    with open(f"./{output}.cache.json", "w",
                              encoding="utf-8") as f:
                        json.dump(
                            completion_flag,
                            f,
                            ensure_ascii=False,
                            indent=4,
                        )
                else:
                    logger.info("SLEEPING")

            # Sleep until next check
            time.sleep(freq)
    except Exception as ex:
        logger.exception(ex)
        if to_alert(
                bucket_name=BUCKET_NAME,
                output_dir=output,
                interval=int(alert) * 60,
                running_hours=RUNNING_HOURS,
        ):
            telebot_send_message(
                f"Channel *{output}*: {ex} !!! No data in the last {alert} minutes."
            )


if __name__ == "__main__":
    fetch_hls_stream()
