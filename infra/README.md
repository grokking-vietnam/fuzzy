# Terraform on Proxmox

## Credentials for Proxmox integration
Create files `infra/credentials.auto.tfvars` and `infra/packer/credentials.pkr.hcl`

```txt
proxmox_api_url = "https://proxmox-server.com:8006/api2/json"
proxmox_api_token_id = "root@pam!terraform"
proxmox_api_token_secret = ""
```

## Prepare Ubuntu Packer image
https://www.youtube.com/watch?v=1nf3WOEFq1Y

```bash
cd infra/packer/ubuntu-server-focal-docker
packer validate -var-file='../credentials.pkr.hcl' ubuntu-server-focal-docker.pkr.hcl
packer build -var-file='../credentials.pkr.hcl' ubuntu-server-focal-docker.pkr.hcl
```

## Notes
1. Replace the domain to your Proxmox server by its explicit IP. `proxmox-server.com` -> `123.45.67.89`
