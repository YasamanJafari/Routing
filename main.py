#!/usr/bin/python

import sys
from dataclasses import dataclass


@dataclass
class LnxInfo:
    local_physical_IP: str
    local_physical_port: int
    interfaces: []


@dataclass
class LnxBody:
    remote_physical_IP: str
    remote_physical_port: int
    local_virtual_IP: str
    remote_virtual_IP: str


def read_link_data(file_name):
    f = open(file_name, "r")
    contents = f.read()
    data = contents.split("\n")
    local_phys_address = data[0].split(" ")
    interfaces_info = []
    for info in data[1:]:
        if info == '':
            break
        address = info.split(" ")
        interface = LnxBody(address[0], address[1], address[2], address[3])
        interfaces_info.append(interface)
    node_data = LnxInfo(local_phys_address[0], local_phys_address[1], interfaces_info)
    return node_data


def main(file_name):
    read_link_data(file_name)


if __name__ == "__main__":
    main(sys.argv[1])

