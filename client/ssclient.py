#
import requests
import json
import time
from time import sleep
import math

Orderer = "http://52.150.10.126:5000/"
NODE = ["http://52.255.188.66:5000/", "http://52.152.228.253:5000/", "http://104.211.54.236:5000/", "http://13.68.75.6:5000/"]

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
    data = {'ts' : ts,
            'sender': sender,
            'recipient': recipient,
            'amount': amount}

    response = requests.post(new_tx_address, json=data, headers={'Content-type': 'application/json'})
    if response.status_code == 201:
        print(response.content)

def initialize(addr, overlap):
    url = f"{addr}/setoverlap"
    data = {"overlap":overlap}
    response = requests.post(url,json=data, headers={"Content-Type":'application/json'})
    if response.status_code == 200:
        print(response.content)
        
def print_worldstate(addr):
    print(f"{addr}/printworldstate")
    response = requests.get(f"{addr}/printworldstate")
    print(response.content)


def register_to_anchor(anchor, node, orderer):
    data = {'node_address': anchor,
            'orderer': orderer}
    register_address = f'{node}/register_with'
    print(register_address)
    response = requests.post(register_address, json=data, headers={"Content-Type": 'application/json'})
    if response.status_code ==200:
        print(json.loads(response.content))
    else:
        print(response.status_code)


def querybalance(key,n):
    file = open("query_latency",'a')
    url = "{}/query".format(NODE[0])
    data = {"key":key}
    start = time.time()
    response = requests.post(url,json=data, headers={"Content-Type":'application/json'})
    end = time.time()
    elapsed = end-start
    file.write(f'{n} {elapsed}\n')
    file.close()
    if response.status_code == 200:
        print(response.content)

def wholeshardquery(key, n):
    file = open("query_latency",'a')
    url = "{}/wholeshardquery".format(NODE[0])
    data = {"sender":key}
    start = time.time()
    response = requests.post(url,json=data, headers={"Content-Type":'application/json'})
    end = time.time()
    elapsed = end-start
    file.write(f'{n} {elapsed}\n')
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

def shutdown(addr):
    url = f"{addr}/shutdown"
    response = requests.get(url)
    print(response.content)

def peerlist(node):
    data = {'dat': 200}
    address = f'{node}/printpeer'
    response = requests.get(address)
    print(response.content)
    
def latency(node):
    data = {'dat': 200}
    address = f'{node}/latency'
    response = requests.get(address)
    print((800.0 * 1000)/float(response.content))




for i in range(4):
    register_to_anchor(NODE[0],NODE[i], Orderer)

for i in range(800):
    if i%4 == 0:
        new_transaction(NODE[0],'C','D',5)
    if i%4 == 1:
        new_transaction(NODE[1],'A','B',5)
    if i%4 == 2:
        new_transaction(NODE[2],'B','C',5)
    if i%4 == 3:
        new_transaction(NODE[3],'D','A',5)

sleep(5)
for i in range(4):
    printchain(NODE[i])

latency(NODE[0])