# Link_Layer
This is the last project of Computer Networks course at University of Tehran.

In this project, forwarding and routing functions are implemented.
Interfaces can be disabled and enabled, nodes can be added or leave the network and tables will be updated dynamically.
To implement this, distance vector algorithm(which uses Bellman-Ford algorithm) is used.
Packets and messages which can be user messages, distance tables, etc. are first broken into chunks and then sent to other nodes.
Different threads and locking mechanisms are used to be able to implement the mentioned functionalities.
Also, using ICMP Time Exceeded messages, we implemented traceroute to have the entire path from source to destinations.
