class Link:
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


def read_link_data(file_name):
    f = open(file_name, "r")
    contents = f.read()
    data = contents.split("\n")
    local_phys_address = data[0].split(" ")
    link = Link(local_phys_address[0], int(local_phys_address[1]))
    for info in data[1:]:
        if info == '':
            break
        address = info.split(" ")
        link.add_interface(LnxBody(address[0], int(address[1]), address[2], address[3]))
    return link
