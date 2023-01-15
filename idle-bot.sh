#!/bin/bash

while true; do
    ./idle-bot.py
    ret=$?
    if [[ $ret == 2 ]]; then
        continue
    else
        break
    fi
done
