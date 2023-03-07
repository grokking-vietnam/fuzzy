import os
import sqlite3
from typing import List, Optional

import boto3
from configs import S3Configuration

# AWS
BUCKET_NAME = "radio-project"


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


def validate_size() -> bool:
    """Validates whether the total size of requested objects is within limit."""
    return True


def seaweedfs_to_r2() -> None:
    """Downloads objects from SeaweedFS and upload to Cloudflare R2."""
    # Get current status of objects
    requested_objects = list_objects(from_side="client")
    existing_objects = list_objects(from_side="r2")

    # Infer the list of download and remove objects
    download_objects = []
    remove_objects = []

    # Execution
    clean_up_r2(objects=remove_objects)


def clean_up_r2(objects: List[str]) -> None:
    """Removes objects on Cloudflare R2."""
    r2 = create_client(service_type="client", backend="r2")
    1


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
    main()
