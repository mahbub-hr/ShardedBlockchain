from hashlib import sha256
import time
import json
import pickle
from urllib.parse import urlparse


class Block:
    def __init__(self, index, transactions, timestamp, previous_hash):

        self.index = index
        self.transactions = transactions
        self.timestamp = timestamp
        self.previous_hash = previous_hash  # Adding the previous hash field

    def compute_hash(self):

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
        self.current_transactions = []
        self.peers = set()
        self.create_genesis_block()

    def create_genesis_block(self):
        genesis_block = Block(0, [], time.time(), "0")
        genesis_block.hash = genesis_block.compute_hash()
        self.chain.append(genesis_block)

    @property
    def last_block(self):
        return self.chain[-1]

    def add_block(self, block):
        previous_hash = self.last_block.hash

        if previous_hash != block.previous_hash:
            return False

        self.chain.append(block)
        return True

    def new_transaction(self, sender, recipient, amount):

        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
        })

        return self.last_block.index + 1

    def register_node(self, address):
        """
        Add a new node to the list of nodes
        :param address: Address of node. Eg. 'http://192.168.0.5:5000'
        """

        parsed_url = urlparse(address)
        if parsed_url.netloc:
            self.nodes.add(parsed_url.netloc)
        elif parsed_url.path:
            # Accepts an URL without scheme like '192.168.0.5:5000'.
            self.nodes.add(parsed_url.path)
        else:
            raise ValueError('Invalid URL')

    def is_valid(self):
        """
        need to be implemented
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

