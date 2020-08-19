import requests
import json
import time
import sys
import socket 
import math
from flask import Flask, jsonify, request
app = Flask(__name__)

import blockchain


TX_PER_BLOCK = 1
LAST_INDEX = 1
SHARD_SIZE = 2
NODE_NUMBER = 1
IS_SHARDED = False
IS_ANCHOR = False
SHARDING_THRESHOLD = 10
OVERLAPPING = 1

LAST_SHARD = 0
LAST_CHAIN_SIZE = 1
x = 0
SELF_KEY = ""
PREV_HASH=""
bchain = blockchain.Blockchain()
PREV_HASH = bchain.chain[0].hash
worldstate = blockchain.Worldstate()
tracker = blockchain.ShardInfoTracker()

peers = []

def initialize():

    global  TX_PER_BLOCK, LAST_INDEX, IS_SHARDED,OVERLAPPING,LAST_SHARD,LAST_CHAIN_SIZE,x,PREV_HASH,peers
    global bchain, worldstate, tracker
    TX_PER_BLOCK = 1
    LAST_INDEX = 1
    IS_SHARDED = False
    OVERLAPPING = 1
    LAST_SHARD = 0
    LAST_CHAIN_SIZE = 1
    x = 0
    PREV_HASH = ""
    bchain = blockchain.Blockchain()
    PREV_HASH = bchain.chain[0].hash
    worldstate = blockchain.Worldstate()
    tracker = blockchain.ShardInfoTracker()
    peers = []
    peer_insert(SELF_KEY)
    
    return

@app.route("/setoverlap",methods=['POST'])
def setoverlap():
    global OVERLAPPING
    data = request.get_json()
    initialize()
    print('initialized to zero')
    OVERLAPPING = data['overlap']
    return 'setoverlap returned',200

def peer_insert(p):
    if p not in peers:
        peers.append(p)
    else:
        print(f"{p} already exists")


def peer_update(peer):
    for p in peer:
        if p not in peers:
            peers.append(p)


def get_my_key():
    if SELF_KEY == "":
        print("key is not set")
        return ""
    return SELF_KEY


@app.route('/getsize', methods=['GET'])
def getchainsize():
    f = open("size.txt", 'a')
    if SELF_KEY in tracker.node_to_shard:
        num_of_shard = len(tracker.node_to_shard[SELF_KEY])
        block_size = sys.getsizeof(bchain.chain[1])
    else:
        num_of_shard =0
        block_size = 0

    element = len(bchain.chain)-1
    f.write(f'{SELF_KEY},{OVERLAPPING},{num_of_shard},{block_size},{element},{block_size*element}\n')

    f.close()
    return 'get size function returned', 200

#act as a orderer
@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    global LAST_INDEX
    global PREV_HASH
    values = request.get_json()

    # Check that the required fields are in the POST'ed data
    required = ['ts', 'sender', 'recipient', 'amount']
    if not all(k in values for k in required):
        return 'Missing values', 400

    # Create a new Transaction
    index = bchain.new_transaction(values['ts'], values['sender'], values['recipient'], values['amount'])

    if len(bchain.current_transactions) == TX_PER_BLOCK:
        #
        block = blockchain.Block(LAST_INDEX, bchain.current_transactions, time.time(), PREV_HASH)
        block.hash = block.compute_hash()
        PREV_HASH = block.hash
        peer_broadcast("add_block", block.__dict__, [])
        LAST_INDEX += 1
        bchain.current_transactions=[]
        print('block has been broadcasted')

    return 'block has been broadcasted', 201

@app.route('/add_block', methods=['POST'])
def verify_and_add_block():
    block_data = request.get_json()
    block = blockchain.Block(block_data["index"],
                             block_data["transactions"],
                             block_data["timestamp"],
                             block_data["previous_hash"],
                             )
    block.hash = block_data['hash']
    added = bchain.add_block_on_shard(block,"")
    if not added:
        return "The block was discarded by the node", 400
    worldstate.update_with_block(block)
    return "Block added to the chain", 201

@app.route('/chain', methods=['GET'])
def full_chain():
    chain_data = []
    for block in bchain.chain:
        chain_data.append(block.__dict__)

    response = json.dumps(
        {"length": len(chain_data),
         "chain": chain_data,
         "peers": peers,
         "worldstate": worldstate.worldstate})

    return response


def unsharded_chain():
    chain_data = []
    for block in range(LAST_CHAIN_SIZE, len(bchain.chain)):
        chain_data.append(block.__dict__)
    return chain_data


