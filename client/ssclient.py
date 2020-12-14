#
import requests
import json
import time
from time import sleep
import math

CONNECTED_NODE_ADDRESS = "http://192.168.0."
Orderer = "http://40.76.87.243:5000/"
NODE = list()

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
    print(response.content)





register_to_anchor('http://40.121.35.50:5000','http://40.121.35.50:5000', Orderer)
register_to_anchor('http://40.121.35.50:5000','http://40.76.69.71:5000', Orderer)
register_to_anchor('http://40.121.35.50:5000','http://40.76.70.75:5000', Orderer)
register_to_anchor('http://40.121.35.50:5000','http://40.79.255.70:5000', Orderer)

for i in range(800):
    if i%4 == 0:
        new_transaction('http://40.121.35.50:5000','C','D',5)
    if i%4 == 1:
        new_transaction('http://40.76.69.71:5000','A','B',5)
    if i%4 == 2:
        new_transaction('http://40.76.70.75:5000','B','C',5)
    if i%4 == 3:
        new_transaction('http://40.79.255.70:5000','D','A',5)


shardinit("http://40.121.35.50:5000")
sleep(5)

latency("http://40.121.35.50:5000")