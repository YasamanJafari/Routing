import socket
import pickle
import constant


class LnxInfo:
    def __init__(self, local_physical_host, local_physical_port):
        self.local_physical_IP = local_physical_host
        self.local_physical_port = local_physical_port
        self.interfaces = []

    def add_interface(self, interface):
        self.interfaces.append(interface)


class LnxBody:
    def __init__(self, remote_physical_host, remote_physical_port, local_virtual, remote_virtual):
        self.remote_physical_IP = remote_physical_host
        self.remote_physical_port = remote_physical_port
        self.local_virtual_IP = local_virtual
        self.remote_virtual_IP = remote_virtual


class Link:
    def __init__(self, run_handler, physical_host, physical_port):
        self.run_handler = run_handler
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((physical_host, physical_port))
        self.send_sockets = []

    def create_neighbour_sockets(self, neighbours_count):
        for i in range(0, neighbours_count):
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.send_sockets.append(sock)

    def receive(self):
        return self.sock.recvfrom(constant.MTU)

    def receive_data(self):
        while True:
            data, address = self.receive()
            msg = pickle.loads(data)
            self.run_handler(msg)

    def send_table(self, message, neigh_remote_physical_port, neigh_local_virtual_host, index):
        msg = pickle.dumps(message)
        self.send_sockets[index].sendto(msg, (neigh_local_virtual_host, neigh_remote_physical_port))


def read_link_data(file_name):
    f = open(file_name, "r")
    contents = f.read()
    data = contents.split("\n")
    local_phys_address = data[0].split(" ")
    link = LnxInfo(local_phys_address[0], int(local_phys_address[1]))
    for info in data[1:]:
        if info == '':
            break
        address = info.split(" ")
        link.add_interface(LnxBody(address[0], int(address[1]), address[2], address[3]))
    return link
