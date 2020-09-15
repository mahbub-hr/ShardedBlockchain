# To add a new cell, type '# %%'
# To add a new markdown cell, type '# %% [markdown]'
# %%
#
import requests
import json
import time
from time import sleep
import math
import os
import random


CONNECTED_NODE_ADDRESS = "http://192.168.0."
peer = list()
account = list()
anchor = 0
def readConfig():
    global peer
    global account 
    with open('config.json','r') as file:
        config = json.load(file)
    peer = config["peers"]
    account = config["accounts"]
    print(peer)
    print(account)
    


def new_transaction(addr, sender, recipient, amount):
    new_tx_address = "{}/transactions/new".format(addr)
    ts = time.time()
    data = {'ts' : ts,
            'sender': sender,
            'recipient': recipient,
            'amount': amount}

    response = requests.post(new_tx_address, json=data, headers={'Content-type': 'application/json'})
    if response.status_code == 201:
        return response.content

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


def querybalance(file, k, m, n):
    
    elapsed = 0.0
    #node = random.randint(0,3)
    node =0
    key = account[random.randint(0,len(account)-1)]
    url = f"{peer[node]}/query"
    data = {"key":key}
    start = time.time()
    response = requests.post(url,json=data, headers={"Content-Type":'application/json'})
    end = time.time()
    elapsed = end-start

    file.write(f'{k}, {m}, {n}, {round(elapsed,5)}\n')
   
    if response.status_code == 200:
        print(response.content)

def wholeshardquery(file, k, m, n):
    
    elapsed = 0.0
    avg_query=0.0
    #for i in range(0,3):
    node = 0#random.randint(0,3)
    #key = account[random.randint(0,len(account)-1)]
    key = "A"

    url = f"{peer[node]}/wholeshardquery"
    data = {"sender":key}
    start = time.time()
    response = requests.post(url,json=data, headers={"Content-Type":'application/json'})
    end = time.time()
    elapsed = elapsed + end-start
    data = json.loads(response.content)
    print(f"{peer[node]} : {json.dumps(data['time_stats'], indent =4)}")
    time_stats = data['time_stats']
    avg_query = time_stats['total']
    
    file.write(f'{k}, {m}, {n}, {round(elapsed,5)}, {round(avg_query,5)}\n')
    
    return

def shardinit(addr):
    response=requests.get(addr+"/shardinit")
    return response

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
    
def getsize(addr, m, k):

    url = f'{addr}/getsize'
    response= requests.get(url)
    print(response.content)
    with open('size.txt','a') as f:
        f.write(f'{k},{m},{json.loads(response.content)}')
    return


# %%
#benchmark chain size estimation
def chain_size_estimate():
    number_of_node = len(peer)+1
    k = 100
    while k <=300:
        for m in range(4, number_of_node):
            for n in range(1,m+1):

                for p in range(0,m):
                    initialize(peer[p],n)

                for i in range(k):
                    rand_account = random.sample(range(0,3),2)
                    balance = random.randint(0,1000)
                    new_transaction(peer[anchor], account[rand_account[0]],account[rand_account[1]],balance)
               
                for p in range(1,m):
                    if peer[p] != peer[anchor]:
                        register_to_anchor(peer[anchor],peer[p])
                
                shardinit(peer[anchor])
                
                for p in range(0,m): 
                    getsize(peer[p], m, k)
        
        k= k+50

#%%
def latency_estimate():
    number_of_node = len(peer)+1
    k = 100

    history_query = open("history_query_latency.txt",mode='a',buffering=1)
    state_query = open("state_query_latency.txt",mode='a',buffering=1)

    while k <=300:
        for m in range(4, number_of_node):
            for n in range(1,m+1):

                for p in range(0,m):
                    initialize(peer[p],n)

                for i in range(k):
                    balance = random.randint(0,1000)
                    new_transaction(peer[anchor], 'A',"B",balance)
                
                for p in range(1,m):
                    if peer[p] != peer[anchor]:
                        register_to_anchor(peer[anchor],peer[p])
                
                shardinit(peer[anchor])
                
                wholeshardquery(history_query,k, m, n)
                querybalance(state_query,k, m, n)
        
        k= k+50   

    history_query.close()
    state_query.close()

def throughput_estimate():
    number_of_node = len(peer)+1
    k = 100000
    throughput = open("throughput.txt", mode='a',buffering=1) 

    
    for m in range(4, number_of_node):
        for n in range(1,m+1):
            if m == 10 or (m<10 and n == 4):
                for p in range(0,m):
                    initialize(peer[p],n)

                total_valid = 0
                start = time.time()
                for i in range(k):
                    rand_account = random.sample(range(0,3),2)
                    balance = random.randint(0,10000)
                    response = new_transaction(peer[anchor], account[rand_account[0]],account[rand_account[1]],balance)
                    if response:
                        #print(response)
                        response_log = json.loads(response)
                        update_log = response_log[0]
                        total_valid += len(update_log['valid'])

                shardinit(peer[0])
                for p in range(1,m):
                    if peer[p] != peer[anchor]:
                        register_to_anchor(peer[anchor],peer[p])

                end = time.time()
                
                throughput.write(f"{k}, {m}, {n}, {total_valid}, {round(end-start,5)}\n")
        
        

    throughput.write("...........Finished ........\n")
    throughput.close()

#
readConfig()
#latency_estimate()
throughput_estimate()
print("benchmarking finished")
