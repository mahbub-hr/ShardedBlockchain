from hashlib import sha256
import json
import time
import socket
import selectors
import pickle


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


class Block:
    def __init__(self, index, transactions, timestamp, previous_hash):
        """
        Constructor for the `Block` class.
        :param index:         Unique ID of the block.
        :param transactions:  List of transactions.
        :param timestamp:     Time of generation of the block.
        :param previous_hash: Hash of the previous block in the chain which this block is part of.                                        
        """
        self.index = index
        self.transactions = transactions
        self.timestamp = timestamp
        self.previous_hash = previous_hash  # Adding the previous hash field

    def compute_hash(self):
        """
        Returns the hash of the block instance by first converting it
        into JSON string.
        """
        block_string = json.dumps(self.__dict__,
                                  sort_keys=True)  # The string equivalent also considers the previous_hash field now
        return sha256(block_string.encode()).hexdigest()

    def persist_bock(self):
        filename = repr(self.index) + ".block"
        with open(filename, 'wb') as f:
            pickle.dump(self, f, pickle.HIGHEST_PROTOCOL)
        return


class Blockchain:

    def __init__(self):
        """
        Constructor for the `Blockchain` class.
        """
        self.chain = []
        self.create_genesis_block()

    def create_genesis_block(self):
        """
        A function to generate genesis block and appends it to
        the chain. The block has index 0, previous_hash as 0, and
        a valid hash.
        """
        genesis_block = Block(0, [], time.time(), "0")
        genesis_block.hash = genesis_block.compute_hash()
        self.chain.append(genesis_block)

    @property
    def last_block(self):
        """
        A quick pythonic way to retrieve the most recent block in the chain. Note that
        the chain will always consist of at least one block (i.e., genesis block)
        """
        return self.chain[-1]

    def add_block(self, block):
        """
        A function that adds the block to the chain after verification.
        Verification includes:******validation not implemented yet********
        * Checking if the proof is valid.
        * The previous_hash referred in the block and the hash of a latest block
          in the chain match.
        """
        previous_hash = self.last_block.hash

        if previous_hash != block.previous_hash:
            return False

        self.chain.append(block)
        return True

    def is_valid(self):
        """
        need to be implemented
        :return:
        """
    pass

    def persist_chain(self):
        """
        save blockchain to disk
        :return:
        """
        size = len(self.chain)
        for i in range(size):
            self.chain[i].persist_block()
        return


blockchain = Blockchain()


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
    blockstr = ""
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

        blockstr += str.decode()+'\n'
        COUNT += 1
        if COUNT == BLOCK_SIZE:
            block = Block(GLOBAL_BLOCK_COUNT, blockstr, time.time(), blockchain.last_block.hash)
            block.hash = block.compute_hash()
            block.persist_bock()
            blockchain.add_block(block)
            COUNT = 0
            block = ""
            GLOBAL_BLOCK_COUNT += 1
