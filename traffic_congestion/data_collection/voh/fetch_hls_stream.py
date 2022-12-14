import datetime
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor

import click
import m3u8
from google.cloud import storage
from google.oauth2 import service_account
from requests import get

import sys
from pathlib import Path

sys.path.append(Path(__file__).parent.absolute().as_posix())  # Add voh/ to root path

from utils.notification import telegram_bot_send_message

# Set representing chunks that we have already downloaded
dlset = set()

# Download Pool
dlpool = ThreadPoolExecutor(max_workers=4)

# Logger
logger = logging.getLogger("fetch_hls_stream")

# GCS credentials
CREDENTIALS = service_account.Credentials.from_service_account_file('service-account.json')


def setuplog(verbose):
    """Config the log output of fetch_hls_stream"""
    log_msg_format = '%(asctime)s :: %(levelname)5s ::  %(name)10s :: %(message)s'
    log_date_format = '%Y-%m-%d %H:%M:%S'
    logging.basicConfig(format=log_msg_format, datefmt=log_date_format)
    if verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)


def upload_blob_from_memory(bucket_name, contents, destination_blob_name):
    """Uploads a file to the bucket."""

    # The ID of your GCS bucket
    # bucket_name = "your-bucket-name"

    # The contents to upload to the file
    # contents = "these are my contents"

    # The ID of your GCS object
    # destination_blob_name = "storage-object-name"

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
        upload_blob_from_memory(bucket_name="voh-project",
        contents=response.content,
        destination_blob_name=fpath)

        logger.debug("FINISHED WRITING " + uri + " TO GCS: " + fpath)

        # Comment all the code in the try block and 
        # raise a Exception here to test the alert.
        # raise Exception("Fake exception!")
    except Exception as ex:
        logger.error(ex)

        # Re-raise exception to catch it from outside
        raise Exception(f"Cannot download file and upload to GCS due to: {ex}")


@click.command()
@click.option('--url',
              default=os.getenv("M3U8_URL"),
              help='URL to HLS m3u8 playlist.')
@click.option('--freq',
              default=10,
              help="Frequency for downloading the HLS m3u8 stream")
@click.option('--output',
              default=os.getenv("OUTPUT_DIR"),
              type=click.Path(exists=True),
              help="Output directory for video files")
@click.option('--verbose', is_flag=True, help="Verbose")
def fetch_hls_stream(url, freq, output, verbose):
    """Fetch a HLS stream by periodically retrieving the m3u8 url for new
    playlist video files every freq seconds. For each segment that exists,
    it downloads them to the output directory as a TS video file."""

    setuplog(verbose)

    while True:
        # Retrieve the main m3u8 dynamic playlist file
        dynamicplaylist = m3u8.load(url)

        # Retrieve the real m3u8 playlist file from the dynamic one
        for playlist in dynamicplaylist.playlists:
            # Check if we have each segment in the playlist file
            playlistdata = m3u8.load(playlist.absolute_uri)

            for videosegment in playlistdata.segments:
                # Since the playlist changes names dynamically we use the
                # last part of the uri (vfname) to identify segments
                videouri = videosegment.absolute_uri
                videofname = videouri.split("_")[-1]

                if videofname not in dlset:
                    dlset.add(videofname)
                    task = dlpool.submit(download_file_and_upload_to_gcs, videouri, output, videofname)
                    
                    # Exception handling outside the task submit()
                    # => the task has to raise Exception first.
                    try:
                        _ = task.result()
                    except Exception as e:
                        telegram_bot_send_message(f"Error with {videouri}: {e}")
                        
        # Sleep until next check
        time.sleep(freq)


if __name__ == '__main__':
    try:
        fetch_hls_stream()
    except Exception as e:
        telegram_bot_send_message(f"FATAL ERROR: {type(e).__name__} !!! The process has been stopped.")
