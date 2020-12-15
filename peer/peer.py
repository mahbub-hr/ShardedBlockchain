import requests
import json
import time
import sys
import socket 
import math
import gc
import psutil
import os
from flask import Flask, jsonify, request
import threading
import logging
app = Flask(__name__)

import blockchain


logging.basicConfig(level=logging.INFO, format='[%(asctime)s] - %(message)s', datefmt='%H:%M:%S')

adding_block = False

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
Orderer = None

peers = []
temp_update_log = {}

# pBFT global variables
added_blocks = [] #entries are int (block index)
yet_to_be_added_blocks = [] #list of metadata from peers
new_block_found_from_peers = []
new_block_found_from_orderer = [] #entries are int (block index)
waiting_block = []
fault_tolerance = 0

first_tx = False
first_tx_time = None
last_block_add_time = time.time()

def initialize():

    global  TX_PER_BLOCK, LAST_INDEX, IS_SHARDED,OVERLAPPING,LAST_SHARD,LAST_CHAIN_SIZE,x,PREV_HASH,peers
    global bchain, worldstate, tracker
    
    global added_blocks #entries are int (block index)
    global yet_to_be_added_blocks #list of metadata from peers
    global new_block_found_from_peers
    global new_block_found_from_orderer #entries are int (block index)
    global waiting_block
    global fault_tolerance

    global first_tx
    global first_tx_time
    global last_block_add_time
    
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
    added_blocks = [] #entries are int (block index)
    yet_to_be_added_blocks = [] #list of metadata from peers
    new_block_found_from_peers = []
    new_block_found_from_orderer = [] #entries are int (block index)
    waiting_block = []
    fault_tolerance = 0
    first_tx = False
    first_tx_time = None
    last_block_add_time = time.time()
    #peers = []
    #peer_insert(SELF_KEY)
    
    return

@app.route("/setoverlap",methods=['POST'])
def setoverlap():
    global OVERLAPPING
    data = request.get_json()
    initialize()
    logging.info(f'initialized to zero')
    OVERLAPPING = data['overlap']
    return 'setoverlap returned',200

def peer_insert(p):
    global fault_tolerance
    if p not in peers:
        peers.append(p)
    else:
        logging.info(f"{p} already exists")
    
    fault_tolerance = math.floor( (len(peers) - 1) /3 )


def peer_update(peer):
    global fault_tolerance
    for p in peer:
        if p not in peers:
            peers.append(p)

    fault_tolerance = math.floor( (len(peers) - 1) /3 )


def get_my_key():
    if SELF_KEY == "":
        logging.info(f"key is not set")
        return ""
    return SELF_KEY

@app.route('/ps_util', methods=['GET'])
def memory_usage_psutil():
    # return the memory usage in MB
    
    process = psutil.Process(os.getpid())
    mem = (process.memory_info()[0])/float(2**20) 
    return mem

def get_obj_size(obj):
    marked = {id(obj)}
    obj_q = [obj]
    sz = 0

    while obj_q:
        sz += sum(map(sys.getsizeof, obj_q))

        # Lookup all the object referred to by the object in obj_q.
        # See: https://docs.python.org/3.7/library/gc.html#gc.get_referents
        all_refr = ((id(o), o) for o in gc.get_referents(*obj_q))

        # Filter object that are already marked.
        # Using dict notation will prevent repeated objects.
        new_refr = {o_id: o for o_id, o in all_refr if o_id not in marked and not isinstance(o, type)}

        # The new obj_q will be the ones that were not marked,
        # and we will update marked with their ids so we will
        # not traverse them again.
        obj_q = new_refr.values()
        marked.update(new_refr.keys())

    return sz
    

@app.route('/latency', methods=['GET'])
def latency():
    global first_tx_time, last_block_add_time
    return (f"{last_block_add_time - first_tx_time}"), 200


@app.route('/getsize', methods=['GET'])
def getchainsize():
    
    block_size = sys.getsizeof(bchain.chain[1])
    if SELF_KEY in tracker.node_to_shard:
        num_of_shard = len(tracker.node_to_shard[SELF_KEY])
        
    else:
        num_of_shard =0
       

    element = len(bchain.chain)
    
    return json.dumps(f'{SELF_KEY},{OVERLAPPING},{num_of_shard},{block_size},{element},{get_obj_size(bchain)}, {memory_usage_psutil()}\n'), 200


def send_transaction_to_orderer(tx, Orderer):
    response = requests.post(Orderer + '/getTransaction', json = tx, headers={"Content-Type": 'application/json'})
    logging.info(f"Transaction sent to Orderer, Orderer response - {response.content}")

#act as a orderer
@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    global LAST_INDEX
    global PREV_HASH
    global temp_update_log
    global Orderer
    global first_tx
    global first_tx_time
    temp_update_log = {}
    values = request.get_json()

    # Check that the required fields are in the POST'ed data
    required = ['ts', 'sender', 'recipient', 'amount']
    if not all(k in values for k in required):
        return 'Missing values', 400

    if first_tx == False:
        first_tx = True
        first_tx_time = time.time()


    t = threading.Thread(target=send_transaction_to_orderer, args=(values, Orderer, ))
    t.start()

    return "Transaction sent to Orderer", 201


