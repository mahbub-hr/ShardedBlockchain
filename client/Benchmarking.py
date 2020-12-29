#
import requests
import json
import time
from time import sleep
import math
import random

from base64 import (
    b64encode,
    b64decode,
)

from Crypto.Hash import SHA256
from Crypto.Signature import PKCS1_v1_5
from Crypto.PublicKey import RSA


import struct
chain_info_wrt_n = []
chain_info_wrt_m = []
Orderer = "http://52.150.10.126:5000/"
MSP = "http://192.168.0.102:5001/"
NODE = ["http://52.255.188.66:5000/", "http://52.152.228.253:5000/", "http://104.211.54.236:5000/", "http://13.68.75.6:5000/"]

test = "http://192.168.0.102:5000/"

def readPeerList(): 
    with open('peer_list.txt','r') as file:
        for f in file:
            str = f.split('\n')
            str= str[0]
            NODE.append(str)
    print(NODE)


def new_transaction(addr, sender, recipient, amount):
    new_tx_address = "{}/transactions/new".format(addr)
    ts = time.time()
    
    msg = sender + recipient + str(amount)
    private_key = False
    filename = sender + "_key.pem"
    with open (filename, "r") as myfile:
        private_key = RSA.importKey(myfile.read())

    # Load private key and sign message
    signer = PKCS1_v1_5.new(private_key)
    digest = SHA256.new()
    digest.update(msg.encode("utf-8"))
    
    
    sig = signer.sign(digest)
    bytes_length = len(sig)
    signature = int.from_bytes(sig, byteorder="big")
    #print(testResult)
    
    #print("type sig -----------", type(sig))
    

    data = {'ts' : ts,
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
            'sig': signature,
            'len': bytes_length}

    response = requests.post(new_tx_address, json=data, headers={'Content-type': 'application/json'})
    if response.status_code == 201:
        print(response.content)

def initialize(addr, overlap):
    url = f"{addr}/setoverlap"
    data = {"overlap":overlap}
    response = requests.post(url,json=data, headers={"Content-Type":'application/json'})
    if response.status_code == 200:
        print(response.content)
        
def init_node(addr):
    url = f"{addr}/init_node"
    response = requests.get(url)
    if response.status_code == 200:
        print(response.content)


def init_network(overlap):
    global NODE, Orderer, MSP
    for peer in NODE:
        initialize(peer, overlap)
    init_node(Orderer)
    init_node(MSP)
     

def print_worldstate(addr):
    print(f"{addr}/printworldstate")
    response = requests.get(f"{addr}/printworldstate")
    print(response.content)


def register_to_anchor(anchor, node, orderer, msp):
    data = {'node_address': anchor,
            'orderer': orderer,
            'msp': msp}
    register_address = f'{node}/register_with'
    print(register_address)
    response = requests.post(register_address, json=data, headers={"Content-Type": 'application/json'})
    if response.status_code ==200:
        print(json.loads(response.content))
    else:
        print(response.status_code)


def querybalance(filename, key, n, k):
    file = open(filename,'a')
    url = "{}/query".format(NODE[0])
    data = {"key":key}
    start = time.time()
    response = requests.post(url,json=data, headers={"Content-Type":'application/json'})
    end = time.time()
    elapsed = end-start
    file.write(f'{k},{n},{elapsed}\n')
    file.close()
    #if response.status_code == 200:
        #print(response.content)

def wholeshardquery(filename, key, n, k):
    file = open(filename,'a')
    url = "{}/wholeshardquery".format(NODE[0])
    data = {"sender":key}
    start = time.time()
    response = requests.post(url,json=data, headers={"Content-Type":'application/json'})
    end = time.time()
    elapsed = end-start
    file.write(f'{k},{n},{elapsed}\n')
    file.close()
    #data = json.loads(response.content)
    #print(json.dumps(data, indent=4, sort_keys=True))
    return

def shardinit(addr):
    response=requests.get(addr+"/shardinit")
    print(response.content)

