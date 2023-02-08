import logging
from pathlib import Path

from fs.errors import DirectoryExists
from fs.googledrivefs import GoogleDriveFS
from google.oauth2.service_account import Credentials

# Logger
logger = logging.getLogger("fetch_hls_stream")


def write_file_to_gdrive(credential_filename: str, root_folder_id: str,
                         file_path: str):
    """Writes data to Google Drive"""
    credentials = Credentials.from_service_account_file(credential_filename)
    fs = GoogleDriveFS(credentials=credentials, rootId=root_folder_id)

    file_path = Path(file_path)

    with open(file_path, "rb") as fp:
        try:
            fs.makedirs(str(file_path.parent))
        except Exception as ex:
            if not isinstance(ex, DirectoryExists):
                logger.exception(ex)
        fs.upload(str(file_path), fp)
        logger.info(f"UPLOADED {file_path} to Google Drive")