def verify_and_add_block(block_index):
    global adding_block
    adding_block = True
    global waiting_block
    global LAST_INDEX
    global added_blocks
    global last_block_add_time
    """block_data = request.get_json()
    block = blockchain.Block(block_data["index"],
                             block_data["transactions"],
                             block_data["timestamp"],
                             block_data["previous_hash"],
                             )
    block.hash = block_data['hash']"""
    block = blockchain.Block
    #print("len of waiting block - ", len(waiting_block))
    for i in range(len(waiting_block)):
        if int(waiting_block[i].index) == int(block_index):
            #print("\n\n\n\nInside, i = ",i, "\n\n")
            #print("Printing block txs ----", waiting_block[i].transactions)   
            #print("\n\n\n\n")
            block = blockchain.Block(
                waiting_block[i].index,
                waiting_block[i].transactions,
                waiting_block[i].timestamp,
                waiting_block[i].previous_hash,
            )
            block.hash = waiting_block[i].hash
            waiting_block.remove(waiting_block[i])
    
    added = bchain.add_block_on_shard(block,"")
    LAST_INDEX += 1
    if not added:
        return "The block was discarded by the node", 400

    #print("Printing block ----", block.transactions)
    
    added_blocks.append(int(block_index))
    update_log = worldstate.update_with_block(block)
    last_block_add_time = time.time()

    return update_log, 201


@app.route('/add_block', methods=['POST'])
def pBFT_prepare():
    global waiting_block
    global temp_update_log
    global adding_block
    block_data = request.get_json()
    block = blockchain.Block(block_data["index"],
                             block_data["transactions"],
                             block_data["timestamp"],
                             block_data["previous_hash"],
                             )
    block.hash = block_data['hash']
    hash_data = {"index": block_data["index"], "hash_received_by_sender": block.hash, "sender": SELF_KEY}
    peer_broadcast("consensus", hash_data, {SELF_KEY})
    
    
    newentry = [block_data["index"], SELF_KEY, block.hash]
    yet_to_be_added_blocks.append(newentry)
    new_block_found_from_orderer.append(int(block_data["index"]))
    required_replies = (2*fault_tolerance) + 1
    reply_found = 0
    #print(block_data)
    waiting_block.append(block)
    
    for correct_reply in yet_to_be_added_blocks:
        if int(correct_reply[0]) == int(block_data["index"]):
            if correct_reply[2] == block.hash:
                reply_found = reply_found + 1
    
    if reply_found >= required_replies:
        #print("Block added stage 1")
        if not adding_block:
            temp_update_log = verify_and_add_block(int(block_data["index"]))
            adding_block = False

    return 'block hash has been broadcasted for pBFT', 201


@app.route('/consensus', methods=['POST'])
def pBFT_commit():
    global fault_tolerance
    global added_blocks
    global adding_block
    global yet_to_be_added_blocks
    global new_block_found_from_orderer
    global temp_update_log
    received_data = request.get_json()
    block_index = received_data["index"]
    sender = received_data["sender"]
    hash_computed_by_sender = received_data["hash_received_by_sender"]
    

    required_replies = (2*fault_tolerance) + 1
    reply_found = 0
    my_hash = ""

    if int(block_index) not in added_blocks:
        #print("inside 1st if")
        if int(block_index) in new_block_found_from_orderer:
            #print("inside 2nd if")
            newentry = [block_index, sender, hash_computed_by_sender]
            yet_to_be_added_blocks.append(newentry)
            
            for correct_reply in yet_to_be_added_blocks:
                if int(correct_reply[0]) == int(block_index):
                    if correct_reply[1] == SELF_KEY:
                        my_hash = correct_reply[2]
                        break
            for correct_reply in yet_to_be_added_blocks:
                if int(correct_reply[0]) == int(block_index):
                    if correct_reply[2] == my_hash:
                        reply_found = reply_found + 1
            #new_block_found_from_peers.append(int(block_index))
        else:
            newentry = [int(block_index), sender, hash_computed_by_sender]
            yet_to_be_added_blocks.append(newentry) 
            return "reply received from peers but not yet from orderer, reply recorded", 200

    if reply_found >= required_replies:
        #print("Block added stage 2")
        if not adding_block:
            temp_update_log = verify_and_add_block(int(block_index))
            adding_block = False

    
    reply = "Reply received from " + SELF_KEY
    return reply, 201

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
    logging.info(f'giving {k} shards')
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

    logging.info(f"node_address - {node_address}")

    data = {
            'track': track.__dict__,
            'tracker':tracker.__dict__,
            'node_address' : node_address
    }
    if SELF_KEY in track.node_to_shard:
        shards = bchain.remove_multiple_shards(track.node_to_shard[SELF_KEY], SHARD_SIZE)
        send_shard_to(shards,node_address)

    resp = peer_broadcast('sendnewnodeinfo', data, {SELF_KEY, node_address})
    logging.info(f"resp - {resp}")

    response = {
        'worldstate': worldstate.worldstate,
        'tracker': tracker.__dict__,
        'peers': peers,
        'chain': unsharded
    }
    return json.dumps(response)

