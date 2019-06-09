import math;


class Node:
    def __init__(self, physical_host, physical_port, neighbours_info):
        self.physical_host = physical_host
        self.physical_port = physical_port
        self.neighbours_info = neighbours_info

    def giveCoordinates(self, dest, via):
        if(dest in self.destination):
            destCoor = self.destination[dest]

        if(via in self.passingNode):
            viaCoor = self.passingNode[via]

    def initialize_table(self):
        self.destination = {}
        self.passingNode = {}

        size = len(self.neighbours_info)

        self.distanceTable = [[(math.inf, -1, "")] * size] * size
        for neighbour in self.neighbours_info:
            neighbourVirtualIP = neighbour.remote_virtual_IP
            self.destination[neighbourVirtualIP] = len(self.destination)
            self.passingNode[neighbourVirtualIP] = len(self.passingNode)





