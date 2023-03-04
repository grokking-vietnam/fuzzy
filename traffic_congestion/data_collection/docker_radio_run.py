"""
Simple program to build and run Docker containers for each radio channel.
"""

import subprocess
import time

import yaml
from radio.utils.aws import create_client

# AWS
BUCKET_NAME = "radio-project"


def run_cmd(cmd: str) -> None:
    """Runs bash script."""
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
    while p.poll() is None:
        stdout = p.stdout.readline()
        print(stdout)


if __name__ == "__main__":
    build_radio_images = input("Do you want to build radio images: (y/n) ")

    # Start SeaweedFS
    seaweedfs_cmd = """
    docker compose -f seaweedfs/seaweedfs-compose.yml -p seaweedfs up -d
    """
    run_cmd(cmd=seaweedfs_cmd)
    while True:
        try:
            client = create_client()
            client.create_bucket(Bucket=BUCKET_NAME)
            time.sleep(10)
        except Exception as ex:
            if "BucketAlreadyExists" not in str(ex):
                print(ex)
            else:
                print(f"Bucket {BUCKET_NAME} created")
                break

    if build_radio_images.lower() == "y":
        # Build base Docker image
        with open("radio_channels.yaml", "r") as fp:
            try:
                channels = yaml.safe_load(fp)
            except yaml.YAMLError as e:
                print(e)

        alert_interval = int(input("Alert interval in minute: "))

        build_cmd = f"""docker build -f Dockerfile.radio . \
                                -t radio"""
        run_cmd(cmd=build_cmd)

        for channel in channels["channels"].keys():
            url = channels["channels"][channel]["M3U8_URL"]

            remove_cmd = f"docker rm -f radio-{channel}"
            docker_run_cmd = f"""docker run --detach -it --restart=always \
                                --add-host=seaweedfs:10.10.0.1 \
                                -e OUTPUT_DIR='{channel}' \
                                -e M3U8_URL='{url}' \
                                -e ALERT={alert_interval} \
                                --log-driver json-file \
                                --log-opt max-size=1M \
                                --log-opt max-file=5 \
                                --name=radio-{channel} radio:latest"""

            run_cmd(cmd=remove_cmd)
            run_cmd(cmd=docker_run_cmd)
