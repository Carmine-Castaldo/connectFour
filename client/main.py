from controller.network_controller import NetworkClient
import threading
from UI.GUI import GUI

def main():
    network = NetworkClient(host="tqofu-2001-b07-a3c-af2c-7cc-26a2-e4f9-4032.run.pinggy-free.link", port=41743) 
    if not network.connect():
        print("Connessione Fallita")
        return
    gui = GUI(network)
    network_thread = threading.Thread(target=network.listen_server, daemon=True)
    network_thread.start()
    
    gui.start()

if __name__ == "__main__":
    main()