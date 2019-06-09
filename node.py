import socket
import constant
import pickle
import time


class Node:
    def __init__(self, physical_host, physical_port, neighbours_info):
        self.physical_host = physical_host
        self.physical_port = physical_port
        self.neighbours_info = neighbours_info
        self.destination = {}
        self.passing_node = {}
        self.distance_table = []
        self.initialize_table()
        self.registered_handlers = {}

    def register_handlers(self, protocol_num, handler):
        if protocol_num in self.registered_handlers:
            print("This protocol number is already registered.")
        else:
            self.registered_handlers[protocol_num] = handler

    def run_handler(self, protocol_num):
        self.protocol_switcher.get(protocol_num, lambda _: print("This protocol number is not registered."))

    def give_coordinates(self, dest, via):
        if dest not in self.destination:
            self.distance_table.append([[(float('inf'), -1, "")] * len(self.distance_table[0])])
            self.destination[dest] = len(self.destination)

        dest_coor = self.destination.get(dest)

        if via not in self.passing_node:
            for row in self.distance_table:
                row.append((float('inf'), -1, ""))
            self.passing_node[via] = len(self.passing_node)

        via_coor = self.passing_node.get(via)

        return dest_coor, via_coor

    def print_distance_table(self):
        for dest in self.destination:
            for via in self.passing_node:
                d_coor, v_coor = self.give_coordinates(dest, via)
                print(dest, via, self.distance_table[d_coor][v_coor])

    def initialize_table(self):
        self.destination = {}
        self.passing_node = {}

        size = len(self.neighbours_info)

        self.distance_table = [[(float('inf'), -1, "")] * size] * size

        for neighbour in self.neighbours_info:
            neighbour_virtual = neighbour.remote_virtual_IP
            self.destination[neighbour_virtual] = len(self.destination)
            self.passing_node[neighbour_virtual] = len(self.passing_node)

            dest_coor, via_coor = self.give_coordinates(neighbour_virtual, neighbour_virtual)
            self.distance_table[dest_coor][via_coor] = (1, neighbour.remote_physical_port, neighbour.remote_physical_IP)

        for neighbour in self.neighbours_info:
            for other in self.neighbours_info:
                dest_coor, via_coor = self.give_coordinates(neighbour.local_virtual_IP, other.local_virtual_IP)
                self.distance_table[dest_coor][via_coor] = (0, self.physical_port, self.physical_host)

        self.print_distance_table()

    def num_digits(self, number):
        count = 0
        while number > 0:
            number /= 10
            count += 1
        return count

    def show_interfaces(self):
        id_ = 0

        print("id    remote         local")

        for neighbor in self.neighbours_info:
            space_size = 6 - self.num_digits(id_)
            print(id_, " " * space_size, neighbor.remote_virtual_IP, " " * 5, neighbor.local_virtual_IP)
            id_ += 1

    def get_header(self, destination_port, local_virtual, protocol):
        return [self.physical_host, self.physical_port, destination_port, local_virtual, protocol]


    # def send_message(self, port, message):
    #     sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    #     header = self.get_header(, 0)

    def send_table(self):
        while True:
            for neighbour in self.neighbours_info:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                table_info = [self.distance_table, self.destination, self.passing_node]
                header = self.get_header(neighbour.remote_physical_port, neighbour.local_virtual_IP, 200)
                msg = pickle.dumps([header, table_info])
                sock.sendto(msg, (neighbour.remote_physical_IP, neighbour.remote_physical_port))
            time.sleep(1)

    def print_message(self, body):
        print(body)

    def receive_table(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((self.physical_host, self.physical_port))

        while True:
            data, address = sock.recvfrom(constant.MTU)
            msg = pickle.loads(data)
            header = msg[0]
            body = msg[1]
            source_physical_host = header[0]
            source_physical_port = header[1]
            destination_physical_port = header[2]
            virtual_IP = header[3]
            protocol_number = header[4]
            if protocol_number == 200:
                neigh_dist_table = body[0]
                neigh_destination_map = body[1]
                neigh_passing_map = body[2]
            elif protocol_number == 0:
                print(body)
            print("Received message:", msg)
