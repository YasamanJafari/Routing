

class Node:
    def __init__(self, physical_host, physical_port, neighbours_info):
        self.physical_host = physical_host
        self.physical_port = physical_port
        self.neighbours_info = neighbours_info
        self.destination = {}
        self.passing_node = {}
        self.distance_table = []

        self.initialize_table()

    def give_coordinates(self, dest, via):
        if dest in self.destination:
            dest_coor = self.destination.get(dest)

        if via in self.passing_node:
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

        self.print_distance_table()

    def numDigits(self, number):
        count  = 0
        while(number > 0):
            number /= 10
            count += 1
        return count

    def show_interfaces(self):
        id_ = 0

        print("id    remote         local")

        for neighbor in self.neighbours_info:
            space_size = 6 - self.numDigits(id_)
            print(id_, " " * space_size, neighbor.remote_virtual_IP, " "* 5, neighbor.local_virtual_IP)
            id_ += 1



