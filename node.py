import socket
import pickle
import time
from link import Link


class Node:
    def __init__(self, physical_host, physical_port, neighbours_info):
        self.physical_host = physical_host
        self.physical_port = physical_port
        self.neighbours_info = neighbours_info
        self.destination = {}
        self.passing_node = {}
        self.distance_table = []
        self.last_updates = []
        self.initialize_table()
        self.registered_handlers = {}
        self.link = Link(self.run_handler, self.physical_host, self.physical_port)
        self.link.create_neighbour_sockets(len(neighbours_info))

    def register_handlers(self, protocol_num, handler):
        if protocol_num in self.registered_handlers:
            print("This protocol number is already registered.")
        else:
            self.registered_handlers[protocol_num] = handler

    def run_handler(self, packet):
        if packet[0][4] in self.registered_handlers:
            self.registered_handlers.get(packet[0][4])(packet)
        else:
            print("This protocol number is not registered.")

    def give_coordinates(self, dest, via):
        if via not in self.passing_node:
            for row in self.distance_table:
                row.append([float('inf'), -1, ""])
            for row in self.last_updates:
                row.append(0)
            self.passing_node[via] = len(self.passing_node)

            self.destination[dest] = len(self.destination)
            if len(self.distance_table) > 0:
                self.distance_table.append([[float('inf'), -1, ""]] * len(self.distance_table[0]))
                self.last_updates.append([0] * len(self.last_updates[0]))

            else:
                self.distance_table.append([[float('inf'), -1, ""]])
                self.last_updates.append([0])
        via_coor = self.passing_node.get(via)

        if dest not in self.destination:
            self.distance_table.append([[float('inf'), -1, ""]] * len(self.distance_table[0]))
            # self.last_updates.append(time.time())
            self.last_updates.append([0] * len(self.last_updates[0]))
            self.destination[dest] = len(self.destination)

        dest_coor = self.destination.get(dest)

        return dest_coor, via_coor

    # def check_for_unusable(self):
    #     for i in range(len(self.last_updates)):
    #         updated = False
    #         for j in range(len(self.last_updates[i])):
    #

    def print_distance_table(self):
        for dest in self.destination:
            print(dest, end="    ")
        print(" ")
        for i in range(len(self.distance_table)):
            for j in range(len(self.distance_table[i])):
                print(self.distance_table[i][j][0], end="              ")
            print(" ")

    def initialize_table(self):
        self.destination = {}
        self.passing_node = {}

        for neighbour in self.neighbours_info:
            for other in self.neighbours_info:
                dest_coor, via_coor = self.give_coordinates(neighbour.local_virtual_IP, other.local_virtual_IP)
                self.distance_table[dest_coor][via_coor] = [0, self.physical_port, self.physical_host]
                self.last_updates[dest_coor][via_coor] = -1

    def num_digits(self, number):
        count = 0
        if number == 0:
            return 1
        while number > 0:
            number = int(number/10)
            count += 1
        return count

    def get_header(self, destination_port, local_virtual, protocol):
        return [self.physical_host, self.physical_port, destination_port, local_virtual, protocol]

    def read_commands(self):
        while True:
            text = input("> ")
            items = (text.split(" "))
            if items[0] == "interfaces" or items[0] == "li":
                self.show_interfaces()

            elif items[0] == "routes" or items[0] == "lr":
                self.show_routes()

            elif items[0] == "down":
                print("Not Implemented.")

            elif items[0] == "up":
                print("Not Implemented.")

            elif items[0] == "send":
                if len(items) != 4:
                    print("Invalid form. Press help for more info.")
                else:
                    self.send_message(items[1], int(items[2]), items[3])

            elif items[0] == "q":
                print("Not Implemented.")
                quit(0)
                break

            else:
                print("- help, h: Print this list of commands\n"
                      "- interfaces, li: Print information about each interface, one per line\n"
                      "- routes, lr: Print information about the route to each known destination, one per line\n"
                      "- up [integer]: Bring an interface \"up\" (it must be an existing interface, "
                      "probably one you brought down)\n"
                      "- down [integer]: Bring an interface \"down\"\n"
                      "- send [ip] [protocol] [payload]: sends payload with protocol=protocol to virtual-ip ip\n"
                      "- q: quit this node\n")

    def find_addr(self, local_interface):
        i = 0
        for neigbour in self.neighbours_info:
            if neigbour.local_virtual_IP == local_interface:
                return neigbour.remote_physical_port, neigbour.remote_physical_IP, i
            i += 1

    def send_message(self, dest, protocol_number, message):
        local_interface, min_dist = self.find_hop(dest)
        port, host, i = self.find_addr(local_interface)
        header = self.get_header(port, local_interface, protocol_number)
        self.link.send_message([header, message], port, host, i)

    def send_table(self):
        while True:
            table_info = [self.distance_table, self.destination, self.passing_node]
            i = 0
            for neighbour in self.neighbours_info:
                header = self.get_header(neighbour.remote_physical_port, neighbour.local_virtual_IP, 200)
                self.link.send_message([header, table_info],
                                     neighbour.remote_physical_port, neighbour.remote_physical_IP, i)
                i += 1
            time.sleep(1)

    def print_message(self, message):
        print(message[1])

    def update_distance_table(self, message):
        header = message[0]
        body = message[1]
        source_physical_host = header[0]
        source_physical_port = header[1]
        virtual_ip = header[3]
        neigh_dist_table = body[0]
        neigh_destination_map = body[1]
        d_coor, v_coor = self.give_coordinates(virtual_ip, virtual_ip)
        if not (self.distance_table[d_coor][v_coor][0] == 1):
            self.distance_table[d_coor][v_coor][0] = 1
        for destination in neigh_destination_map:
            dest_index = neigh_destination_map[destination]
            min_distance = float('inf')
            for distance_info in neigh_dist_table[dest_index]:
                if min_distance > distance_info[0] and not(distance_info[1] == self.physical_port and distance_info[2] == self.physical_host):
                    min_distance = distance_info[0]
            d_coor, v_coor = self.give_coordinates(destination, virtual_ip)
            self.last_updates[d_coor][v_coor] = time.time()
            min_distance += 1
            if self.distance_table[d_coor][v_coor][0] >= min_distance:
                updated_data = [min_distance, source_physical_port, source_physical_host]
                self.distance_table[d_coor][v_coor] = updated_data
                self.last_updates[d_coor][v_coor] = time.time()

        neigh_index = self.passing_node[virtual_ip]
        for index in range(len(self.distance_table)):
            if not self.give_passing_node_virtual_by_index(index) in neigh_destination_map:
                self.distance_table[index][neigh_index][0] = float('inf')
                self.delete_inf_row_col_distance_table()
            # distance_info = self.distance_table[index][neigh_index]

            # else:
            #     neigh_dest_index = neigh_destination_map[self.give_passing_node_virtual_by_index(index)]
            #     min_entry = neigh_dist_table[neigh_dest_index][0]
            #     for d_info in neigh_dist_table[neigh_dest_index]:
            #         if min_entry[0] > d_info[0]:
            #             min_entry = d_info

    def give_passing_node_virtual_by_index(self, index):
        for virtual, i in self.passing_node.items():
            if index == i:
                return virtual

    def give_dest_node_virtual_by_index(self, index):
        for virtual, i in self.destination.items():
            if index == i:
                return virtual
            
    def search_for_local_interface(self, virtual):
        for neighbour in self.neighbours_info:
            if neighbour.remote_virtual_IP == virtual:
                return neighbour.local_virtual_IP
            return virtual

    def find_hop(self, dest):
        dest_index = self.destination[dest]
        min_dist = self.distance_table[dest_index][0][0]
        virtual_index = 0
        i = 0
        for dist_instance in self.distance_table[dest_index]:
            if min_dist > dist_instance[0]:
                min_dist = dist_instance[0]
                virtual_index = i
            i += 1
        if not min_dist ==0:
            local_interface = self.search_for_local_interface(self.give_passing_node_virtual_by_index(virtual_index))
        else:
            local_interface = dest
        return local_interface, min_dist

    def show_interfaces(self):
        id_ = 0

        print("id    rem            loc")

        for neighbor in self.neighbours_info:
            space_size = 6 - self.num_digits(id_)
            print(str(id_) + " " * space_size + neighbor.remote_virtual_IP + " " * 5 + neighbor.local_virtual_IP)
            id_ += 1

    def show_routes(self):
        print("cost    dst             loc")

        for dest in self.destination:
            local_interface, min_dist = self.find_hop(dest)
            if not min_dist == float('inf'):
                space_size = 8 - self.num_digits(min_dist)
                print(str(min_dist) + " " * space_size + dest + " " * 5 + local_interface)