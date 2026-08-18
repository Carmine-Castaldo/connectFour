# Installazione della Repository

Clona il progetto ed entra nella directory principale da terminale:
```bash
git clone https://github.com/Carmine-Castaldo/connectFour
cd connectFour
```

# In alternativa, scarica ed estrai l'archivio .zip del progetto.

Modalità di Avvio
Metodo 1: 
Autorizza Docker ad accedere al monitor dell'host 
```bash
    xhost +local:docker
```
Avvia il server e scala automaticamente a 2 Client:
```bash
docker compose up --build --scale client=2
```
Metodo 2:
Avvia solo il Server con Docker Compose:

```bash
docker compose up --build server
```
Avvia i Client sul tuo PC:

```bash
cd client && python3 main.py
```
