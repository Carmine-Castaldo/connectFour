from controller.network_controller import NetworkClient
import threading
from UI.GUI import GUI

def main():
    network = NetworkClient(
    host="naxko-93-56-156-229.run.pinggy-free.link", 
    port=39173)
    if not network.connect():
        print("Connessione Fallita")
        return
    gui = GUI(network)
    network_thread = threading.Thread(target=network.listen_server, daemon=True)
    network_thread.start()
    
    gui.start()

if __name__ == "__main__":
    main()