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

    alert_interval = int(input("Alert interval in minute: "))

    build_command = f"""docker build -f Dockerfile.radio . \
                            -t radio"""
    p = subprocess.Popen(build_command, stdout=subprocess.PIPE, shell=True)
    while p.poll() is None:
        stdout = p.stdout.readline()
        print(stdout)

    for channel in channels["channels"].keys():
        url = channels["channels"][channel]["M3U8_URL"]

        remove_command = f"docker rm -f radio-{channel}"
        run_command = f"""docker run --detach -it --restart=always \
                            -e OUTPUT_DIR='{channel}' \
                            -e M3U8_URL='{url}' \
                            -e ALERT={alert_interval} \
                            --log-driver json-file \
                            --log-opts max-size=1M \
                            --log-opts max-file=5 \
                            --name=radio-{channel} radio:latest"""

        p = subprocess.Popen(remove_command,
                             stdout=subprocess.PIPE,
                             shell=True)
        print(p.communicate())

        p = subprocess.Popen(run_command, stdout=subprocess.PIPE, shell=True)
        print(p.communicate())
