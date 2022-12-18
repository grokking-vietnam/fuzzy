import datetime as dt
import io
import logging
import sys
from pathlib import Path
from typing import Tuple

from google.cloud import storage
from google.oauth2 import service_account
from pydub import AudioSegment

sys.path.append(
    Path(__file__).parent.absolute().as_posix())  # Add radio/ to root path

from utils.gcs import multithreaded_download

# Logger
logger = logging.getLogger("data_retrieval")
log_msg_format = '%(asctime)s :: %(levelname)5s ::  %(name)10s :: %(message)s'
log_date_format = '%Y-%m-%d %H:%M:%S'
logging.basicConfig(format=log_msg_format, datefmt=log_date_format)
logger.setLevel(logging.INFO)

# GCS
CREDENTIALS = service_account.Credentials.from_service_account_file(
    'service-account.json')
GCS_BUCKET = "radio-project"


class RadioData:

    def __init__(self, channel: str) -> None:
        self.gcs_bucket = GCS_BUCKET
        self.channel = channel

    def retrieve(self,
                 from_date: dt.datetime,
                 to_date: dt.datetime,
                 time_range: Tuple[Tuple[int, int, int],
                                   Tuple[int, int,
                                         int]] = ((10, 30, 0), (11, 30, 0))):

        # Search for files on GCS
        storage_client = storage.Client(credentials=CREDENTIALS)
        date_iterator = from_date
        while date_iterator <= to_date:
            from_time = date_iterator.replace(hour=time_range[0][0],
                                              minute=time_range[0][1],
                                              second=time_range[0][2])
            to_time = date_iterator.replace(hour=time_range[1][0],
                                            minute=time_range[1][1],
                                            second=time_range[1][2])
            audio_files = []
            for blob in storage_client.list_blobs(
                    GCS_BUCKET,
                    prefix='{}/{}/'.format(self.channel,
                                           date_iterator.strftime("%Y/%m/%d")),
                    delimiter="/"):
                if (self._path_to_datetime(path=blob.name) >= from_time) & (
                        self._path_to_datetime(path=blob.name) <= to_time):
                    audio_files.append(blob.name)

            # Download to memory
            results = multithreaded_download(storage_client=storage_client,
                                             bucket=self.gcs_bucket,
                                             blob_names=audio_files)
            results = [(self._path_to_datetime(result[0][-1]), result[1])
                       for result in results]
            results.sort(key=lambda x: x[0])

            # Combine audio files
            audio_segments = [
                AudioSegment.from_file(io.BytesIO(result[1]), format="aac")
                for result in results
            ]
            joined = sum(audio_segments)
            joined.export("./{}_{}_{}_{}.wav".format(
                self.channel, date_iterator.strftime("%Y_%m_%d"),
                from_time.strftime("%H%M%S"), to_time.strftime("%H%M%S")),
                          format="wav")

            date_iterator += dt.timedelta(days=1)

    def _path_to_datetime(self, path: str) -> dt.datetime:
        return dt.datetime.strptime(
            path, f'{self.channel}/%Y/%m/%d/%H_%M_%S_%f.aac')


if __name__ == "__main__":
    data = RadioData(channel="voh-95.6")
    data.retrieve(from_date=dt.datetime(2022, 11, 29),
                  to_date=dt.datetime(2022, 11, 30))
