import io
import logging
import os
import sys
from pathlib import Path
from typing import Optional

import boto3
from botocore.exceptions import ClientError

sys.path.append(Path(
    __file__).parent.parent.absolute().as_posix())  # Add radio/ to root path

from configs import S3Configuration

# Logger
logger = logging.getLogger("fetch_hls_stream")


def create_client(service_type: str = "client",
                  backend: str = "seaweedfs") -> boto3.Session.client:
    """Returns S3 clients depends on the backend option."""

    if backend == "seaweedfs":
        kwrgs = {
            "endpoint_url": "http://seaweedfs:8333",
            "aws_access_key_id": S3Configuration.AWS_SEAWEEDFS_KEY_ID,
            "aws_secret_access_key": S3Configuration.AWS_SEAWEEDFS_SECRET,
        }
    elif backend == "aws":
        kwrgs = {
            "aws_access_key_id": S3Configuration.AWS_KEY_ID,
            "aws_secret_access_key": S3Configuration.AWS_SECRET,
        }
    else:
        raise NotImplementedError

    if service_type == "client":
        return boto3.client("s3", **kwrgs)
    elif service_type == "resource":
        return boto3.resource("s3", **kwrgs)
    else:
        raise NotImplementedError


def write_file_to_s3(bucket_name: str,
                     file_name: str,
                     object_name: str,
                     backend: str = "seaweedfs") -> None:
    """Writes data to S3, either on SeaweedFS or AWS."""
    client = create_client(backend=backend)

    try:
        _ = client.upload_file(file_name, bucket_name, object_name)
        logger.info(f"UPLOADED {object_name} to S3 [{backend}]")
    except ClientError as ex:
        logger.exception(ex)


def write_buf_to_s3(contents: bytes,
                    bucket_name: str,
                    object_name: str,
                    backend: str = "seaweedfs") -> None:
    """Writes buffer to S3, either on SeaweedFS or AWS."""
    client = create_client(backend=backend)

    # Write bytes content to buffer
    buf = io.BytesIO()
    buf.write(contents)
    buf.seek(0)

    try:
        _ = client.upload_fileobj(buf, bucket_name, object_name)
        logger.info(f"UPLOADED {object_name} to S3 [{backend}]")
    except ClientError as ex:
        logger.exception(ex)


def list_blob(bucket_name: str,
              prefix: str,
              backend: str = "seaweedfs") -> Optional[list]:
    """Lists the blobs inside a bucket with prefix."""
    s3 = create_client(service_type="resource", backend=backend)

    bucket = s3.Bucket(name=bucket_name)
    files_not_found = True
    blobs = []
    for blob in bucket.objects.filter(Prefix=prefix):
        blobs.append(blob)
        files_not_found = False
    if files_not_found:
        print("ALERT", "No file in {0}/{1} {2}".format(bucket, prefix,
                                                       backend))

    if blobs:
        return blobs
    else:
        return


def download_blob(bucket_name: str,
                  object_name: str,
                  backend: str = "seaweedfs") -> None:
    """Downloads blob from S3 to local file."""
    client = create_client(backend=backend)

    if not os.path.exists(Path(object_name).parent):
        os.makedirs(Path(object_name).parent)

    with open(object_name, "wb") as f:
        client.download_fileobj(Bucket=bucket_name, Key=object_name, Fileobj=f)


def delete_blob(bucket_name: str,
                object_name: str,
                backend: str = "seaweedfs") -> None:
    """Deletes blob on S3."""
    client = create_client(backend=backend)

    try:
        client.delete_object(Bucket=bucket_name, Key=object_name)
    except ClientError as ex:
        logger.exception(ex)
