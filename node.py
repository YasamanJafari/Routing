import constant
import time
from link import Link


class Node:
    def __init__(self, physical_host, physical_port, neighbours_info, lock):
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
        self.trace_route_result = []
        self.trace_route_ttl = 1
        self.lock = lock
        self.trace_route_done = True
        self.trace_dest = None

    def register_handlers(self, protocol_num, handler):
        if protocol_num in self.registered_handlers:
            print("This protocol number is already registered.")
        else:
            self.registered_handlers[protocol_num] = handler

    def check_if_interface_is_mine(self, virtual):
        for neighbour in self.neighbours_info:
            if neighbour.local_virtual_IP == virtual:
                return True, neighbour
        return False, ""

    def run_handler(self, packet):
        if packet[0][4] in self.registered_handlers:
            exists, neighbour = self.check_if_interface_is_mine(packet[0][5])
            if exists and neighbour.status == constant.DOWN:
                return
            if not exists and packet[0][4] != constant.TRACEROUTE_QUERY_PROTOCOL_NUM:
                self.send_message(packet[0][5], packet[0][4], packet[1], packet[0][6])
                return
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
        via_coor = self.passing_node.get(via)

        if dest not in self.destination:
            self.destination[dest] = len(self.destination)
            if len(self.distance_table) > 0:
                self.distance_table.append([[float('inf'), -1, ""]] * len(self.distance_table[0]))
                self.last_updates.append([0] * len(self.last_updates[0]))
            else:
                self.distance_table.append([[float('inf'), -1, ""]])
                self.last_updates.append([0])
        dest_coor = self.destination.get(dest)

        return dest_coor, via_coor

    def check_for_out_of_date(self):
        while True:
            self.lock.acquire()
            for i in range(len(self.last_updates)):
                for j in range(len(self.last_updates[i])):
                    if self.last_updates[i][j] == -1:
                        continue
                    if time.time() - self.last_updates[i][j] > 5:
                        d_coor, v_coor = self.give_coordinates\
                            (self.give_destination_node_virtual_by_index(i), self.give_passing_node_virtual_by_index(j))
                        self.distance_table[d_coor][v_coor] = [float('inf'), -1, ""]
            self.delete_inf_row_col_distance_table()
            self.lock.release()
        time.sleep(3)

    def print_distance_table(self):
        self.lock.acquire()
        print("____________________DISTANCE_TABLE_______________")
        print(" ", end="              ")
        for passing in self.passing_node:
            print(passing, end="    ")
        print(" ")
        print("_________________________________________________")
        for i in range(len(self.distance_table)):
            print(self.give_destination_node_virtual_by_index(i), end="  | ")
            for j in range(len(self.distance_table[i])):
                print(self.distance_table[i][j][0], end="              ")
            print(" ")
        print("_________________________________________________")
        print("_________________________________________________\n\n")
        self.lock.release()

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

    def get_header(self, destination_port, local_virtual, protocol, dest, src):
        return [self.physical_host, self.physical_port, destination_port, local_virtual, protocol, dest, src]

    def read_commands(self):
        while True:
            text = input("> ")
            items = (text.split(" "))
            if items[0] == "interfaces" or items[0] == "li":
                if len(items) != 1:
                    print("Invalid form. Press help for more info.")
                    continue
                self.show_interfaces()

            elif items[0] == "routes" or items[0] == "lr":
                if len(items) != 1:
                    print("Invalid form. Press help for more info.")
                    continue
                self.show_routes()

            elif items[0] == "down":
                if len(items) != 2:
                    print("Invalid form. Press help for more info.")
                    continue
                self.down_interface(int(items[1]))

            elif items[0] == "up":
                if len(items) != 2:
                    print("Invalid form. Press help for more info.")
                    continue
                self.up_interface(int(items[1]))

            elif items[0] == "send":
                if len(items) < 4:
                    print("Invalid form. Press help for more info.")
                else:
                    msg = ""
                    for i, data in enumerate(items[3:]):
                        msg += data
                        if i != len(items[3:]) - 1:
                            msg += " "
                    self.send_message(items[1], int(items[2]), msg, None)

            elif items[0] == "q":
                if len(items) != 1:
                    print("Invalid form. Press help for more info.")
                    continue
                for i in range(len(self.neighbours_info)-1, 0, -1):
                    print(i, len(self.neighbours_info))
                    if not self.neighbours_info[i].status == constant.DOWN:
                        self.down_interface(i)

                print("Goodbye!")
                return

            elif items[0] == "traceroute":
                if len(items) != 2:
                    print("Invalid form. Press help for more info.")
                    continue
                self.trace_route(items[1])

            else:
                print("- help, h: Print this list of commands\n"
                      "- interfaces, li: Print information about each interface, one per line\n"
                      "- routes, lr: Print information about the route to each known destination, one per line\n"
                      "- up [integer]: Bring an interface \"up\" (it must be an existing interface, "
                      "probably one you brought down)\n"
                      "- down [integer]: Bring an interface \"down\"\n"
                      "- send [ip] [protocol] [payload]: sends payload with protocol=protocol to virtual-ip ip\n"
                      "- q: quit this node\n")

    def find_neigh_index(self, dest):
        for i, neigh in enumerate(self.neighbours_info):
            if neigh.remote_virtual_IP == dest:
                return i

    def send_message(self, dest, protocol_number, message, src):
        if dest not in self.destination:
            print("Destination is not reachable.")
            self.trace_route_done = True
            return
        local_interface, send_info, virtual_index = self.find_hop(dest)
        port = send_info[1]
        host = send_info[2]

        i = self.find_neigh_index(self.give_passing_node_virtual_by_index(virtual_index))

        if i is None:
            return

        if src is None:
            src = local_interface
        header = self.get_header(port, local_interface, protocol_number, dest, src)
        self.link.send_message([header, message], port, host, i)

    def send_table(self):
        while True:
            self.lock.acquire()
            table_info = [self.distance_table, self.destination, self.passing_node]

            for i, neighbour in enumerate(self.neighbours_info):
                if not neighbour.status == constant.DOWN:
                    header = self.get_header(neighbour.remote_physical_port, neighbour.local_virtual_IP, 200, neighbour.remote_virtual_IP, neighbour.local_virtual_IP)
                    self.link.send_message([header, table_info],
                                         neighbour.remote_physical_port, neighbour.remote_physical_IP, i)
            self.lock.release()
            time.sleep(1)

    def print_message(self, message):
        print(message[1])

    def up_interface(self, interface_id):
        if interface_id < 0 or interface_id >= len(self.neighbours_info):
            print("This interface_id does not exist")
        elif self.neighbours_info[interface_id].status == constant.UP:
            print("This interface is already up.")
        else:
            interface_to_up = self.neighbours_info[interface_id]
            virtual_IP = interface_to_up.remote_virtual_IP
            for interface in self.neighbours_info:
                if interface.status != constant.DOWN:
                    dest_coor, via_coor = self.give_coordinates(virtual_IP, interface.local_virtual_IP)
                    self.distance_table[dest_coor][via_coor] = [0, self.physical_port, self.physical_host]
                    self.last_updates[dest_coor][via_coor] = -1
                    dest_coor, via_coor = self.give_coordinates(interface.local_virtual_IP, virtual_IP)
                    self.distance_table[dest_coor][via_coor] = [0, self.physical_port, self.physical_host]
                    self.last_updates[dest_coor][via_coor] = -1
            self.neighbours_info[interface_id].status = constant.UP

    def down_interface(self, interface_id):
        if interface_id < 0 or interface_id >= len(self.neighbours_info):
            print("This interface_id does not exist")
        elif self.neighbours_info[interface_id].status == constant.DOWN:
            print("This interface is already down.")
        else:
            interface_to_down = self.neighbours_info[interface_id]
            rem_virtual_IP = interface_to_down.remote_virtual_IP
            loc_virtual_IP = interface_to_down.local_virtual_IP

            should_del_dests = [self.destination[loc_virtual_IP]]
            should_del_passings = [self.passing_node[loc_virtual_IP]]
            if rem_virtual_IP in self.destination:
                should_del_dests.append(self.destination[rem_virtual_IP])
            if rem_virtual_IP in self.passing_node:
                should_del_passings.append(self.passing_node[rem_virtual_IP])

            self.delete_dests(should_del_dests)
            self.delete_passings(should_del_passings)

            self.neighbours_info[interface_id].status = constant.DOWN

    def update_distance_table(self, message):
        header = message[0]
        body = message[1]
        source_physical_host = header[0]
        source_physical_port = header[1]
        virtual_ip = header[3]
        neigh_dist_table = body[0]
        neigh_destination_map = body[1]

        self.lock.acquire()
        d_coor, v_coor = self.give_coordinates(virtual_ip, virtual_ip)
        if not (self.distance_table[d_coor][v_coor][0] == 1):
            self.distance_table[d_coor][v_coor] = [1, source_physical_port, source_physical_host]

            self.last_updates[d_coor][v_coor] = time.time()
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
                if min_distance > 64:
                    min_distance = float('inf')
                updated_data = [min_distance, source_physical_port, source_physical_host]
                self.distance_table[d_coor][v_coor] = updated_data
                self.last_updates[d_coor][v_coor] = time.time()

        neigh_index = self.passing_node[virtual_ip]
        for index in range(len(self.distance_table)):
            if not self.give_destination_node_virtual_by_index(index) in neigh_destination_map:
                if not self.distance_table[index][neigh_index][0] == float('inf'):
                    self.distance_table[index][neigh_index][0] = float('inf')
                    self.last_updates[index][neigh_index] = time.time()

        self.delete_inf_row_col_distance_table()
        self.lock.release()

    def give_passing_node_virtual_by_index(self, index):
        for virtual, i in self.passing_node.items():
            if index == i:
                return virtual

    def give_destination_node_virtual_by_index(self, index):
        for virtual, i in self.destination.items():
            if index == i:
                return virtual

    def row_is_infinity(self, i):
        for dist_item in self.distance_table[i]:
            if not dist_item[0] == float('inf'):
                return False
        return True

    def col_is_infinity(self, i):
        for dist_item in self.distance_table[:][i]:
            if not dist_item[0] == float('inf'):
                return False
        return True

    def update_dest_map_after(self, i):
        for virtual, index in self.destination.items():
            if index > i:
                self.destination[virtual] = index - 1

    def update_passing_map_after(self, i):
        for virtual, index in self.passing_node.items():
            if index > i:
                self.passing_node[virtual] = index - 1

    def delete_dests(self, dests):
        dests.sort()
        while len(dests) > 0:
            del self.distance_table[dests[0]]
            del self.destination[self.give_destination_node_virtual_by_index(dests[0])]
            self.update_dest_map_after(dests[0])
            del dests[0]
            for i in range(len(dests)):
                dests[i] -= 1

    def delete_passings(self, passings):
        passings.sort()
        while len(passings) > 0:
            for row in self.distance_table:
                del row[passings[0]]
            del self.passing_node[self.give_passing_node_virtual_by_index(passings[0])]
            self.update_passing_map_after(passings[0])
            del passings[0]
            for i in range(len(passings)):
                passings[i] -= 1

    def delete_inf_row_col_distance_table(self):
        inf_row = []
        inf_col = []

        for i in range(len(self.distance_table)):
            if self.row_is_infinity(i):
                inf_row.append(i)
        for j in range(len(self.distance_table[0])):
            if self.col_is_infinity(j):
                inf_col.append(j)
        self.delete_dests(inf_row)
        self.delete_passings(inf_col)

    def search_for_connected_local_interface(self, virtual):
        for neighbour in self.neighbours_info:
            if neighbour.remote_virtual_IP == virtual:
                return neighbour.local_virtual_IP

    def find_hop(self, dest):
        dest_index = self.destination[dest]
        min_dist = self.distance_table[dest_index][0][0]
        virtual_index = 0

        for i, dist_instance in enumerate(self.distance_table[dest_index]):
            if min_dist > dist_instance[0]:
                min_dist = dist_instance[0]
                virtual_index = i
        if not (min_dist == 0):
            local_interface = self.search_for_connected_local_interface(self.give_passing_node_virtual_by_index(virtual_index))
        else:
            local_interface = dest
        # return local_interface, min_dist

        return local_interface, self.distance_table[dest_index][virtual_index], virtual_index

    def show_interfaces(self):
        print("id    rem             loc")

        for i, neighbor in enumerate(self.neighbours_info):
            if not neighbor.status == constant.DOWN:
                space_size = 6 - self.num_digits(i)
                print(str(i) + " " * space_size + neighbor.remote_virtual_IP + " " * 5 + neighbor.local_virtual_IP)

    def show_routes(self):
        print("cost    dst             loc")

        for dest in self.destination:
            local_interface, distance_info, virtual_index = self.find_hop(dest)
            min_dist = distance_info[0]
            if not min_dist == float('inf'):
                space_size = 8 - self.num_digits(min_dist)
                print(str(min_dist) + " " * space_size + dest + " " * 5 + local_interface)

    def trace_route(self, virtual_ip):
        self.trace_route_done = False
        self.trace_dest = virtual_ip
        is_mine, neigh = self.check_if_interface_is_mine(virtual_ip)
        if is_mine:
            self.trace_route_done = True
            print("Traceroute from", virtual_ip, "to", virtual_ip)
            print(1, virtual_ip)
            print("Traceroute finished in", 1, "hops")
        else:
            self.send_message(virtual_ip, constant.TRACEROUTE_QUERY_PROTOCOL_NUM, 1, None)
        self.trace_route_result = []

        while not self.trace_route_done:
            continue

    def handle_trace_route_query(self, message):
        header = message[0]
        packet_ttl = message[1]

        local_virtual = header[3]
        dest = header[5]
        src = header[6]

        if packet_ttl == 1:
            self_virtual = self.search_for_connected_local_interface(local_virtual)
            is_mine, nei = self.check_if_interface_is_mine(dest)
            send_msg = [local_virtual, self_virtual]
            if is_mine and not(dest == self_virtual):
                send_msg.append(dest)

            self.send_message(src, constant.TRACEROUTE_RESPONSE_PROTOCOL_NUM, send_msg, self_virtual)
        else:
            new_ttl = packet_ttl - 1
            self.send_message(dest, constant.TRACEROUTE_QUERY_PROTOCOL_NUM, new_ttl, src)

    def print_hops(self):
        print("Traceroute from", self.trace_route_result[0], "to", self.trace_route_result[-1])

        index = 1
        for hop in self.trace_route_result:
            print(index, hop)
            index += 1

        print("Traceroute finished in", index - 1, "hops")

    def handle_trace_route_response(self, message):
        header = message[0]
        body = message[1]

        dest = header[5]
        src = header[6]

        is_mine, nei = self.check_if_interface_is_mine(dest)
        if is_mine:
            for item in body:
                self.trace_route_result.append(item)
            if self.trace_dest in self.trace_route_result:
                self.print_hops()
                self.trace_route_result = []
                self.trace_route_ttl = 1
                self.trace_route_done = True
            else:
                self.trace_route_ttl += 1
                self.send_message(self.trace_dest, constant.TRACEROUTE_QUERY_PROTOCOL_NUM, self.trace_route_ttl, None)
        else:
            self.send_message(dest, constant.TRACEROUTE_RESPONSE_PROTOCOL_NUM, body, src)


