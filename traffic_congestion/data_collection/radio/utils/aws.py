import io
import logging
import sys
from pathlib import Path
from typing import List, Optional

import boto3
from botocore.exceptions import ClientError
from dotmap import DotMap

sys.path.append(Path(
    __file__).parent.parent.absolute().as_posix())  # Add radio/ to root path

from configs import S3Configuration

# Logger
logger = logging.getLogger("fetch_hls_stream")


def create_client(backend: str = "seaweedfs") -> boto3.Session.client:
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
    return boto3.client("s3", **kwrgs)


def write_buf_to_s3(contents: bytes,
                    bucket_name: str,
                    object_name: str,
                    backend: str = "seaweedfs") -> None:
    """Writes data to S3, either on SeaweedFS or AWS."""
    client = create_client(backend=backend)

    # Write bytes content to buffer
    buf = io.BytesIO()
    buf.write(contents)
    buf.seek(0)

    try:
        _ = client.upload_fileobj(buf, bucket_name, object_name)
        logger.info(f"UPLOADED {object_name} to S3 [{backend}]")
    except ClientError as ex:
        logger.error(ex)


def list_blob(bucket_name: str,
              prefix: str,
              backend: str = "seaweedfs") -> Optional[List[DotMap]]:
    """Lists the blobs inside a bucket with prefix."""
    client = create_client(backend=backend)
    blobs = client.list_objects_v2(Bucket=bucket_name,
                                   Prefix="/".join(prefix.split("/")) + "/",
                                   Delimiter="/").get("Contents", None)
    if blobs:
        return [DotMap(blob) for blob in blobs]
    else:
        return
