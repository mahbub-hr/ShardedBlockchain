import requests
import json
import time
from time import sleep
import math

msp = "http://192.168.0.102:5000/"


url = f'{msp}/sign_up'
data = {"name":"A", "amount": 10000}
response = requests.post(url,json=data, headers={"Content-Type":'application/json'})
filename = data["name"] + "_key.pem"
key = response.content.decode("utf-8")

file1 = open(filename,"w") 
file1.write(key)
file1.close()