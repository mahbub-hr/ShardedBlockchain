import logging
import time
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
from flask import Flask, jsonify, request, send_from_directory
import subprocess
import threading
import blockchain

from base64 import (
    b64encode,
    b64decode,
)

from Crypto.Hash import SHA256
from Crypto.Signature import PKCS1_v1_5
from Crypto.PublicKey import RSA

app = Flask(__name__)

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] - %(message)s', datefmt='%H:%M:%S')

Clients = []
peerlist = []


@app.route('/init_node', methods=['GET'])
def initialize():
    global Clients, peerlist
    Clients = []
    peerlist = []
    return "MSP Reset - Done", 200

@app.route('/register', methods=['POST'])
def new_peer():
    peer_address = request.get_json()
    peerlist.append(peer_address['node_address'])
    #peerlist_broadcast()
    return "Enlisted as Peer : " + str(peer_address['node_address']), 200

def get_ext_ip():
    ip = requests.get('https://api.ipify.org').text 
    logging.info(f'My public IP address is: {ip}')
    return ip

def get_host_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        logging.info(f"can not get host name and ip address")


def peerbroadcast_nonthreaded(data):
    global peerlist
    for peer in peerlist:
        url = f'{peer}/new_client'
        requests.post(url,json=data, headers={"Content-Type":'application/json'})

@app.route('/sign_up', methods=['POST'])
def signup():
    data = request.get_json()
    global Clients
    print("Got req for ------", data["name"])
    if data["name"] not in Clients:
        account_name = data["name"]
        Clients.append(data["name"])
        filename = account_name + "_key.pem"
        cmd = "openssl genrsa -out " + filename + " 1024"
        os.system(cmd)
        #time.sleep(1)
        path = subprocess.check_output("pwd", shell=True).decode("utf-8").rstrip()
        with open (filename, "r") as myfile:
            public_key = RSA.importKey(myfile.read()).publickey().exportKey("PEM").decode("utf-8")
        temp_data = {"name" : account_name, "amount": data["amount"], "publickey": public_key}
        peerbroadcast_nonthreaded(temp_data)
        try:
            print(subprocess.check_output("ls", shell=True))
            return send_from_directory(path, filename = filename, as_attachment = True)
        except FileExistsError:
            print("File exist error")
            return "File Not Found", 404
    
    else:
        return "Client already exist", 501





@app.route('/test', methods=['POST', 'GET'])
def test_func():
    #data = request.get_json()
    global Clients
    
    #account_name = "A"
    #initial_amount = 10000
    #Clients.append(data["name"])
    filename = "A_key.pem"
    #cmd = "openssl genrsa -out " + filename + " 1024"
    #os.system(cmd)
    #time.sleep(1)
    path = subprocess.check_output("pwd", shell=True).decode("utf-8")
    path2 = "/home/soumit/SliveredChain/ShardedBlockchain/peer"
    print(path2)
    #peerbroadcast_nonthreaded(data)
    try:
        return send_from_directory("/home/soumit/SliveredChain/ShardedBlockchain/peer", filename = filename, as_attachment = True)
    except FileExistsError:
        print("File exist error")
        return "File Not Found", 404

if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on')
    args = parser.parse_args()
    port = args.port
    NODE_NUMBER = port
    # NODE_NUMBER = args.node
    #host_ip =  get_ext_ip() #for cloud
    host_ip =  get_host_ip() #for local machine
    
    SELF_KEY = "http://" + host_ip + ":" + repr(port)+"/"
    print(SELF_KEY)
    app.run(host=host_ip, port=port, debug=True, threaded=False)