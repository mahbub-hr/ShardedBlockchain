#!/bin/bash
p=5000
while [ $p -le 5014 ]
do
 fuser -k "${p}/tcp"
 p=$((p + 1))
done
