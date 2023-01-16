#!/bin/bash

while true; do
    ./idle-bot.py
    ret=$?
    if [[ $ret == 2 ]]; then
        continue
    else
        if [[ $ret != 0 ]]; then
            echo
            echo "ERROR: idle-pyt.py exited with $ret"
        fi
        break
    fi
done
