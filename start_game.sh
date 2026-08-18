#!/bin/bash

# Script per avviare il server e un numero dinamico di client per il progetto Connect Four (LSO)

# Cartelle del server e del client
SERVER_DIR="./server"
CLIENT_DIR="./client"

# Verifica se il parametro è stato fornito
if [ -z "$1" ]; then
    echo "Errore: Specificare il numero di client da avviare."
    echo "Uso: $0 <numero_client> (deve essere minore di 100)"
    exit 1
fi

# Verifica se il parametro è un numero intero positivo
if ! [[ "$1" =~ ^[0-9]+$ ]] || [ "$1" -eq 0 ]; then
    echo "Errore: Il numero di client deve essere un intero positivo (maggiore di 0)."
    exit 1
fi

# Verifica che il numero sia minore di 100
if [ "$1" -ge 100 ]; then
    echo "Errore: Il numero massimo di client consentito è 99 (deve essere minore di 100)."
    exit 1
fi

NUM_CLIENTS=$1

# Funzione per terminare tutti i processi all'uscita dello script
cleanup() {
    echo ""
    echo "Arresto del server (PID: $SERVER_PID) e dei client..."
    kill $SERVER_PID 2>/dev/null
    # Termina anche eventuali client avviati in background nel terminale corrente
    kill $(jobs -p) 2>/dev/null
    exit 0
}

trap cleanup SIGINT SIGTERM

if [ ! -d "$SERVER_DIR" ] || [ ! -d "$CLIENT_DIR" ]; then
    echo "Errore: Assicurati di lanciare lo script dalla cartella principale del progetto."
    exit 1
fi

echo "Avvio del server C..."
cd "$SERVER_DIR" || exit
./server &
SERVER_PID=$!
cd - > /dev/null
