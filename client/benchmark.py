# To add a new cell, type '# %%'
# To add a new markdown cell, type '# %% [markdown]'
# %%
#
import requests
import json
import time
from time import sleep
import math

CONNECTED_NODE_ADDRESS = "http://192.168.0."
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


def register_to_anchor(anchor, node):
    data = {'node_address': anchor}
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

    


# %%
#
for i in range(4):
   new_transaction('http://192.168.43.96:5000','A','B',5)

getsize('http://192.168.43.96:5000')


# %%
print_tracker(5000)
print_tracker(5001)
print_tracker(5002)
print_tracker(5003)


# %%
printchain(5000)
printchain(5001)
printchain(5002)
printchain(5003)


# %%
#
print_worldstate(5000)
print_worldstate(5001)
print_worldstate(5002)
print_worldstate(5003)


# %%
#benchmark chain size estimation
NODE.clear()
readPeerList()
peer = NODE
m = len(peer)+1
for n in range(1,m):
    for i in range(8):
        new_transaction("http://192.168.0.100:5000", 'A','B',1)

    for p in peer:
        if p != "http://192.168.0.100:5000":
            register_to_anchor("http://192.168.0.100:5000",p)

    sleep(5)
    shardinit("http://192.168.0.100:5000")
    sleep(5)
    for p in peer: 
        getsize(p)
        sleep(2)

    
    for p in peer:
        initialize(p,n+1)
    sleep(1)


# %%
peer=list(range(5000,5015))
m = len(peer)+1

for n in range(1,m):
    for i in range(400):
        new_transaction(5000,'A','B',1)

    for p in peer:
        if p != 5000:
            register_to_anchor(5000,p)
            
    shardinit('http://192.168.43.96:5000')
    sleep(2)
    
    for k in range(10):
        wholeshardquery('A',n)
    
    for p in peer:
        initialize(p,n+1)
    sleep(1)
    print("value of n: ",n)


# %%
for i in range(100):
    new_transaction(5000,'A','B',1)

    for p in peer:
        if p != 5000:
            register_to_anchor(5000,p)
            
    shardinit('http://192.168.43.96:5000')
    sleep(2)
    
    for k in range(10):
        wholeshardquery('A',n)
    


