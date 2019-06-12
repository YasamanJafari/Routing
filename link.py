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
        self.status = constant.UP


class Link:
    def __init__(self, run_handler, physical_host, physical_port):
        self.run_handler = run_handler
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((physical_host, physical_port))
        self.send_sockets = []
        self.message_contents = {}
        self.message_id = 0

    def break_to_chunks(self, message):
        parts = [message[i:i+constant.CHUNK_SIZE] for i in range(0, len(message), constant.CHUNK_SIZE)]
        return parts

    def create_neighbour_sockets(self, neighbours_count):
        for i in range(0, neighbours_count):
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.send_sockets.append(sock)

    def receive(self):
        return self.sock.recvfrom(constant.MTU)

    def send(self, msg, neigh_remote_physical_port, neigh_local_physical_host, index):
        self.send_sockets[index].sendto(msg, (neigh_local_physical_host, neigh_remote_physical_port))

    def is_complete(self, msg_id, size):
        contents = self.message_contents[msg_id]
        count = 0
        for item in contents:
            if item != "":
                count += 1
        return count == size

    def get_complete_msg(self, msg_id):
        contents = self.message_contents[msg_id]
        msg = b""
        for item in contents:
            msg += item
        message = pickle.loads(msg)
        del self.message_contents[msg_id]
        return message

    def receive_data(self):
        while True:
            data, address = self.receive()
            msg = pickle.loads(data)
            if msg[0] in self.message_contents:
                self.message_contents[msg[0]][msg[1]] = msg[3]
            else:
                self.message_contents[msg[0]] = [""] * msg[2]
                self.message_contents[msg[0]][msg[1]] = msg[3]
            if self.is_complete(msg[0], msg[2]):
                self.run_handler(self.get_complete_msg(msg[0]))

    def send_message(self, message, neigh_remote_physical_port, neigh_local_physical_host, index):
        parts = self.break_to_chunks(pickle.dumps(message))
        for i, part in enumerate(parts):
            msg = pickle.dumps([self.message_id, i, len(parts), part])
            self.send(msg, neigh_remote_physical_port, neigh_local_physical_host, index)
        self.message_id += 1


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
