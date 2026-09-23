from controller.network_controller import NetworkController
from controller.network_interface import INetworkController
from UI.GUI import GUI      

def main():
    network: INetworkController = NetworkController(host="127.0.0.1", port=8080) 

    if not network.connect():
        print("Connessione Fallita")
        return    

    gui = GUI(network)
    gui.start()

if __name__ == "__main__":
    main()