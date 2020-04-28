import requests
import json

CONNECTED_NODE_ADDRESS = "http://127.0.0.1:"
NODE = ["http://localhost:5000", "http://localhost:5001"]

def new_transaction(port):
    addr = CONNECTED_NODE_ADDRESS+repr(port)
    print(addr)
    new_tx_address = "{}/transactions/new".format(addr)
    data = {'sender':'A',
            'recipient':'B',
            'amount': 5}

    response = requests.post(new_tx_address, json=data, headers={'Content-type': 'application/json'})
    if response.status_code == 201:
        print(json.loads(response.content))


def print_worldstate():
    response = requests.get("{}/print".format(CONNECTED_NODE_ADDRESS))


def register_to_anchor():
    data = {'node_address': 'http://localhost:5000'}
    register_address = "{}/register_with".format(NODE[1])
    response = requests.post(register_address, json=data, headers={"Content-Type": 'application/json'})
    if response.status_code ==200:
        print(json.loads(response.content))


def querybalance(key):
    url = "{}/query".format(NODE[0])
    data = {"key":key}
    response = requests.post(url,json=data, headers={"Content-Type":'application/json'})
    if response.status_code == 200:
        print(response.content)

def wholeshardquery(key):
    url = "{}/wholeshardquery".format(NODE[0])
    data = {"sender":key}
    response = requests.post(url,json=data, headers={"Content-Type":'application/json'})

    print(response.content)

def shardinit():
    response=requests.get(CONNECTED_NODE_ADDRESS+"5000/shardinit")
    print(response.content)

def printchain(port):
    url = "{}/printchain".format(CONNECTED_NODE_ADDRESS+repr(port))
    response = requests.get(url)
    print(response.content)

# for i in range(4):
#    new_transaction(5000)
#
# register_to_anchor()
# shardinit()
#
# for i in range(4):
#     new_transaction(5000)
#     new_transaction(5001)
# shardinit()
#
# printchain(5000)
# printchain(5001)
#     new_transaction(5001)

wholeshardquery('A')
