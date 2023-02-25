resource "proxmox_vm_qemu" "deeplab-demo" {
    name = "deeplab-demo"
    desc = "GPU Ubuntu Server"
    vmid = "401"
    target_node = "hpz440"

    agent = 1

    clone = "ubuntu-focal-cloudinit-template"
    cores = 2
    sockets = 1
    cpu = "host"
    memory = 2048

    network {
        bridge = "vmbr1"
        model = "virtio"
    }

    disk {
        storage = "local-lvm"
        type = "virtio"
        size = "20G"
    }

    os_type = "cloud-init"
    ipconfig0 = "ip=11.11.1.88/16,gw=11.11.1.1"
    nameserver = "1.1.1.1"
    ciuser = "gpu"
    sshkeys = <<EOF
    ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC0Ji3n1/qwVydGS8OoOpw5LDd0VOcUPPDhRSDmU4Rl3bMceK17jXBZBZz1dofDIJiOKqGRGbYcLxh0kha3epIGyia9Z+z0ZHQg0ByRzuNlpepZYUva5EssOjVekRZtC1NiROS1BREVPG1sSwORdW0KiVJ4UiT7eJRNZwAm/0TZWmLTYdLqMI4FoBp8bzCQPMUbPb27sU0xZB/m8P7xJaAj9dZfpQEvV8azd2cLKNX9R1Fohft0eFE7U3D9oO26CbbQRlAOm9lxSAON9KZp6aAS0I2eY44vBZiprGafl12C/zFdywhJ9D4VcURfncufLUeSAImklz96IL3OK4hurKYhMTGydb9HHN03zcw69gwWAqnVJn3Yx/NflLZE9DIvQzAZQiYu14r5CL2SWNwoS7ui9Y0mdjP3Ah4rwRIjq/37C92g/qph4kqI8XlRe5NgYwdwtEr8vkL3dT0RatJU+ZTIW/uXsAk4rQ1JQ+VplLucEGjzmLZtC/R4q/IaBmGmCOs= tqtensor
    EOF
}
