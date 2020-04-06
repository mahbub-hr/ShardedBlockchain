import socket

T_PORT = 1111

TCP_IP = '127.0.0.1'

BUF_SIZE = 1024

MSG = b"0 A B 100"

for i in range(4):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:

        s.connect((TCP_IP, T_PORT))
        s.sendall(MSG)
        print(i,' sent: ', MSG)

