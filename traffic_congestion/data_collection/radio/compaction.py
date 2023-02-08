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
from utils.gcp import write_file_to_gdrive

# AWS
BUCKET_NAME = "radio-project"
TTL = 14  # days

# GCP
CREDENTIAL_FILENAME = "grokking-ai.json"
ROOT_FOLDER_ID = "1d7WyTcSIOW5s2HT7bxySCJxpP-xXukPA"

# Logger
logger = logging.getLogger("fetch_hls_stream")


def compress(output: str, file_paths: List[str]) -> None:
    """Compresses files into tar file."""

    def delete_file(file_path: str):
        os.remove(file_path)

    # Compress to tar file
    file_paths = [
        file_path for file_path in file_paths if os.path.exists(file_path)
    ]
    with tarfile.open(output, "w:gz") as archive:
        for file_path in file_paths:
            with io.BytesIO(open(file_path, "rb").read()) as f:
                info = tarfile.TarInfo(os.path.basename(file_path))
                f.seek(0, io.SEEK_END)
                info.size = f.tell()
                f.seek(0, io.SEEK_SET)
                archive.addfile(info, f)

    # Check the size of tar file
    if os.path.getsize(output) < 1e7:
        logger.warning(f"This tar file {output} is less than 10 MB.")
    else:
        # Upload to Google Drive
        write_file_to_gdrive(
            credential_filename=CREDENTIAL_FILENAME,
            root_folder_id=ROOT_FOLDER_ID,
            file_path=output,
        )

        # Upload to AWS S3
        write_file_to_s3(bucket_name=BUCKET_NAME,
                         file_name=output,
                         object_name=output,
                         backend="aws")

    # Clean up
    with ThreadPoolExecutor(100) as p:
        _ = [p.submit(delete_file, file_path) for file_path in file_paths]
    delete_file(file_path=output)


def main(channel: str, running_hours=range(6, 22)) -> None:
    """Compresses files into 1 hour block and upload to AWS S3."""
    # Get list of all files from SeaweedFS S3
    blobs = list_blob(bucket_name=BUCKET_NAME, prefix=f"{channel}/")

    if blobs:
        s3_compress = defaultdict(list)
        s3_garbage = []
        # Parsing channel and datetime from file
        for blob in blobs:
            _, year, month, day, filename = blob.key.split("/")
            hour = filename.split("_")[0]
            ymdh = datetime.datetime(int(year), int(month), int(day),
                                     int(hour))
            if int(hour) + 7 in running_hours:
                if (datetime.datetime.utcnow() -
                        ymdh).total_seconds() > 2 * 3600:
                    s3_compress["|".join([channel, year, month, day,
                                          hour])].append(blob.key)
                if (datetime.datetime.utcnow() -
                        ymdh).total_seconds() > TTL * 24 * 3600:
                    s3_garbage.append(blob.key)
            else:
                s3_garbage.append(blob.key)

        # Get list of all files from AWS S3
        aws_blobs = list_blob(bucket_name=BUCKET_NAME,
                              prefix=f"{channel}/",
                              backend="aws")
        if aws_blobs:
            aws_keys = set([
                blob.key.replace(".tar.gz", "").replace("/", "|")
                for blob in aws_blobs
            ])
        else:
            aws_keys = set([])

        s3_compress = {
            key: file_paths
            for key, file_paths in s3_compress.items() if key not in aws_keys
        }  # compressed and uploaded to AWS S3 or not?

        # Get files to local disk
        for key, file_paths in s3_compress.items():
            logger.info(key)
            with ThreadPoolExecutor(10) as p:
                _ = [
                    p.submit(download_blob, BUCKET_NAME, file_path,
                             "seaweedfs") for file_path in file_paths
                ]

        # Compress files to 1 hour block
        for key, file_paths in s3_compress.items():
            try:
                compress(output="/".join(key.split("|")) + ".tar.gz",
                         file_paths=file_paths)
            except Exception as ex:
                logger.exception(ex)

        # Remove garbage files
        with ThreadPoolExecutor(10) as p:
            _ = [
                p.submit(delete_blob, BUCKET_NAME, file_path)
                for file_path in s3_garbage
            ]


if __name__ == "__main__":
    main(channel="voh-95.6")
