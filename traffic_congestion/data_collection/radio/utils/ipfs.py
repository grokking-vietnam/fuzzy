import logging

from ipyfs import Files

IPFS_NODE_IP = "11.11.1.89"

# Logger
logger = logging.getLogger("fetch_hls_stream")


def write_file_to_ipfs(file_path: str):
    """Writes data to IPFS node."""

    files = Files(host=f"http://{IPFS_NODE_IP}", port=5001)

    with open(file_path, "rb") as f:
        files.write(path=f"/{f.name}", file=f, create=True)