def sharded_chain(node_address):
    chain_data = []
    shard = []
    tracker.printshard()
    k = min(len(tracker.node_to_shard[SELF_KEY]), len(tracker.node_to_shard), len(tracker.shard_to_node))
    print('giving ', k, ' shards')
    track = blockchain.ShardInfoTracker()
    i = 1
    while k > 0:
        #change here if we want to remove shard from node that have maximum shard
        node = tracker.remove_shard(i)
        tracker.insert(node_address, i)
        track.insert(node, -i)
        k -= 1
        i += 1
    track.print()
    tracker.print()
    unsharded = unsharded_chain()

    print(node_address)

    data = {
            'track': track.__dict__,
            'tracker':tracker.__dict__,
            'node_address' : node_address
    }
    if SELF_KEY in track.node_to_shard:
        shards = bchain.remove_multiple_shards(track.node_to_shard[SELF_KEY], SHARD_SIZE)
        send_shard_to(shards,node_address)

    resp = peer_broadcast('sendnewnodeinfo', data, {SELF_KEY, node_address})
    print(resp)

    response = {
        'worldstate': worldstate.worldstate,
        'tracker': tracker.__dict__,
        'peers': peers,
        'chain': unsharded
    }
    return json.dumps(response)


# endpoint to add new peers to the network.
@app.route('/register_node', methods=['POST'])
def register_new_peers():
    node_address = request.get_json()["node_address"]
    if not node_address:
        return "Invalid data", 400

    # Add the node to the peer list
    peer_insert(node_address)
    if IS_SHARDED:
        return sharded_chain(node_address)
    else:
        return full_chain()


@app.route('/register_with', methods=['POST'])
def register_with_existing_node():
    node_address = request.get_json()["node_address"]
    if not node_address:
        return "Invalid data", 400

    data = {"node_address": request.host_url}
    headers = {'Content-Type': "application/json"}

    # Make a request to register with remote node and obtain information
    response = requests.post(node_address + "/register_node",
                             json=data, headers=headers)

    if response.status_code == 200:
        global bchain
        #this is in master
        global peers
        global worldstate
        global LAST_INDEX
        # update chain and the peers
        json_data = response.json()
        chain_dump = json_data['chain']
        if not IS_SHARDED:
            bchain = create_chain_from_dump(chain_dump)
        if IS_SHARDED:
            t = json_data['tracker']
            tracker.node_to_shard = t['node_to_shard']
            tracker.shard_to_node = t['shard_to_node']
        # need to remove if there is a seperate orderer
        LAST_INDEX = bchain.chain[-1].index + 1
        peer_update(json_data['peers'])
        print(peers)
        worldstate.worldstate = json_data['worldstate']
        return jsonify("Registration successful"), 200
    else:
        # if something goes wrong, pass it on to the API response
        return response.content, response.status_code


@app.route('/sendnewnodeinfo', methods=['POST'])
def get_new_node_info():
    global tracker
    response = request.get_json()
    track = response['track']
    tracker_ = response['tracker']
    node_address = response['node_address']
    tracker.node_to_shard=tracker_['node_to_shard']
    tracker.shard_to_node=tracker_['shard_to_node']
    peer_insert(node_address)

    node_to_shard = track['node_to_shard']
    if SELF_KEY not in node_to_shard:
        return "get new node info returned wihtout sending any shard"
    shards = bchain.remove_multiple_shards(node_to_shard[SELF_KEY], SHARD_SIZE)
    print(send_shard_to(shards, node_address))
    return 'get new node info returned', 200

def send_shard_to(shards, node_address):
    chain_dump =[]
    for b in shards:
        chain_dump.append(b.__dict__)
    data ={
            'shard':chain_dump
    }
    response = requests.post(node_address+'sendshard', json=data, headers={'Content-Type': "application/json"})
    if response.status_code == 200:
        print(response.content)
    return 'send_shard returned'

@app.route('/sendshard',methods=["POST"])
def recv_shard():
    global IS_SHARDED
    global bchain
    IS_SHARDED = True
    print('recv shard entered')
    data = request.get_json()
    shard = data['shard']
    generated_shard=create_chain_from_dump(shard)
    generated_shard.chain.pop(0)
    bchain.chain.extend(generated_shard.chain)
    return 'recv shard returned',200

def create_chain_from_dump(chain_dump):
    generated_blockchain = blockchain.Blockchain()
    # generated_blockchain.create_genesis_block()
    for idx, block_data in enumerate(chain_dump):
        if idx == 0 and not IS_SHARDED:
            continue  # skip genesis block
        block = blockchain.Block(block_data["index"],
                                 block_data["transactions"],
                                 block_data["timestamp"],
                                 block_data["previous_hash"])
        block.hash = block_data['hash']
        if IS_SHARDED:
            #integraty check is not performed

            added= generated_blockchain.add_block_on_shard(block,'')
        else:
            added = generated_blockchain.add_block(block)

        if not added:
            raise Exception("The chain dump is tampered!!")
    return generated_blockchain


