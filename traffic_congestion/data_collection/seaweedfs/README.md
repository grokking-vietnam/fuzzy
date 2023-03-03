# Setup

## Create Local Folders
```bash
sudo mkdir -p /etc/seaweedfs
sudo cp seaweedfs/s3.json /etc/seaweedfs

sudo mkdir -p /etc/prometheus
sudo cp seaweedfs/prometheus.yml /etc/prometheus

sudo mkdir -p /var/seaweedfs/volume_01
sudo mkdir -p /var/seaweedfs/volume_02
sudo chmod -R 777 /var/seaweedfs
```

## Host
Add this to your `/etc/hosts` file.
```txt
10.10.0.1 seaweedfs
```
