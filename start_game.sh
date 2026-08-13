#!/bin/bash

SERVER_DIR="./server"
CLIENT_DIR="./client"

cleanup() {
    echo ""
    kill $SERVER_PID 2>/dev/null
    exit 0
}

trap cleanup SIGINT SIGTERM

if [ ! -d "$SERVER_DIR" ] || [ ! -d "$CLIENT_DIR" ]; then
    echo "Errore: avvia lo script dalla root del progetto."
    exit 1
fi

cd "$SERVER_DIR" || exit
./server &
SERVER_PID=$!
cd - > /dev/null

sleep 1

if command -v gnome-terminal &> /dev/null; then
    for i in {1..3}; do
        gnome-terminal --title="Client $i" -- bash -c "cd $CLIENT_DIR && python3 main.py; exec bash" &
    done
elif command -v xterm &> /dev/null; then
    for i in {1..3}; do
        xterm -title "Client $i" -e "cd $CLIENT_DIR && python3 main.py; bash" &
    done
else
    for i in {1..3}; do
        cd "$CLIENT_DIR" || exit
        python3 main.py &
        cd - > /dev/null
    done
fi

while true; do
    sleep 1
done