@app.route('/printpeer')
def showpeer():
    global peers
    logging.info(f"peers - {peers}")
    return 'Printed', 200

@app.route('/peer_update_on_registration', methods=['POST'])
def reg_update():
    updated_peerlist = request.get_json()["updated_peerlist"]
    peer_update(updated_peerlist)
    return "New Peer emerged, list updated", 200

# endpoint to add new peers to the network.
@app.route('/register_node', methods=['POST'])
def register_new_peers():
    node_address = request.get_json()["node_address"]
    data = {
        'updated_peerlist': peers
    }
    if not node_address:
        return "Invalid data", 400

    # Add the node to the peer list
    peer_insert(node_address)
    peer_broadcast('peer_update_on_registration', data, {SELF_KEY, node_address})
    if IS_SHARDED:
        return sharded_chain(node_address)
    else:
        return full_chain()


'''@app.route('/peerlist', methods=['POST'])
def update_peerlist():
    global peers
    global SELF_KEY
    data = request.get_json()
    orderer_peers = data['peers']
    peers = orderer_peers
    #logging.info(f"Peerlist Updated, peerlist - {peers}")
    print("Peerlist Updated, peerlist ", peers)
    return "Peerlist Updated for" + str(SELF_KEY)'''


def register_to_orderer(Orderer, data, headers):
    response = requests.post(Orderer + "/register",
                             json=data, headers=headers)
    if response.status_code == 200:
        logging.info(f"Registered to Orderer : Orderer response - {response.content}")


@app.route('/register_with', methods=['POST'])
def register_with_existing_node():
    global Orderer
    global IS_ANCHOR
    node_address = request.get_json()["node_address"]
    Orderer = request.get_json()["orderer"]
    if not node_address:
        return "Invalid data", 400

    data = {"node_address": request.host_url}
    headers = {'Content-Type': "application/json"}

    # Make a request to register with remote node and obtain information
    t = threading.Thread(target = register_to_orderer, args = (Orderer, data, headers, ))
    t.start()
    if IS_ANCHOR:
        return jsonify("Anchor registered to orderer"), 200
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
        #print(peers)
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
    logging.info(f"{send_shard_to(shards, node_address)}")
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
        logging.info(f"response - {response.content}")
    return 'send_shard returned'

@app.route('/sendshard',methods=["POST"])
def recv_shard():
    global IS_SHARDED
    global bchain
    IS_SHARDED = True
    logging.info(f'recv shard entered')
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
    logging.info(f'chain len: {len(bchain.chain)}')
    global peers
    global OVERLAPPING
    global IS_SHARDED

    track = blockchain.ShardInfoTracker()

    IS_SHARDED = True
    logging.info(f"peers - {peers}")
    num_of_shard = (len(bchain.chain) - LAST_CHAIN_SIZE) / SHARD_SIZE
    logging.info(f'num of shard: {num_of_shard}')
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
                logging.info(f"{peer} : {response.content}")
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
    time_stats = {}
    start = time.time()

    for shard in tracker.shard_to_node:
        peer = tracker.shard_to_node[shard][0]

        if (peer != SELF_KEY) and tracker.node_to_shard[peer]:
            data['shard'] = shard
            s = time.time()
            response = requests.post(peer + "txbysender", json=data, headers={"Content-Type": 'application/json'})
            e = time.time()
            tx.extend(response.json()['tx'])
        else:
            s = time.time()
            tx.extend(tx_in_shard_by_sender(sender, shard))
            e = time.time()
        
        stats ={}
        stats['peer'] = peer
        stats['time'] = e - s
        time_stats[shard] = stats

    end = time.time()
    total_elapsed = end-start

    time_stats['total'] = total_elapsed
    response= {
                "tx":tx,
                "time_stats":time_stats
                }

    return json.dumps(response),200


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
    logging.info(f"Total Blocks - {len(bchain.chain)} Current chain - ")
    for block in bchain.chain:
        print(json.dumps(block.__dict__, indent=4))

    return "print chain"


def peer_broadcast_thread(url, data, header={"Content-Type": 'application/json'}):
    response = requests.post(url, json = data, headers=header)
    logging.info(f"response of broadcast from {url} - {response.content}")

def peer_broadcast(url, data, exclude, header={"Content-Type": 'application/json'}):
    for peer in peers:
        if peer not in exclude:
            t = threading.Thread(target=peer_broadcast_thread, args=(peer+url, data, header, ))
            t.start()
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
        logging.info(f"can not get host name and ip address")

def get_ext_ip():
    ip = requests.get('https://api.ipify.org').text 
    logging.info(f'My public IP address is: {ip}')
    return ip

def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()

@app.route('/shutdown', methods=['GET'])
def shutdown():
    shutdown_server()
    return 'Server shutting down...'

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
    host_ip =  get_host_ip()
    
    SELF_KEY = "http://" + get_ext_ip() + ":" + repr(port)+"/"
    logging.info(f"SELF_KEY - {SELF_KEY}")
    peer_insert(get_my_key())
    app.run(host=host_ip, port=port, debug=True, threaded=False)