def printchain(addr):
    url = f"{addr}/printchain"
    response = requests.get(url)
    print(response.content)

def print_tracker(addr):
    url = f"{addr}/printtracker"
    response = requests.get(url)
    print(response.content)
    
def shardedchain(addr):
    url = f'{addr}/shardedchain/5003'
    response = requests.get(url)
    print(response.content)
    
def getsize(addr):
    url = f'{addr}/getsize'
    response= requests.get(url)
    print(response.content)
    return response.content

def shutdown(addr):
    url = f"{addr}/shutdown"
    response = requests.get(url)
    print(response.content)

def peerlist(node):
    address = f'{node}/printpeer'
    response = requests.get(address)
    print(response.content)
    
def throughput(node, no_txs):
    address = f'{node}/latency'
    response = requests.get(address)
    return (no_txs * 1000)/float(response.content)

def createclient(name, amount):
    url = f'{MSP}/sign_up'
    data = {"name":name, "amount": float(amount)}
    response = requests.post(url,json=data, headers={"Content-Type":'application/json'})
    filename = name + "_key.pem"
    key = response.content
    #print(type(key))
    #print(key)
    file1 = open(filename,"wb") 
    file1.write(key)
    file1.close()

def Clients():
    with open("initial_balance.txt",'r') as f:
        for line in f:
            key, value = line.partition(" ")[::2]
            time.sleep(1)
            createclient(key, value)    

def peer_up(no_of_NODE):
    for i in range(no_of_NODE):
        register_to_anchor(NODE[0],NODE[i], Orderer, MSP)


# n_vs_eta where m = 10 and k = 125 (n is 1 up to 10)
print("preparing n_vs_eta ----------------------(m =10, k = 125)")
for ovrlp in range(1, 11):
    print(f'n = {ovrlp} running...')
    init_network(ovrlp) # Orderer, MSP, Peer reset
    peer_up(10) # 10 peers in network now, m = 10 fixed
    Clients() # Client with keys generated

    for i in range(25000): # 25000 txs, 250 blocks, 2 blocks in single shard, k = 125
        chosen_node = random.randint(0,9)
        if i%4 == 0:
            new_transaction(NODE[chosen_node],'C','D',5)
        if i%4 == 1:
            new_transaction(NODE[chosen_node],'A','B',5)
        if i%4 == 2:
            new_transaction(NODE[chosen_node],'B','C',5)
        if i%4 == 3:
            new_transaction(NODE[chosen_node],'D','A',5)
    
    for i in range(len(NODE)):
        chain_info_wrt_n.append(getsize(NODE[i]))

n_vs_eta = open("n_vs_eta.csv", "a")
for line in chain_info_wrt_n:
    n_vs_eta.write(line)
    n_vs_eta.write("\n")
n_vs_eta.close()


# m_vs_eta where n = 4 and k = 50 (m is 4 up to 10)
print("preparing n_vs_eta ----------------------(n = 4, k = 50 )")
for no_peer in range(4, 11):
    print(f'm = {no_peer} running')
    init_network(4) # no of copies of chain is 4, n = 4 fixed
    peer_up(no_peer)
    Clients()

    for i in range(10000): # 10000 txs, 100 blocks, 2 blocks in single shard, k = 50
        chosen_node = random.randint(0, (no_peer - 1))
        if i%4 == 0:
            new_transaction(NODE[chosen_node],'C','D',5)
        if i%4 == 1:
            new_transaction(NODE[chosen_node],'A','B',5)
        if i%4 == 2:
            new_transaction(NODE[chosen_node],'B','C',5)
        if i%4 == 3:
            new_transaction(NODE[chosen_node],'D','A',5)
    
    for i in range(len(NODE)):
        chain_info_wrt_m.append(getsize(NODE[i]))

m_vs_eta = open("m_vs_eta.csv", "a")
for line in chain_info_wrt_m:
    m_vs_eta.write(line)
    m_vs_eta.write("\n")
m_vs_eta.close()


k_txs = [10000, 15000, 20000, 25000, 30000]

