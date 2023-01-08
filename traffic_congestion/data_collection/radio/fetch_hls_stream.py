import datetime
import logging
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import List

import click
import m3u8
from google.cloud import storage
from google.cloud.storage.blob import Blob
from google.oauth2 import service_account
from pydub import AudioSegment
from requests import get

sys.path.append(
    Path(__file__).parent.absolute().as_posix())  # Add radio/ to root path

from utils.notification import telebot_send_message

# Set representing chunks that we have already downloaded
dlset = set()

# Download Pool
dlpool = ThreadPoolExecutor(max_workers=4)

# Logger
logger = logging.getLogger("fetch_hls_stream")

# GCS
BUCKET_NAME = "radio-project"
CREDENTIALS = service_account.Credentials.from_service_account_file(
    'service-account.json')


def setuplog(verbose):
    """Configs the log output of fetch_hls_stream"""
    log_msg_format = '%(asctime)s :: %(levelname)5s ::  %(name)10s :: %(message)s'
    log_date_format = '%Y-%m-%d %H:%M:%S'
    logging.basicConfig(format=log_msg_format, datefmt=log_date_format)
    if verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)


def to_alert(bucket_name: str, output_dir: str, interval: int) -> bool:
    """Fetches the latest timestamp of data and decides to
    alert or not."""
    date = datetime.datetime.now().strftime("%Y/%m/%d")
    prefix = os.path.join(output_dir, date)
    latest_timestamp = max([
        blob.updated
        for blob in list_blob(bucket_name=bucket_name, prefix=prefix)
    ])
    return (datetime.datetime.utcnow().timestamp() -
            latest_timestamp.timestamp()) > interval


def list_blob(bucket_name, prefix) -> List[Blob]:
    """Lists the blobs inside a bucket with prefix."""
    storage_client = storage.Client(credentials=CREDENTIALS)
    return [
        blob for blob in storage_client.list_blobs(bucket_name, prefix=prefix)
    ]


def upload_blob_from_memory(bucket_name, contents,
                            destination_blob_name) -> None:
    """Uploads a file to the bucket."""
    storage_client = storage.Client(credentials=CREDENTIALS)
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_string(contents)


def download_file_and_upload_to_gcs(uri, output_dir, filename) -> None:
    """Download a ts video and save on the output_dir as the following file:
    output_dir/date_filename"""
    try:
        date = datetime.datetime.now().strftime("%Y/%m/%d/%H_%M_%S")
        fpath = os.path.join(
            output_dir,
            date + "_" + filename.split(".")[0] + "_mono_16khz.aac")

        logger.info("DOWNLOADING FILE: " + uri)
        response = get(uri)

        # Convert audio to mono channel and 16 kHz
        if not os.path.exists("var"):
            os.makedirs("var")
        with open(os.path.join("var", filename), "wb") as fp:
            fp.write(response.content)

        audio = AudioSegment.from_file(os.path.join("var", filename))
        audio = audio.set_channels(1).set_frame_rate(16000)
        audio.export(os.path.join("var",
                                  filename.split(".")[0] + "_mono_16khz.aac"),
                     format="adts")
        # audio, _ = ffmpeg.input(os.path.join(
        #     "var", filename)).output('-', format="adts", ar=16000,
        #                              ac=1).run(cmd="/home/radio/bin/ffmpeg",
        #                                        capture_stdout=True)

        upload_blob_from_memory(bucket_name=BUCKET_NAME,
                                contents=open(os.path.join("var", filename),
                                              "rb").read(),
                                destination_blob_name=fpath)

        os.remove(os.path.join("var", filename))

        logger.debug("FINISHED WRITING " + uri + " TO GCS: " + fpath)

        # Comment all the code in the try block and
        # raise a Exception here to test the alert.
        # raise Exception("Fake exception!")
    except Exception as ex:
        logger.exception(ex)

        # Re-raise exception to catch it from outside
        raise Exception(f"Cannot download file and upload to GCS due to: {ex}")


@click.command()
@click.option('--url',
              default=os.getenv("M3U8_URL"),
              help='URL to HLS m3u8 playlist')
@click.option('--freq',
              default=10,
              help="Frequency for downloading the HLS m3u8 stream")
@click.option('--output',
              default=os.getenv("OUTPUT_DIR"),
              type=click.Path(exists=True),
              help="Output directory for video files")
@click.option('--verbose', is_flag=True, help="Verbose")
@click.option('--alert',
              default=os.getenv("ALERT"),
              help="Alert interval in minute")
def fetch_hls_stream(url, freq, output, verbose, alert):
    """Fetch a HLS stream by periodically retrieving the m3u8 url for new
    playlist video files every freq seconds. For each segment that exists,
    it downloads them to the output directory as a TS video file."""

    try:
        setuplog(verbose)

        while True:
            # Retrieve the main m3u8 dynamic playlist file
            dynamic_playlist = m3u8.load(url)

            # Retrieve the real m3u8 playlist file from the dynamic one
            for playlist in dynamic_playlist.playlists:
                # Check if we have each segment in the playlist file
                playlist_data = m3u8.load(playlist.absolute_uri)

                for audio_segment in playlist_data.segments:
                    # Since the playlist changes names dynamically we use the
                    # last part of the uri (vfname) to identify segments
                    audio_uri = audio_segment.absolute_uri
                    audio_fname = audio_uri.split("_")[-1]

                    if audio_fname not in dlset:
                        dlset.add(audio_fname)
                        task = dlpool.submit(download_file_and_upload_to_gcs,
                                             audio_uri, output, audio_fname)

                        # Exception handling outside the task submit()
                        # => the task has to raise Exception first.
                        _ = task.result()

            # Sleep until next check
            time.sleep(freq)
    except Exception as ex:
        logger.exception(ex)
        if to_alert(bucket_name=BUCKET_NAME,
                    output_dir=output,
                    interval=int(alert) * 60):
            telebot_send_message(
                f"Channel *{output}*: {ex} !!! No data in the last {alert} minutes."
            )


if __name__ == '__main__':
    fetch_hls_stream()
