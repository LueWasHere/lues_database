import socket
import threading
import logging
import sys

class database:
    def __init__(self, max_size: int=-1, local_only: bool=True, read_only: bool=False, read_protect_password: str="", write_protect_password: str="") -> None:
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

        # Initialize database thread
        self.database_thread = threading.Thread(target=self.database_handle, args=(max_size, read_only, read_protect_password, write_protect_password, True, ["test1", "test2"]))

        # Start Threads
        self.logger.info(" [ Main ] Starting threads.")
        self.socket_thread.start()
        self.database_thread.start()

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
                        self.logger.debug(f" [ Send ] Before parse: {self.qued_operations[0][1]}")
                        operation, target, data = self.qued_operations[0][1].split(' ')
                        self.logger.debug(f" [ Send ] Information: {operation}, {target}, {data}")

                        target = target.replace('(', '').replace(')', '').replace("'", '').split(',')
                        target[1] = int(target[1])

                        address_index = self.addresses.index(tuple(target))
                        tcp_send(data, self.clients[address_index], tuple(target))

                        self.qued_operations.pop(0)
                except IndexError:
                    pass

        def recv_client(t_client: socket.socket, self: database, client_address: tuple, client_offset: int):
            this_thread = self.recv_threads[client_offset-1]
            
            self.logger.debug(f" [ Client Handle ] Creating client recieving port for {client_address}")
            data = b""
            recv_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # For dual mode
            recv_sock.bind((socket.gethostbyname('localhost'), 56704+client_offset))

            self.qued_operations.append([0, f"send {str(client_address).replace(' ', '')} {56704+client_offset}"])
            #print(self.qued_operations)

            recv_sock.settimeout(69.420)
            recv_sock.listen(1)

            _address = "1"
            _client = 0

            while _address[0] != client_address[0]:
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
                        tcp_send("1,Restricted_operation,256", _client, _address) # Send error status, error, and error code
                    elif data[0] not in self.valid_operations:
                        self.logger.debug(f" [ Client Handle ] '{data[0]}' is not recognized, sending error")
                        tcp_send("1,Invalid_operation,255", _client, _address)
                    else:
                        data = [" ".join(data)]
                        data.insert(0, 1)
                        data.append(client_address)
                        self.qued_operations.append(data)
                        self.logger.info(f" [ Client Handle ] Qued {data} for {_address}")
                        #tcp_send("0", _client, _address)

            self.logger.info(f" [ Client Handle ] Client {client_address} has disconnected")
            self.recv_threads.pop(self.recv_threads.index(this_thread))
            self.clients.pop(self.clients.index(t_client))
            self.addresses.pop(self.addresses.index(client_address))

        # Initialize clients, addresses, and recieving threads
        self.clients: list[socket.socket] = []
        self.addresses: list[socket._Address] = []
        self.recv_threads: list[threading.Thread] = []

        self.logger.debug(" [ TCP ] TCP is listening")
        self.socket.listen(5)

        # Initialize sending thread
        self.send_thread = threading.Thread(target=send_clients, args=(self,))
        self.send_thread.start()

        while self.running:
            try:
                s, a = self.socket.accept() # 's' is the socket, 'a' is the address
                self.logger.info(f" [ TCP ] Client {a} has connected")
                self.logger.debug(f" [ TCP ] Number of clients: {len(self.clients)+1}")

                self.clients.append(s)
                self.addresses.append(a)

                self.recv_threads.append(threading.Thread(target=recv_client, args=(s,self,a,len(self.clients))))
                self.recv_threads[-1].start()
            except TimeoutError:
                pass
            except KeyboardInterrupt:
                self.running = False

        self.logger.info("Shutting down...")
        return
    
    def database_handle(self, size_cap: int, read_only: bool=False, read_protect_password: str="", write_protect_password: str="", create_new: bool=False, headers: list[str]=[]):
        self.size_cap = size_cap
        self.read_only = read_only
        self.read_protect_password = read_protect_password
        self.write_protect_password = write_protect_password
        self.logger.info(" [ Database_handle ] Database starting...")
        self.logger.debug(f" [ Database_handle ] Params: size_cap | {size_cap}, read_only | {read_only}, read_protect_password | {'*' * len(read_protect_password)}, write_protect_password | {'*' * len(write_protect_password)}, create_new | {create_new}, headers | {headers}")

        self.write_buffer = ""

        if create_new:
            self.logger.info(" [ Database_handle ] Creating new database...")
            self.head = headers
            self.db_content = []
        else:
            self.logger.debug(" [ Database_handle ] Using existing database...")
            with open("database.db", 'r') as DBFile:
                db_content = DBFile.read()
                DBFile.close()

            db_content = db_content.split('\n')
            self.head = db_content[0].split(',')
            db_content.pop(0)
            self.db_content = db_content

        self.logger.info(" [ Database_handle ] Started!")
        while self.running:
            if len(self.qued_operations) > 0:
                operation = self.qued_operations[0]
                if operation[1][0:4] == "read":
                    self.logger.info(" [ Database_handle ] read request recieved")
                    proceed = True
                    
                    if operation[0] == 0:
                        self.logger.debug(" [ Database_handle ] internal read")
                        source, _operation = operation[0], operation[1]
                    else:
                        self.logger.info(" [ Database_handle ] external read")
                        source, _operation, client = operation[0], operation[1], operation[2]

                    full_operation = _operation.split(' ')
                    self.logger.info(f" [ Database_handle ] operation: {_operation}")

                    if self.read_protect_password != "" and source != 0: 
                        try:
                            pass_compare = full_operation[2]
                            if pass_compare != self.read_protect_password:
                                self.logger.info(f" [ Database_handle ] Incorrect read password! Client provided: {pass_compare}")
                                self.qued_operations.append([0, f"send {str(client).replace(' ', '')} 1,Incorrect_pass,90"]) # Send an error, the password is incorrect
                                proceed = False
                        except IndexError:
                            self.logger.info(" [ Database_handle ] Client provided no read password! This data base is read-pass protected!")
                            self.qued_operations.append([0, f"send {str(client).replace(' ', '')} 1,Pass_not_provided,91"]) # Send an error, the password was not provided
                            proceed = False

                    if proceed:
                        self.logger.info(" [ Database_handle ] All clear. Beginning read.")

                        # Parse the read
                        self.logger.debug(f" [ Database_handle ] pre-context: {full_operation}")
                        _context = full_operation[1].split(',')
                        try: 
                            if _context[1][1] == '"': _context[1] = self.head.index(_context[1])
                        except IndexError: pass
                        _context[0] = int(_context[0])
                        _context[1] = int(_context[1])
                        self.logger.info(f" [ Database_handle ] Context: ({_context[0]}, {_context[1]})")

                        try:
                            r_product = self.db_content[_context[0]][_context[1]]
                            self.qued_operations.append([0, f"send {str(client).replace(' ', '')} 0,{r_product.replace(' ', '_')}"])
                            self.logger.info(f" [ Database_handle ] read success. '{r_product}' was read and sent to client")
                        except IndexError:
                            self.qued_operations.append([0, f"send {str(client).replace(' ', '')} 1,Read_out_of_bounds,300"])
                            self.logger.error(" [ Database_handle ] read is out of bounds")
                        except NameError:
                            self.qued_operations.append([0, f"result {operation.replace(' ', '_')} {r_product}"])
                            self.logger.info(f" [ Database_handle ] read success. '{r_product}' was read and provided to internal")

                    self.qued_operations.pop(0)
                elif operation[1][0:5] == "write":
                    proceed = True

                    if operation[0] == 0:
                        source, _operation = operation.split()
                    else:
                        source, _operation, client = operation.split()
        return
    
if __name__ == "__main__":
    logging.basicConfig(filename="newfile.log",
                    format='%(asctime)s %(message)s',
                    filemode='a',
                    )
    
    db = database()
