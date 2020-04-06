import socket
import selectors


sel = selectors.DefaultSelector()
T_PORT = 1111
TCP_IP = '127.0.0.1'
BUF_SIZE = 30
BLOCK_SIZE = 4
PREV_HASH = ""
COUNT = 0
GLOBAL_BLOCK_COUNT = 0


class worldState:
    pass


def block_write(block):
    print('inside block!!!!')
    global GLOBAL_BLOCK_COUNT
    strs = repr(GLOBAL_BLOCK_COUNT)
    strs+='.block'
    file = open(strs, 'w')
    print('writing ', block)
    file.write(block)
    file.close()
    GLOBAL_BLOCK_COUNT = GLOBAL_BLOCK_COUNT + 1
    return


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    sock.bind((TCP_IP, T_PORT))

    sock.listen(5)
    print('listenning at : ',TCP_IP, 'Port: ', T_PORT)
    while True:
        conn, addr = sock.accept()
        with conn:
            print("connection address is : ", addr)
            str=b""
            while True:
                data = conn.recv(BUF_SIZE)
                str+=data
                if not data:
                    break
                print("s: ", data)

        block = ""
        block = block + str.decode()+'\n'
        COUNT += 1
        if COUNT == BLOCK_SIZE:
            block_write(block)
            COUNT = 0