# state query latency vs n (n is 1 up to 10)
print("preparing state query latency vs n ----------------(m =10)")
for k in k_txs:
    for ovrlp in range(1, 11):
        init_network(ovrlp)
        peer_up(10)
        Clients()

        for i in range(k):
            chosen_node = random.randint(0, 9)
            if i%4 == 0:
                new_transaction(NODE[chosen_node],'C','D',5)
            if i%4 == 1:
                new_transaction(NODE[chosen_node],'A','B',5)
            if i%4 == 2:
                new_transaction(NODE[chosen_node],'B','C',5)
            if i%4 == 3:
                new_transaction(NODE[chosen_node],'D','A',5)

        querybalance("state_query_latency_vs_n.csv", "A", ovrlp, (k/200))


# state query latency vs m (n is 4)
print("preparing state query latency vs m ----------------(n = 4)")
for k in k_txs:
    for no_peer in range(4, 11):
        init_network(4)
        peer_up(no_peer)
        Clients()

        for i in range(k):
            chosen_node = random.randint(0, (no_peer - 1))
            if i%4 == 0:
                new_transaction(NODE[chosen_node],'C','D',5)
            if i%4 == 1:
                new_transaction(NODE[chosen_node],'A','B',5)
            if i%4 == 2:
                new_transaction(NODE[chosen_node],'B','C',5)
            if i%4 == 3:
                new_transaction(NODE[chosen_node],'D','A',5)

        querybalance("state_query_latency_vs_m.csv", "A", no_peer, (k/200))


# history query latency vs n (n is 1 up to 10)
print("preparing history query latency vs n ----------------(m =10)")
for k in k_txs:
    for ovrlp in range(1, 11):
        init_network(ovrlp)
        peer_up(10)
        Clients()

        for i in range(k):
            chosen_node = random.randint(0, 9)
            if i%4 == 0:
                new_transaction(NODE[chosen_node],'C','D',5)
            if i%4 == 1:
                new_transaction(NODE[chosen_node],'A','B',5)
            if i%4 == 2:
                new_transaction(NODE[chosen_node],'B','C',5)
            if i%4 == 3:
                new_transaction(NODE[chosen_node],'D','A',5)

        wholeshardquery("history_query_latency_vs_n.csv", "A", ovrlp, (k/200)) # k, n, history_latency format


# history query latency vs m (n is 4)
print("preparing history query latency vs m ----------------(n = 4)")
for k in k_txs:
    for no_peer in range(4, 11):
        init_network(4)
        peer_up(no_peer)
        Clients()

        for i in range(k):
            chosen_node = random.randint(0, (no_peer - 1))
            if i%4 == 0:
                new_transaction(NODE[chosen_node],'C','D',5)
            if i%4 == 1:
                new_transaction(NODE[chosen_node],'A','B',5)
            if i%4 == 2:
                new_transaction(NODE[chosen_node],'B','C',5)
            if i%4 == 3:
                new_transaction(NODE[chosen_node],'D','A',5)

        wholeshardquery("history_query_latency_vs_m.csv", "A", no_peer, (k/200)) # k, m, history_latency format


# throughput varying m and n (k = 150)
print("preparing throughput varying m and n------------------- (k = 150)")
for no_peer in range(4, 11):
    for ovrlp in range(1, 11):
        init_network(ovrlp)
        peer_up(no_peer)
        Clients()

        for i in range(30000):
            chosen_node = random.randint(0, (no_peer - 1))
            if i%4 == 0:
                new_transaction(NODE[chosen_node],'C','D',5)
            if i%4 == 1:
                new_transaction(NODE[chosen_node],'A','B',5)
            if i%4 == 2:
                new_transaction(NODE[chosen_node],'B','C',5)
            if i%4 == 3:
                new_transaction(NODE[chosen_node],'D','A',5)

        throughput_ = throughput(NODE[0], 30000)
        thpt = open("throughput.csv", "a")
        thpt.write(f'{no_peer},{ovrlp},{throughput_}\n') # m, n, throughput format
        thpt.close()
