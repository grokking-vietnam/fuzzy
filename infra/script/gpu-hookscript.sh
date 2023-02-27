#!/bin/bash

if [ $2 == "pre-start" ]; then
    echo "gpu-hookscript: Resetting GPU for Virtual Machine $1"
    echo 1 >/sys/bus/pci/devices/0000\:02\:00.0/remove
    echo 1 >/sys/bus/pci/rescan

    echo 0 >/sys/class/vtconsole/vtcon0/bind
    echo 0 >/sys/class/vtconsole/vtcon1/bind

    echo vesa-framebuffer.0 >/sys/bus/platform/drivers/vesa-framebuffer/unbind
    echo efi-framebuffer.0 >/sys/bus/platform/drivers/efi-framebuffer/unbind
    echo simple-framebuffer.0 >/sys/bus/platform/drivers/simple-framebuffer/unbind
fi
