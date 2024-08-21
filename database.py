import socket
import threading

class database:
    def __init__(self, max_size: int=-1, local_only: bool=True) -> None:
        # Init all provided operands
        self.local_only: bool = local_only
        self.max_size: int = max_size

        # All qued operations
        # A qued operation follows the following structure:
        #  que list    Operation source    Operation   Client
        #    \        /                   /           /
        #     [ ... [0,                  "read 1,1",  "192.168.1.61"] ... ]
        #           ^-----------------------------------------------^
        #                                   \
        #                              qued operation
        #
        # Operation type: either 0 or 1. 0 is an internal operation, 1 is external (requested by a client)
        # Operation: the operation to be executed
        # Client: used only for external operations, lists the IP of the client who requested the command
        #
        self.qued_operations: list[str] = []
        self.running = True

        # Initialize TCP Server
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.socket.bind((socket.gethostbyname('localhost'), 56703))
        self.socket_thread = threading.Thread(target=self._tcp_server, args=())

        # Start Threads
        self.socket_thread.start()

    def _tcp_server(self):
        # Define comm threads
        def send_clients(self: database):
            while self.running:
                try:
                    if self.qued_operations[0][0] == 0 and self.qued_operations[0][1][0:4] == "send": # Check operation type and operation
                        operation, target, data = self.qued_operations[0][1].split(' ')

                        address_index = addresses.index(target)
                        clients[address_index].send()
                except IndexError:
                    pass

        def recv_clients(self: database):
            pass
        
        # Initialize clients and addresses
        clients: list[socket.socket] = []
        addresses: list[socket._Address] = []

        self.socket.listen(5)
        self.socket.settimeout(1)

        while self.running:
            try:
                s, a = self.socket.accept() # 's' is the socket, 'a' is the address
            except TimeoutError:
                pass

        print("Done.")
        return
    
if __name__ == "__main__":
    db = database()
