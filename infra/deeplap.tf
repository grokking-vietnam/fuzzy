resource "proxmox_vm_qemu" "deeplab" {
  name        = "deeplab"
  desc        = "GPU Ubuntu Server"
  vmid        = 401
  target_node = "hpz440"

  agent = 1

  clone   = "ubuntu-focal-q35-template"
  cores   = 4
  sockets = 1
  cpu     = "host"
  memory  = 20480
  balloon = 2048

  network {
    bridge   = "vmbr1"
    model    = "virtio"
    firewall = true
  }

  disk {
    storage = "local-lvm"
    type    = "virtio"
    size    = "80G"
  }

  os_type    = "cloud-init"
  ipconfig0  = "ip=11.11.1.88/16,gw=11.11.1.1"
  nameserver = "1.1.1.1"
  ciuser     = "terrabot"
  sshkeys    = <<EOF
    ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC1s3xm/TxBJ38g2jMlg1MseGEy7gYQ7++ofccdwgkuYkVMx/6+li4bimhlCcxfoWea1nqowoM8R/OkkJI2SSVjHEoIm1i9cfZ+VADzoDGuHvGpqud/TQqsskiryQv8hx8upKbvAHRYt8c1YJTEKrWYJd6UW9xIg/+IwyqzlScHeNeomxKFPy3j7GBeAzzh3R+tVVWLajNqUIuHBxmlUkHU4Ko6B/YQziI1PLQXesvLK3/ab/XRlkWh6ZIrK6/xYF+rs/MGUZD43nZrpBUFH4u0ht7uUCrdcVxUoaHZcnKk5qF3nvDzzL2K9SqyY6NfOUjnpXxDSNFh5unzwkNfqTr/3mDoDeXonxrd3QaEKjgZzqkyZ4YwNGGfFxGhFsUwyLa6MJ3KGE98hTmMGtYnAuGqvBQf1BVKhcVzXjK8R37nEayNXZT163felTWgNnSnspRNMnpx5epIIvlCODIundCMTLF8zneIsRUk5NLebmpKbSS+799BtH4UMZax2kW2yzk= terrabot
    EOF

  connection {
    type        = "ssh"
    user        = self.ciuser
    private_key = file("~/.ssh/terrabot")
    host        = "11.11.1.88"
  }

  provisioner "remote-exec" {
    inline = [
      "sudo apt-get update",
      "sudo apt-get -y install ca-certificates curl gnupg lsb-release",
      "sudo mkdir -m 0755 -p /etc/apt/keyrings",
      "curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg",
      "echo \"deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable\" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null",
      "sudo apt-get update",
      "sleep 15",
      "sudo apt-get -y install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin",
      "sudo usermod --append --groups docker \"$USER\"",
      "sudo systemctl enable docker",
      "printf '\nDocker installed successfully\n\n'",
      "printf 'Waiting for Docker to start...\n\n'",
      "sleep 5"
    ]
  }

  provisioner "remote-exec" {
    inline = [
      "wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/cuda-keyring_1.0-1_all.deb",
      "sudo dpkg -i cuda-keyring_1.0-1_all.deb",
      "sudo apt-get update",
      "sudo apt-get -y install cuda",
      "sleep 5",
      "sudo reboot"
    ]
  }
}
