#!/usr/bin/python

import sys
import threading

from node import Node
import link


def main(file_name):
    node_data = link.read_link_data(file_name)
    this_node = Node(node_data.local_physical_IP, node_data.local_physical_port, node_data.interfaces)
    this_node.register_handlers(200, this_node.update_distance_table)
    this_node.register_handlers(0, this_node.print_message)
    t1 = threading.Thread(target=this_node.send_table)
    t2 = threading.Thread(target=this_node.link.receive_data)
    t3 = threading.Thread(target=this_node.check_for_out_of_date)
    t1.start()
    t2.start()
    t3.start()
    this_node.read_commands()
    t1.join()
    t2.join()
    t3.join()


if __name__ == "__main__":
    main(sys.argv[1])
