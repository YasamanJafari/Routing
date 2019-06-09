import math


class Node:
    def __init__(self, physical_host, physical_port, neighbours_info):
        self.physical_host = physical_host
        self.physical_port = physical_port
        self.neighbours_info = neighbours_info
        self.destination = {}
        self.passing_node = {}
        self.distance_table = []

    def give_coordinates(self, dest, via):
        if dest in self.destination:
            dest_coor = self.destination[dest]

        if via in self.passing_node:
            via_coor = self.passing_node[via]

        return dest_coor, via_coor

    def initialize_table(self):
        self.destination = {}
        self.passing_node = {}

        size = len(self.neighbours_info)

        self.distance_table = [[(math.inf, -1, "")] * size] * size

        for neighbour in self.neighbours_info:
            neighbour_virtual = neighbour.remote_virtual_IP
            self.destination[neighbour_virtual] = len(self.destination)
            self.passing_node[neighbour_virtual] = len(self.passing_node)

            dest_coor, via_coor = self.give_coordinates(neighbour_virtual, neighbour_virtual)
            self.distance_table[dest_coor][via_coor] = (1, neighbour.remote_physical_port, neighbour.remote_physical_IP)



