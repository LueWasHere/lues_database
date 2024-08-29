import socket

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((socket.gethostbyname('localhost'), 56703))
print("Connection Success.")

s.settimeout(3.0)
data = s.recv(4)
data = int(s.recv(int.from_bytes(data)).decode())

print(data)

s_d = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s_d.connect((socket.gethostbyname('localhost'), data))

msg = "read 0,0"

s_d.send(len(msg).to_bytes(4))
s_d.send(msg.encode())

data = s.recv(4)
data = int(s.recv(int.from_bytes(data)).decode())

print(data)

s.close()
s_d.close()