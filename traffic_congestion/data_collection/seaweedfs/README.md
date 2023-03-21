# Setup

## Get artifacts from DVC
```bash
# Install Poetry
git clone https://github.com/grokking-vietnam/fuzzy.git
cd fuzzy/traffic_congestion/data_collection
pip install -U pip
pip install poetry
poetry config virtualenvs.in-project true
poetry install

# Install gcloud CLI and authenticate
sudo apt-get -qq -y install apt-transport-https ca-certificates gnupg
echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | sudo tee -a /etc/apt/sources.list.d/google-cloud-sdk.list
curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key --keyring /usr/share/keyrings/cloud.google.gpg add -
sudo apt-get -qq update && sudo apt-get -qq -y install google-cloud-cli
gcloud auth application-default login

# DVC pull
poetry run dvc pull
```

## Make local folders to map with SeaweedFS docker-compose
```bash
sudo mkdir -p /etc/seaweedfs
sudo cp seaweedfs/s3.json /etc/seaweedfs

sudo mkdir -p /etc/prometheus
sudo cp seaweedfs/prometheus.yml /etc/prometheus

sudo mkdir -p /var/seaweedfs/mnt
sudo mkdir -p /var/seaweedfs/volume_01
sudo mkdir -p /var/seaweedfs/volume_02
sudo chmod -R 777 /var/seaweedfs
```

## Host
Add this to your `/etc/hosts` file.
```bash
echo '10.10.0.1 seaweedfs' | sudo tee -a /etc/hosts
```
