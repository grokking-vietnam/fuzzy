import datetime as dt
import io
import logging
from zoneinfo import ZoneInfo

from google.cloud import storage
from google.oauth2 import service_account
from pydub import AudioSegment

from traffic_congestion.data_collection.voh.gcs_utils import \
    multithreaded_download

# Logger
logger = logging.getLogger("data_retrieval")
log_msg_format = '%(asctime)s :: %(levelname)5s ::  %(name)10s :: %(message)s'
log_date_format = '%Y-%m-%d %H:%M:%S'
logging.basicConfig(format=log_msg_format, datefmt=log_date_format)
logger.setLevel(logging.INFO)

# GCS
CREDENTIALS = service_account.Credentials.from_service_account_file(
    'traffic_congestion/data_collection/voh/service-account.json')
GCS_BUCKET = "voh-project"


class VOHData:

    def __init__(self, channel: str) -> None:
        self.gcs_bucket = GCS_BUCKET
        self.channel = channel

    def retrieve(
        self,
        from_time: dt.datetime,
        to_time: dt.datetime,
    ):

        # Check timezone info
        logger.info("Going to retrieve audio from {} to {}".format(
            from_time.replace(tzinfo=ZoneInfo('Asia/Ho_Chi_Minh')),
            to_time.replace(tzinfo=ZoneInfo('Asia/Ho_Chi_Minh'))))

        # Search for files on GCS
        storage_client = storage.Client(credentials=CREDENTIALS)
        audio_files = []
        for blob in storage_client.list_blobs(
                GCS_BUCKET, prefix=f'{self.channel}/2022/11/30/',
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
        joined.export("./output.wav", format="wav")

    def _path_to_datetime(self, path: str) -> dt.datetime:
        return dt.datetime.strptime(
            path, f'{self.channel}/%Y/%m/%d/%H_%M_%S_%f.aac')


if __name__ == "__main__":
    data = VOHData(channel="95.6")
    data.retrieve(from_time=dt.datetime(2022, 11, 30, 10, 30, 0),
                  to_time=dt.datetime(2022, 11, 30, 11, 30, 0))
