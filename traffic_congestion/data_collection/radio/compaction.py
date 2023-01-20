"""
Simple program to remove unused audio files and zip them to block.
"""

import datetime
import io
import logging
import os
import sys
import tarfile
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import List

sys.path.append(
    Path(__file__).parent.absolute().as_posix())  # Add radio/ to root path

from utils.aws import delete_blob, download_blob, list_blob, write_file_to_s3

# AWS
BUCKET_NAME = "radio-project"

# Logger
logger = logging.getLogger("fetch_hls_stream")


def compress(output: str, filepaths: List[str]) -> None:
    """Compresses files into tar file."""

    def delete_file(filepath: str):
        os.remove(filepath)

    # Compress to tar file
    filepaths = [
        filepath for filepath in filepaths if os.path.exists(filepath)
    ]
    with tarfile.open(output, "w:gz") as archive:
        for filepath in filepaths:
            with io.BytesIO(open(filepath, "rb").read()) as f:
                info = tarfile.TarInfo(os.path.basename(filepath))
                f.seek(0, io.SEEK_END)
                info.size = f.tell()
                f.seek(0, io.SEEK_SET)
                archive.addfile(info, f)

    # Check the size of tar file
    if os.path.getsize(output) < 1e7:
        logger.warning(f"This tar file {output} is less than 10 MB.")
    else:
        # Upload to AWS S3
        write_file_to_s3(bucket_name=BUCKET_NAME,
                         file_name=output,
                         object_name=output,
                         backend="aws")

    # Clean up
    with ThreadPoolExecutor(100) as p:
        _ = [p.submit(delete_file, filepath) for filepath in filepaths]
    with ThreadPoolExecutor(10) as p:
        _ = [
            p.submit(delete_blob, BUCKET_NAME, filepath)
            for filepath in filepaths
        ]
    delete_file(filepath=output)


def main(channel: str, running_hours=range(6, 22)) -> None:
    """Compresses files into 1 hour block and upload to AWS S3."""
    # Get list of all files from SeaweedFS S3
    blobs = list_blob(bucket_name=BUCKET_NAME, prefix=f"{channel}/")

    s3_compress = defaultdict(list)
    s3_remove = []
    # Parsing channel and datetime from file
    for blob in blobs:
        _, year, month, day, filename = blob.key.split("/")
        hour = filename.split("_")[0]
        ymdh = datetime.datetime(int(year), int(month), int(day), int(hour))
        if int(hour) + 7 in running_hours:
            if (datetime.datetime.utcnow() - ymdh).total_seconds() > 2 * 3600:
                s3_compress["|".join([channel, year, month, day,
                                      hour])].append(blob.key)
        else:
            s3_remove.append(blob.key)

    # Get files to local disk
    for key, filepaths in s3_compress.items():
        logger.info(key)
        with ThreadPoolExecutor(10) as p:
            _ = [
                p.submit(download_blob, BUCKET_NAME, filepath, "seaweedfs")
                for filepath in filepaths
            ]

    # Compress files to 1 hour block
    for key, filepaths in s3_compress.items():
        compress(output="/".join(key.split("|")) + ".tar.gz",
                 filepaths=filepaths)

    # Remove unnecessary files
    with ThreadPoolExecutor(10) as p:
        _ = [
            p.submit(delete_blob, BUCKET_NAME, filepath)
            for filepath in s3_remove
        ]


if __name__ == "__main__":
    main(channel="voh-95.6")
