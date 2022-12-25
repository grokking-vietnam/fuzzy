"""
Simple program to build and run Docker containers for each radio channel.
"""

import subprocess

import yaml

if __name__ == "__main__":
    with open("radio_channels.yaml", "r") as fp:
        try:
            channels = yaml.safe_load(fp)
        except yaml.YAMLError as e:
            print(e)

    for channel in channels["channels"].keys():
        url = channels["channels"][channel]["M3U8_URL"]
        remove_command = f"docker rm -f {channel}"
        build_command = f"docker build -f Dockerfile.radio . --build-arg CHANNEL={channel} --build-arg M3U8_URL={url} -t {channel}"
        run_command = f"docker run --detach -it --restart=always --name={channel} {channel}:latest"

        p = subprocess.Popen(remove_command,
                             stdout=subprocess.PIPE,
                             shell=True)
        print(p.communicate())

        p = subprocess.Popen(build_command, stdout=subprocess.PIPE, shell=True)
        print(p.communicate())

        p = subprocess.Popen(run_command, stdout=subprocess.PIPE, shell=True)
        print(p.communicate())
