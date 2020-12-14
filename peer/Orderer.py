import logging
import time
import numpy as np
import copy
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
import blockchain
app = Flask(__name__)

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] - %(message)s', datefmt='%H:%M:%S')

transaction_queue = []
creating_block = False
PREV_HASH=""
LAST_INDEX = 1


bchain = blockchain.Blockchain()
PREV_HASH = bchain.chain[0].hash
worldstate = blockchain.Worldstate()
tracker = blockchain.ShardInfoTracker()
max_number_of_transaction_in_single_block = 100

peerlist = []

def get_host_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        print("can not get host name and ip address")

def send_block_to_peer(peer, block):
    response = requests.post(peer + '/add_block', json = block.__dict__, headers={"Content-Type": 'application/json'})
    logging.info(f"Block Sent to Peer : {peer}, peer response : {response}")

def block_broadcast(block):
    for i in range(len(peerlist)):
        peer_thread = threading.Thread(target = send_block_to_peer, args = (peerlist[i], block, ))
        peer_thread.start()

def send_peerlist_to_peer(peer):
    global peerlist
    response = requests.post(peer + '/peerlist', json = {'peers': peerlist}, headers={"Content-Type": 'application/json'})
    logging.info(f"Peerlist Sent to Peer : {peer}, peer response : {response}")

def peerlist_broadcast():
    global peerlist
    for i in range(len(peerlist)):
        peer_thread = threading.Thread(target = send_peerlist_to_peer, args = (peerlist[i], ))
        peer_thread.start()

def create_block():
    global creating_block
    global PREV_HASH
    global LAST_INDEX

    block = blockchain.Block(LAST_INDEX, bchain.current_transactions, time.time(), PREV_HASH)
    block.hash = block.compute_hash()
    PREV_HASH = block.hash
    block_broadcast(copy.deepcopy(block))
    broadcast_index = LAST_INDEX
    LAST_INDEX += 1
    bchain.current_transactions=[]
    print('block has been broadcasted, tx = ' + str(broadcast_index))


@app.route('/getTransaction', methods=['POST'])
def add_tx_to_queue():
    values = request.get_json()
    global creating_block
    bchain.new_transaction(values['ts'], values['sender'], values['recipient'], values['amount'])

    if len(bchain.current_transactions) == max_number_of_transaction_in_single_block:
        create_block()
    return "Transaction Enqued", 200


@app.route('/initialize', methods=['POST'])
def init_orderer():
    global transaction_queue
    global creating_block
    global PREV_HASH
    global LAST_INDEX
    global bchain
    global PREV_HASH
    global worldstate
    global tracker
    global max_number_of_transaction_in_single_block

    transaction_queue = []
    creating_block = False
    PREV_HASH=""
    LAST_INDEX = 1
    bchain = blockchain.Blockchain()
    PREV_HASH = bchain.chain[0].hash
    worldstate = blockchain.Worldstate()
    tracker = blockchain.ShardInfoTracker()
    max_number_of_transaction_in_single_block = 50


@app.route('/register', methods=['POST'])
def new_peer():
    peer_address = request.get_json()
    peerlist.append(peer_address['node_address'])
    #peerlist_broadcast()
    return "Enlisted as Peer : " + str(peer_address['node_address']), 200
    
if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on')
    args = parser.parse_args()
    port = args.port
    NODE_NUMBER = port
    # NODE_NUMBER = args.node
    host_ip =  get_host_ip()
    
    SELF_KEY = "http://" + get_host_ip() + ":" + repr(port)+"/"
    print(SELF_KEY)
    app.run(host=host_ip, port=port, debug=True, threaded=False)