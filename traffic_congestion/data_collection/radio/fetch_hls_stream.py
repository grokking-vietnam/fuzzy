import datetime
import json
import logging
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import click
import m3u8
from google.cloud import storage
from google.oauth2 import service_account
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

# GCS credentials
CREDENTIALS = service_account.Credentials.from_service_account_file(
    'service-account.json')


def setuplog(verbose):
    """Config the log output of fetch_hls_stream"""
    log_msg_format = '%(asctime)s :: %(levelname)5s ::  %(name)10s :: %(message)s'
    log_date_format = '%Y-%m-%d %H:%M:%S'
    logging.basicConfig(format=log_msg_format, datefmt=log_date_format)
    if verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)


def alert_caching(error_type: str, interval: int) -> bool:
    """Cache the timestamp of error and decide to
    alert or not."""

    now_timestamp = time.time()

    if not os.path.exists("alert_cache.json"):
        with open('alert_cache.json', 'w') as fp:
            fp.write(json.dumps({"dummy": time.time()}))
        return False
    else:
        with open('alert_cache.json', 'r') as fp:
            alert_cache = dict(json.loads(fp.read()))
        prev_timestamp = alert_cache.get(error_type, -1)
        if (now_timestamp - prev_timestamp) > interval:
            alert_cache[error_type] = now_timestamp
            with open('alert_cache.json', 'w') as fp:
                fp.write(json.dumps(alert_cache))
            return True
        else:
            return False


def upload_blob_from_memory(bucket_name, contents, destination_blob_name):
    """Uploads a file to the bucket."""
    storage_client = storage.Client(credentials=CREDENTIALS)
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_string(contents)


def download_file_and_upload_to_gcs(uri, outputdir, filename):
    """Download a ts video and save on the outputdir as the following file:
    outputdir/date_filename"""
    try:
        date = datetime.datetime.now().strftime("%Y/%m/%d/%H_%M_%S")
        fpath = os.path.join(outputdir, date + "_" + filename)

        logger.info("DOWNLOADING FILE: " + uri)
        response = get(uri)
        upload_blob_from_memory(bucket_name="radio-project",
                                contents=response.content,
                                destination_blob_name=fpath)

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
@click.option('--alert', default=5, help="Alert interval in minute")
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
        if alert_caching(error_type=type(ex).__name__, interval=alert * 60):
            telebot_send_message(
                f"Channel *{output}*: {ex} !!! The process has been stopped.")


if __name__ == '__main__':
    fetch_hls_stream()
