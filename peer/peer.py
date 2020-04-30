import requests
import json
import time
from flask import Flask, jsonify, request

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
SELF_KEY =""
app = Flask(__name__)
chain = blockchain.Blockchain()
worldstate = blockchain.Worldstate()
tracker = blockchain.ShardInfoTracker()

peers = []

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

@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    global LAST_INDEX
    values = request.get_json()

    # Check that the required fields are in the POST'ed data
    required = ['ts', 'sender', 'recipient', 'amount']
    if not all(k in values for k in required):
        return 'Missing values', 400

    # Create a new Transaction
    index = chain.new_transaction(values['ts'],values['sender'], values['recipient'], values['amount'])
    worldstate.update(values['sender'], values['recipient'], values['amount'])
    if len(chain.current_transactions) == TX_PER_BLOCK:
        block = blockchain.Block(LAST_INDEX, chain.current_transactions, time.time(), chain.last_block.hash)
        block.hash = block.compute_hash()
        added =chain.add_block(block)
        LAST_INDEX += 1
        print('block has been added')
    if added :
        response = {'message': f'Transaction added to Block {index}'}
    else :
        response = {'something is not right'}
    return jsonify(response), 201


@app.route('/chain', methods=['GET'])
def full_chain():
    chain_data = []
    for block in chain.chain:
        chain_data.append(block.__dict__)

    response = json.dumps(
                    {"length": len(chain_data),
                       "chain": chain_data,
                       "peers": peers,
                       "worldstate": worldstate.worldstate})

    return response


# endpoint to add new peers to the network.
@app.route('/register_node', methods=['POST'])
def register_new_peers():
    node_address = request.get_json()["node_address"]
    if not node_address:
        return "Invalid data", 400

    # Add the node to the peer list
    peer_insert(node_address)
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
        global chain
        global peers
        global worldstate
        global LAST_INDEX
        # update chain and the peers
        json_data = response.json()
        chain_dump = json_data['chain']
        chain = create_chain_from_dump(chain_dump)
        # need to remove if there is a seperate orderer
        LAST_INDEX = chain.chain[-1].index +1
        peer_update(json_data['peers'])
        print(peers)
        worldstate.worldstate = json_data['worldstate']
        return jsonify("Registration successful"), 200
    else:
        # if something goes wrong, pass it on to the API response
        return response.content, response.status_code


@app.route('/add_block', methods=['POST'])
def verify_and_add_block():
    block_data = request.get_json()
    block = blockchain.Block(block_data["index"],
                  block_data["transactions"],
                  block_data["timestamp"],
                  block_data["previous_hash"],
                  )

    added = chain.add_block(block)

    if not added:
        return "The block was discarded by the node", 400

    return "Block added to the chain", 201


def announce_new_block(block):
    for peer in peers:
        url = "{}add_block".format(peer)
        headers = {'Content-Type': "application/json"}
        requests.post(url,
                      data=json.dumps(block.__dict__, sort_keys=True),
                      headers=headers)


def create_chain_from_dump(chain_dump):
    generated_blockchain = blockchain.Blockchain()
    #generated_blockchain.create_genesis_block()
    for idx, block_data in enumerate(chain_dump):
        if idx == 0:
            continue  # skip genesis block
        block = blockchain.Block(block_data["index"],
                      block_data["transactions"],
                      block_data["timestamp"],
                      block_data["previous_hash"])
        block.hash = block_data['hash']
        added = generated_blockchain.add_block(block)

        if not added:
            raise Exception("The chain dump is tampered!!")
    return generated_blockchain

@app.route("/shardinit", methods=['GET'])
def init_shard():
    global LAST_SHARD
    print('chain len: ',len(chain.chain))
    global peers
    global OVERLAPPING

    track = blockchain.ShardInfoTracker()

    IS_SHARDED = True
    print(peers)
    num_of_shard = (len(chain.chain)-LAST_CHAIN_SIZE)/SHARD_SIZE
    print('num of shard: ', num_of_shard)
    i=1
    # make this global to turn around lapping
    x = 0
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
    apply_sharding()
    send_info()
    return 'init shard returned'


def apply_sharding():
    global SHARD_SIZE
    global LAST_CHAIN_SIZE
    shards = tracker.node_to_shard[SELF_KEY]
    end = SHARD_SIZE * shards[-1]

    end_index = LAST_CHAIN_SIZE + (end - chain.chain[LAST_CHAIN_SIZE].index) + 1
    start_index = end_index - SHARD_SIZE
    temp = chain.chain[:LAST_CHAIN_SIZE]
    temp.extend(chain.chain[start_index:end_index])
    chain.chain = temp
    LAST_CHAIN_SIZE = len(chain.chain)
    return "sharding done, ok"


def send_info():
    for peer in peers:
        if peer != SELF_KEY:
            url = f"{peer}sendshardinfo"
            headers = {'Content-Type': "application/json"}
            response= requests.post(url,
                                    json=(tracker.__dict__),
                                    headers=headers)
            if response.status_code == 200:
                print(peer,": ",response.content)
    return

@app.route("/sendshardinfo",methods=['POST'])
def shard_info():
    response = request.get_json()
    node_to_shard = response['node_to_shard']
    shard_to_node= response['shard_to_node']
    tracker.node_to_shard = node_to_shard
    tracker.shard_to_node = shard_to_node
    tracker.print()
    apply_sharding()
    return "successfully got it",200

@app.route('/txbysender', methods=['POST'])
def txbysender():
    data = request.get_json()
    print(data)
    sender = data['sender']
    tx_list = []
    for block in chain.chain:
        for tx in block.transactions:
            if tx['sender'] == sender:
                tx_list.append(tx)

    return json.dumps({'tx':tx_list})

@app.route("/wholeshardquery", methods=['POST'])
def wholeshardquery():
    data = request.get_json()
    sender = data['sender']
    tx = []
    for peer in peers:
        if tracker.node_to_shard[peer]:
            print('asking node: ', peer)
            response = requests.post(peer+"txbysender", json=data, headers={"Content-Type":'application/json'})
            tx.extend(response.json()['tx'])


    for t in tx:
        print(json.dumps(t, indent=4))
    return "whole shard function returned"

@app.route("/query", methods=['POST'])
def query():
    data = request.get_json()
    return repr(worldstate.get(data['key'])),200

@app.route("/printworldstate", methods=['GET'])
def printWorldstate():
    worldstate.print()
    return "print worldstate"

@app.route("/printchain", methods=['GET'])
def printchain():
    for block in chain.chain:
        print(json.dumps(block.__dict__, indent=4))

    return "print chain"


if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on')
    parser.add_argument('-a', '--anchor', default=False, type=bool, help='Is this node anchor')
    parser.add_argument('-n', '--node', default=1, type= int , help='this node number')
    args = parser.parse_args()
    port = args.port
    NODE_NUMBER = port
    #NODE_NUMBER = args.node
    IS_ANCHOR = args.anchor
    SELF_KEY="http://localhost:" + repr(NODE_NUMBER) + "/"
    print(get_my_key())
    peer_insert(get_my_key())
    app.run(host='127.0.0.1', port=port, debug=True)