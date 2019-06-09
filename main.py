#!/usr/bin/python

import sys
import threading
import time

from node import Node


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


def read_commands(this_node):
    while True:
        text = input("> ")
        if text == "interfaces":
            this_node.show_interfaces()

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
            break

        else:
            print("- help, h: Print this list of commands\n"
                  "- interfaces: Print information about each interface, one per line\n"
                  "- routes: Print information about the route to each known destination, one per line\n"
                  "- up [integer]: Bring an interface \"up\" (it must be an existing interface, "
                  "probably one you brought down)\n"
                  "- down [integer]: Bring an interface \"down\"\n"
                  "- send [ip] [protocol] [payload]: sends payload with protocol=protocol to virtual-ip ip\n"
                  "- q: quit this node\n")


def main(file_name):
    node_data = read_link_data(file_name)
    this_node = Node(node_data.local_physical_IP, node_data.local_physical_port, node_data.interfaces)
    t1 = threading.Thread(target=this_node.send_table)
    t2 = threading.Thread(target=this_node.receive_table)
    t1.start()
    t2.start()
    read_commands(this_node)


if __name__ == "__main__":
    main(sys.argv[1])
