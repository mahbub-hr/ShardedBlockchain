from hashlib import sha256
import time
import json
import pickle
from urllib.parse import urlparse


class ShardInfoTracker:
    def __init__(self):
        self.node_to_shard = {}
        self.shard_to_node = {}

    def insert(self, node, shard):
        if node not in self.node_to_shard:
            self.node_to_shard[node] =[]
        if shard not in self.shard_to_node:
            self.shard_to_node[shard] = []

        self.node_to_shard[node].append(shard)
        self.shard_to_node[shard].append(node)

    def insert_dict(self, node_shard):
        for node in node_shard:
            if node not in self.node_to_shard:
                self.node_to_shard[node] = []
            self.node_to_shard[node].extend(node_shard[node])

            for shard in node_shard[node]:
                if shard not in self.shard_to_node:
                    self.shard_to_node[shard] = []
                self.shard_to_node[shard].append(node)

    def remove_shard(self, shard):
        node = self.shard_to_node[shard].pop(0)
        self.node_to_shard[node].remove(shard)
        return node


    def print(self):
        print(json.dumps(self.node_to_shard, indent=4))

    def printshard(self):
        print(json.dumps(self.shard_to_node, indent=4))

class Worldstate:
    def __init__(self):
        self.worldstate = {}
        with open("initial_balance.txt",'r') as f:
            for line in f:
                key, value = line.partition(" ")[::2]
                self.worldstate[key.strip()] = float(value)

    def insert(self, key, value):
        self.worldstate['key'] = value

    def update(self, sender, receiver, amount):
        # need a check for double spending
        if self.worldstate[sender] < amount:
            return False

        self.worldstate[sender] = self.worldstate[sender] - amount
        self.worldstate[receiver] = self.worldstate[receiver] + amount
        #return a list of valid and invalid transactions
        return True
    def update_with_block(self,block):
        update_log = {}
        update_log['valid'] = []
        update_log['invalid'] = []
        
        for tx in block.transactions:
            ret=self.update(tx['sender'], tx['recipient'], tx['amount'])
            if not ret:
                update_log['invalid'].append(tx)
            update_log['valid'].append(tx)
        return update_log

    def get(self, key):
        return self.worldstate[key]

    def print(self):
        print(json.dumps(self.worldstate, indent=4))


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

    def load_block(self):
        pass


class Blockchain:
    def __init__(self):
        self.chain = []
        self.current_transactions = []
        self.create_genesis_block()

    def create_genesis_block(self):
        genesis_block = Block(0, [], 0, "0")
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
        self.current_transactions = []
        return True

    def add_block_on_shard(self,block, previous_hash):
        #this check is must , but i will implement it later
        #if previous_hash != block.previous_hash:
         #   return False

        self.chain.append(block)
        return True

    def new_transaction(self, ts,sender, recipient, amount):

        self.current_transactions.append({
            'ts' : ts,
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
        })

        return self.last_block.index + 1

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

    def remove_shard(self, shard, SHARD_SIZE):
        end = shard*SHARD_SIZE
        temp=[]
        length = len(self.chain)
        for i in range(1,length):
            if end == self.chain[i].index:
               break

        i += 1
        temp = self.chain[i-SHARD_SIZE:i]
        del self.chain[i-SHARD_SIZE:i]
        return temp

    def remove_multiple_shards(self, shard_list, SHARD_SIZE):
        temp = []

        for shard in shard_list:
            # need to remove minus sign
            temp.extend(self.remove_shard(-shard, SHARD_SIZE))
        return temp