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
        self.last_updates = []
        self.initialize_table()
        self.registered_handlers = {}

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
                row.append((float('inf'), -1, ""))
            for row in self.last_updates:
                row.append(0)
            self.passing_node[via] = len(self.passing_node)

            self.destination[dest] = len(self.destination)
            if len(self.distance_table) > 0:
                self.distance_table.append([(float('inf'), -1, "")] * len(self.distance_table[0]))
                self.last_updates.append([0] * len(self.last_updates[0]))

            else:
                self.distance_table.append([(float('inf'), -1, "")])
                self.last_updates.append([0])
        via_coor = self.passing_node.get(via)

        if dest not in self.destination:
            self.distance_table.append([(float('inf'), -1, "")] * len(self.distance_table[0]))
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
            print(dest,)
        for i in range(len(self.distance_table)):
            for j in range(len(self.distance_table[i])):
                print(self.distance_table[i][j], )

    def initialize_table(self):
        self.destination = {}
        self.passing_node = {}

        # size = len(self.neighbours_info)

        # self.distance_table = [[(float('inf'), -1, "")] * size] * size
        # self.last_updates = [0 * size] * size

        # for neighbour in self.neighbours_info:
        #     neighbour_virtual = neighbour.remote_virtual_IP
        #     self.destination[neighbour_virtual] = len(self.destination)
        #     self.passing_node[neighbour_virtual] = len(self.passing_node)
        #
        #     dest_coor, via_coor = self.give_coordinates(neighbour_virtual, neighbour_virtual)
        #     self.distance_table[dest_coor][via_coor] = (1, neighbour.remote_physical_port, neighbour.remote_physical_IP)

        for neighbour in self.neighbours_info:
            for other in self.neighbours_info:
                dest_coor, via_coor = self.give_coordinates(neighbour.local_virtual_IP, other.local_virtual_IP)
                self.distance_table[dest_coor][via_coor] = (0, self.physical_port, self.physical_host)
                self.last_updates[dest_coor][via_coor] = -1

    def num_digits(self, number):
        count = 0
        if number == 0:
            return 1
        while number > 0:
            number /= 10
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

    def send_message(self, dest, protocol_number, message):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        local_interface, min_dist, physical_addr = self.find_hop(dest)
        header = self.get_header(physical_addr[1], "", protocol_number)
        msg = pickle.dumps([header, message])
        sock.sendto(msg, (physical_addr[0], physical_addr[1]))

    def send_table(self):
        while True:
            for neighbour in self.neighbours_info:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                table_info = [self.distance_table, self.destination, self.passing_node]
                header = self.get_header(neighbour.remote_physical_port, neighbour.local_virtual_IP, 200)
                msg = pickle.dumps([header, table_info])
                sock.sendto(msg, (neighbour.remote_physical_IP, neighbour.remote_physical_port))
            time.sleep(1)

    def print_message(self, message):
        print(message[1])

    def update_distance_table(self, message):
        header = message[0]
        body = message[1]
        source_physical_host = header[0]
        source_physical_port = header[1]
        virtual_IP = header[3]
        neigh_dist_table = body[0]
        neigh_destination_map = body[1]
        d_coor, v_coor = self.give_coordinates(virtual_IP, virtual_IP)
        if not (self.distance_table[d_coor][v_coor] == 1):
            self.distance_table[d_coor][v_coor] = 1
        for destination in neigh_destination_map:
            dest_index = neigh_destination_map[destination]
            min_distance = neigh_dist_table[dest_index][0][0]
            for distance_info in neigh_dist_table[dest_index]:
                if min_distance > distance_info[0]:
                    min_distance = distance_info[0]
            d_coor, v_coor = self.give_coordinates(destination, virtual_IP)
            self.last_updates[d_coor][v_coor] = time.time()
            min_distance = min_distance+1
            if self.distance_table[d_coor][v_coor] > min_distance:
                updated_data = (min_distance, source_physical_port, source_physical_host)
                self.distance_table[d_coor][v_coor] = updated_data
                self.last_updates[d_coor][v_coor] = time.time()
        self.print_distance_table()

    def receive_data(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((self.physical_host, self.physical_port))

        while True:
            data, address = sock.recvfrom(constant.MTU)
            msg = pickle.loads(data)
            header = msg[0]
            protocol_number = header[4]
            self.run_handler(msg)
            # print("Received message:", msg)

    def search_for_local_interface(self, virtual):
        for neighbour in self.neighbours_info:
            if neighbour.remote_virtual_IP == virtual:
                return neighbour.local_virtual_IP

    def give_passing_node_virtual_by_index(self, index):
        for virtual, i in self.passing_node.items():
            if index == i:
                return virtual

    def find_hop(self, dest):
        dest_index = self.destination[dest]
        min_dist = self.distance_table[dest_index][0][0]
        physical_port = self.distance_table[dest_index][0][1]
        physical_IP = self.distance_table[dest_index][0][2]
        virtual_index = 0
        i = 0
        for dist_instance in self.distance_table[dest_index]:
            if min_dist > dist_instance[0]:
                min_dist = dist_instance[0]
                virtual_index = i
                physical_port = dist_instance[1]
                physical_IP = dist_instance[2]
            i += 1
        local_interface = self.search_for_local_interface(self.give_passing_node_virtual_by_index(virtual_index))
        return local_interface, min_dist, (physical_IP, physical_port)

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
            local_interface, min_dist, addr = self.find_hop(dest)
            if not min_dist == float('inf'):
                if not min_dist == 0:
                    print(str(min_dist) + " " * 7 + dest + " " * 5 + local_interface)
                else:
                    space_size = 8 - self.num_digits(min_dist)
                    print("0" + " " * space_size + dest + " " * 5 + dest)