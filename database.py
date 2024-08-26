import socket
import threading
import logging
import sys

class database:
    def __init__(self, max_size: int=-1, local_only: bool=True) -> None:
        # Init all provided operands
        self.local_only: bool = local_only
        self.max_size: int = max_size

        # Get logger
        self.logger = logging.getLogger()
        self.logger.addHandler(logging.StreamHandler(sys.stdout))

        # Setting the threshold of logger to DEBUG
        self.logger.setLevel(logging.DEBUG)

        self.logger.info(" [ Main ] Logger started.")

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
        self.running: bool = True

        # Define operations
        self.valid_operations: list[str] = ["read", "write"]
        self.restricted_operations: list[str] = ["send"]

        # Initialize TCP Server
        self.socket: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.logger.info(" [ Main ] Starting server.")

        self.socket.bind((socket.gethostbyname('localhost'), 56703))
        self.socket_thread = threading.Thread(target=self._tcp_server, args=())

        # Start Threads
        self.logger.info(" [ Main ] Starting threads.")
        self.socket_thread.start()

    def _tcp_server(self):
        self.socket.settimeout(1)
        
        def tcp_send(message: str, client: socket.socket, address: str):
            self.logger.info(f" [ TCP ] Sending message to {address}: '{message}'")
            client.send(len(message).to_bytes(4))
            client.send(message.encode())

            return

        # Define comm threads
        def send_clients(self: database):
            while self.running:
                try:
                    if self.qued_operations[0][0] == 0 and self.qued_operations[0][1][0:4] == "send": # Check operation type and operation
                        self.logger.debug(f" [ Send ] Qued sending operation recieved")
                        operation, target, data = self.qued_operations[0][1].split(' ')
                        self.logger.debug(f" [ Send ] Information: {operation}, {target}, {data}")

                        address_index = self.addresses.index(target)
                        self.clients[address_index].send(data)
                except IndexError:
                    pass

        def recv_client(self: database, client_address: str, client_offset: int):
            self.logger.debug(f" [ Client Handle ] Creating client recieving port for {client_address}")
            data = b""
            recv_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # For dual mode
            recv_sock.bind((socket.gethostbyname('localhost'), 56704+client_offset))

            recv_sock.settimeout(69.420)
            recv_sock.listen(1)

            _address = ""
            _client = 0

            while _address != client_address:
                try:
                    _client, _address = recv_sock.accept()
                    self.logger.debug(f" [ Client Handle ] Connection attempt by: {_address}")
                except TimeoutError:
                    self.logger.info(f" [ Client Handle ] Connection never recieved.")
                    break

            if _client:
                self.logger.debug(f" [ Client Handle ] {_address} was allowed")
            
                while True:
                    data = _client.recv(4) # Recieve a 4-byte integer detailing how big the command is
                    if not data: break
                    receive_lenght = int.from_bytes(data) # Decode
                    data = _client.recv(receive_lenght) # Recieve the actual data

                    self.logger.info(f" [ Client Handle ] '{data.decode()}' recieved from {_address}")
                    data = data.decode().split()

                    if data[0] in self.restricted_operations:
                        self.logger.debug(f" [ Client Handle ] '{data[0]}' is restricted and not for client use, sending error")
                        tcp_send("1 Restricted_operation 256", _client, _address) # Send error status, error, and error code
                    elif data[0] not in self.valid_operations:
                        self.logger.debug(f" [ Client Handle ] '{data[0]}' is not recognized, sending error")
                        tcp_send("1 Invalid_operation 255", _client, _address)
                    else:
                        data.insert(0, 1)
                        self.qued_operations.append(data)
                        tcp_send("0", _client, _address)

            self.logger.info(f" [Client Handle] Client {client_address} has disconnected")
            self.recv_threads.pop(client_offset-1)
            self.clients.pop(client_offset-1)
            self.addresses.pop(client_offset-1)

        # Initialize clients, addresses, and recieving threads
        self.clients: list[socket.socket] = []
        self.addresses: list[socket._Address] = []
        self.recv_threads: list[threading.Thread] = []

        self.logger.debug(" [ TCP ] TCP is listening")
        self.socket.listen(5)

        while self.running:
            try:
                s, a = self.socket.accept() # 's' is the socket, 'a' is the address
                self.logger.info(f" [ TCP ] Client {a} has connected")
                self.logger.debug(f" [ TCP ] Number of clients: {len(self.clients)+1}")

                self.clients.append(s)
                self.addresses.append(a)

                self.recv_threads.append(threading.Thread(target=recv_client, args=(self,a,len(self.clients))))
                self.recv_threads[-1].start()
            except TimeoutError:
                pass
            except KeyboardInterrupt:
                self.running = False

        self.logger.info("Shutting down...")
        return
    
    def database_handle(self):

        return
    
if __name__ == "__main__":
    logging.basicConfig(filename="newfile.log",
                    format='%(asctime)s %(message)s',
                    filemode='a',
                    )
    
    db = database()