@app.route("/shardinit", methods=['GET'])
def init_shard():
    global LAST_SHARD
    print('chain len: ', len(bchain.chain))
    global peers
    global OVERLAPPING
    global IS_SHARDED

    track = blockchain.ShardInfoTracker()

    IS_SHARDED = True
    print(peers)
    num_of_shard = (len(bchain.chain) - LAST_CHAIN_SIZE) / SHARD_SIZE
    print('num of shard: ', num_of_shard)
    i = 1
    # make this global to turn around lapping
    global x
    overlapping = OVERLAPPING
    while i <= num_of_shard:
        temp = LAST_SHARD + i
        track.insert(peers[x], temp)
        overlapping -= 1
        x += 1

        if x >= len(peers):
            x = 0

        if overlapping <= 0:
            i += 1
            overlapping = OVERLAPPING

        # can be removed
        if i > num_of_shard:
            LAST_SHARD = temp

            break;

    tracker.insert_dict(track.node_to_shard)
    tracker.print()
    apply_sharding(track.node_to_shard)
    send_info(track)
    return 'init shard returned'


def apply_sharding(sharding_update):
    global SHARD_SIZE
    global LAST_CHAIN_SIZE
    shards = sharding_update[SELF_KEY]
    temp = bchain.chain[:LAST_CHAIN_SIZE]
    for i in shards:
        end = SHARD_SIZE * i

        end_index = LAST_CHAIN_SIZE + (end - bchain.chain[LAST_CHAIN_SIZE].index) + 1
        start_index = end_index - SHARD_SIZE
        temp.extend(bchain.chain[start_index:end_index])
    bchain.chain = temp
    LAST_CHAIN_SIZE = len(bchain.chain)
    return "sharding done, ok"


def send_info(track):
    for peer in peers:
        if peer != SELF_KEY:
            url = f"{peer}sendshardinfo"
            headers = {'Content-Type': "application/json"}
            response = requests.post(url,
                                     json=(track.__dict__),
                                     headers=headers)
            if response.status_code == 200:
                print(peer, ": ", response.content)
    return


@app.route("/sendshardinfo", methods=['POST'])
def shard_info():
    response = request.get_json()
    node_to_shard = response['node_to_shard']
    tracker.insert_dict(node_to_shard)
    tracker.print()
    global IS_SHARDED
    IS_SHARDED = True
    apply_sharding(node_to_shard)
    return "successfully got it", 200

def tx_in_shard_by_sender(sender, shard):
    tx_list = []
    for block in bchain.chain:
        if math.ceil(block.index / SHARD_SIZE) == int(shard):
            for tx in block.transactions:
                if tx['sender'] == sender:
                    tx['b_idx'] = block.index
                    tx_list.append(tx)
    return tx_list

@app.route('/txbysender', methods=['POST'])
def txbysender():
    data = request.get_json()
    sender = data['sender']
    shard = data['shard']

    tx_list = tx_in_shard_by_sender(sender, shard)
    return json.dumps({'tx': tx_list})


@app.route("/wholeshardquery", methods=['POST'])
def wholeshardquery():
    data = request.get_json()
    sender = data['sender']
    tx = []
    for shard in tracker.shard_to_node:
        peer = tracker.shard_to_node[shard][0]
        if (peer != SELF_KEY) and tracker.node_to_shard[peer]:
            data['shard'] = shard
            response = requests.post(peer + "txbysender", json=data, headers={"Content-Type": 'application/json'})
            tx.extend(response.json()['tx'])
        else:
            tx.extend(tx_in_shard_by_sender(sender, shard))

    return json.dumps(tx),200


@app.route("/query", methods=['POST'])
def query():
    data = request.get_json()
    return repr(worldstate.get(data['key'])), 200


@app.route("/printworldstate", methods=['GET'])
def printWorldstate():
    worldstate.print()
    return "print worldstate"

@app.route('/printtracker',methods=['GET'])
def print_tracker():
    tracker.print()
    return 'print tracker'

@app.route("/printchain", methods=['GET'])
def printchain():
    for block in bchain.chain:
        print(json.dumps(block.__dict__, indent=4))

    return "print chain"

@app.route("/printpeer", methods=["GET"])
def printpeer():
    for p in peers:
        print(p)

    return "peer list is printed"
    
def peer_broadcast(url, data, exclude, header={"Content-Type": 'application/json'}):
    for peer in peers:
        if peer not in exclude:
            response = requests.post(peer+url, json = data, headers=header)
            print(response.content)

    return "peer broadcast returned"

@app.route("/", methods=['GET'])
def home():
    print("tested ")
    return "<html>\
                <body><h1> Welcome to Homepage</h1></body>\
            </html>"

def get_host_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        print("can not get host name and ip address")

if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on')
    parser.add_argument('-a', '--anchor', default=False, type=bool, help='Is this node anchor')
    parser.add_argument('-n', '--node', default=1, type=int, help='this node number')
    args = parser.parse_args()
    port = args.port
    NODE_NUMBER = port
    # NODE_NUMBER = args.node
    IS_ANCHOR = args.anchor
    SELF_KEY = "http://localhost:" + repr(NODE_NUMBER) + "/"
    host_ip =  get_host_ip()
    print(host_ip)
    peer_insert(get_my_key())
    app.run(host=host_ip, port=port, debug=True)
