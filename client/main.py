from controller.network_controller import NetworkClient
import threading
from UI.GUI import GUI

def main():
    network = NetworkClient(host="127.0.0.1", port=8080) 
    if not network.connect():
        print("Connessione Fallita")
        return
    gui = GUI(network)
    network_thread = threading.Thread(target=network.listen_server, daemon=True)
    network_thread.start()
    
    gui.start()

if __name__ == "__main__":
    main()