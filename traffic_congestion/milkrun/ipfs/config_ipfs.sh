#!/bin/bash

LOCAL_IP=$(ifconfig | grep -Eo 'inet (addr:)?11\.([0-9]*\.){2}[0-9]*' | grep -Eo '([0-9]*\.){3}[0-9]*' | grep -v '127.0.0.1')
echo $LOCAL_IP

echo "
#!/bin/bash

docker compose exec ipfs0 ipfs config --json API.HTTPHeaders.Access-Control-Allow-Origin '[\"http://${LOCAL_IP}:5001\", \"http://localhost:3000\", \"http://127.0.0.1:5001\", \"https://webui.ipfs.io\"]'
docker compose exec ipfs0 ipfs config --json API.HTTPHeaders.Access-Control-Allow-Methods '[\"PUT\", \"POST\"]'

docker compose exec ipfs1 ipfs config --json API.HTTPHeaders.Access-Control-Allow-Origin '[\"http://${LOCAL_IP}:5001\", \"http://localhost:3000\", \"http://127.0.0.1:5001\", \"https://webui.ipfs.io\"]'
docker compose exec ipfs1 ipfs config --json API.HTTPHeaders.Access-Control-Allow-Methods '[\"PUT\", \"POST\"]'

docker compose exec ipfs2 ipfs config --json API.HTTPHeaders.Access-Control-Allow-Origin '[\"http://${LOCAL_IP}:5001\", \"http://localhost:3000\", \"http://127.0.0.1:5001\", \"https://webui.ipfs.io\"]'
docker compose exec ipfs2 ipfs config --json API.HTTPHeaders.Access-Control-Allow-Methods '[\"PUT\", \"POST\"]'
" >/tmp/config_ipfs.sh

bash /tmp/config_ipfs.sh
