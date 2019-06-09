#!/usr/bin/python

import sys
import threading
import time


class LnxInfo:
    def __init__(self, local_physical_host, local_physical_port, interfaces):
        self.local_physical_IP = local_physical_host
        self.local_physical_port = local_physical_port
        self.interfaces = interfaces


class LnxBody:
    def __init__(self, remote_physical_host, remote_physical_port, local_virtual, remote_virtual):
        self.remote_physical_IP = remote_physical_host
        self.remote_physical_port = remote_physical_port
        self.local_virtual_IP = local_virtual
        self.remote_virtual_IP = remote_virtual


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


def read_commands():
    while True:
        text = input("> ")
        if text == "interfaces":
            print("Not Implemented.")

        elif text == "routes":
            print("Not Implemented.")

        elif text == "down":
            print("Not Implemented.")

        elif text == "up":
            print("Not Implemented.")

        elif text == "send":
            print("Not Implemented.")

        elif text == "q":
            print("Not Implemented.")


def main(file_name):
    node_data = read_link_data(file_name)
    # t1 = threading.Thread(target=send_table, args=(10,))
    # t2 = threading.Thread(target=receive_table, args=(10,))
    # t1.start()
    # t2.start()
    read_commands()


if __name__ == "__main__":
    main(sys.argv[1])

