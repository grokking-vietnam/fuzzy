import io
import logging
import os
import random
import sqlite3
from typing import List, Optional

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from configs import S3Configuration

# AWS
BUCKET_NAME = "radio-project"

# SeaweedFS Cluster
SEAWEEDFS_HOSTS = ["11.11.1.89", "11.11.1.90"]

# Logger
logger = logging.getLogger("milk_run")


def create_client(
    service_type: str = "client",
    backend: str = "seaweedfs",
    s3_host: Optional[str] = "seaweedfs",
) -> boto3.Session.client:
    """Returns S3 clients depends on the backend option."""

    if backend == "seaweedfs":
        kwrgs = {
            "endpoint_url": f"http://{s3_host}:8333",
            "aws_access_key_id": S3Configuration.AWS_SEAWEEDFS_KEY_ID,
            "aws_secret_access_key": S3Configuration.AWS_SEAWEEDFS_SECRET,
        }
    elif backend == "r2":
        kwrgs = {
            "endpoint_url": f"https://{S3Configuration.AWS_R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
            "aws_access_key_id": S3Configuration.AWS_R2_KEY_ID,
            "aws_secret_access_key": S3Configuration.AWS_R2_SECRET,
            "config": Config(region_name="auto"),
        }
    else:
        raise NotImplementedError

    if service_type == "client":
        return boto3.client("s3", **kwrgs)
    elif service_type == "resource":
        return boto3.resource("s3", **kwrgs)
    else:
        raise NotImplementedError


def list_objects(from_side: str) -> list:
    """Retrieves a list of active objects from the specified data source."""
    if from_side == "client":
        with sqlite3.connect("objects.db") as con:
            cur = con.cursor()
            return cur.execute("SELECT * FROM objects WHERE active = 1").fetchall()
    elif from_side == "r2":
        s3 = create_client(service_type="resource", backend="r2")
        bucket = s3.Bucket(BUCKET_NAME)
        return [item for item in bucket.objects.all()]
    else:
        raise NotImplementedError


def validate_size(objects: List[str], limit: float = 5) -> bool:
    """Validates whether the total size of requested objects is within limit in Gb."""
    s3 = create_client(service_type="client", backend="seaweedfs", s3_host="11.11.1.89")
    total_size = (
        sum(
            [
                s3.get_object(Bucket=BUCKET_NAME, Key=object_key).get("ContentLength")
                for object_key in objects
            ]
        )
        / 2**30
    )
    return total_size > limit


def seaweedfs_to_r2() -> None:
    """Downloads objects from SeaweedFS and upload to Cloudflare R2."""
    # Get current status of objects
    requested_objects = list_objects(from_side="client")
    existing_objects = list_objects(from_side="r2")

    # Infer the list of download and remove objects
    download_objects = [
        {"source": obj[1], "object_key": obj[2]} for obj in requested_objects
    ]
    remove_objects = []

    # Execution
    for obj in download_objects:
        if obj["source"] == "seaweedfs":
            src_client = create_client(
                backend=obj["source"],
                service_type="client",
                s3_host=random.choice(SEAWEEDFS_HOSTS),
            )
        else:
            src_client = create_client(backend=obj["source"], service_type="client")
        dst_client = create_client(backend="r2", service_type="client")

        # Download object to mem
        obj_body = src_client.get_object(Bucket=BUCKET_NAME, Key=obj["object_key"])[
            "Body"
        ].read()

        # Write bytes content to buffer
        buf = io.BytesIO()
        buf.write(obj_body)
        buf.seek(0)

        # Upload object from buffer to R2
        try:
            _ = dst_client.upload_fileobj(buf, BUCKET_NAME, obj["object_key"])
            logger.info(
                "TRANSFERRED {} from S3 [{}] to R2".format(
                    obj["object_key"], obj["source"]
                )
            )
        except ClientError as ex:
            logger.exception(ex)


def main() -> None:
    # Init the objects.db database
    if not os.path.exists("objects.db"):
        with sqlite3.connect("objects.db") as con:
            cur = con.cursor()
            cur.execute(
                "CREATE TABLE objects(id INTEGER PRIMARY KEY, src TEXT, dst TEXT, active INTEGER)"
            )
            con.commit()


if __name__ == "__main__":
    seaweedfs_to_r2()
