from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Tuple

from tqdm import tqdm


def download_blob_into_memory(storage_client, bucket: str,
                              source_blob_name: str) -> bytes:
    """Downloads a blob from the bucket."""
    bucket = storage_client.bucket(bucket)
    blob = bucket.blob(source_blob_name)
    contents = blob.download_as_string()
    return contents


def multithreaded_download(storage_client,
                           bucket: str,
                           blob_names: List[str],
                           max_workers: int = 10) -> List[Tuple[tuple, bytes]]:
    future_proxy_mapping = {}
    futures = []
    results = []
    with tqdm(total=len(blob_names)) as pbar:
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            args = [(storage_client, bucket, blob_name)
                    for blob_name in blob_names]
            for arg in args:
                future = pool.submit(download_blob_into_memory, *arg)
                futures.append(future)
                future_proxy_mapping[future] = arg
            for future in as_completed(futures):
                results.append((future_proxy_mapping[future], future.result()))
                pbar.update(1)
    return results
