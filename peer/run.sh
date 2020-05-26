#!/bin/bash

p=5000

while [ $p -le 5014 ]
do
 python3 peer.py -p $p &
 p=$((p + 1))
 echo $p
done

