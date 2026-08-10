from controller.network_controller import NetworkClient
from UI.UI import UI

def main():
    network = NetworkClient()
    ui = UI(network)
    network.on_message_callback=ui.handle_msg
    if network.connect():
        print("Connesso")
    else:
        print("Disconnesso")
    ui.input_terminal()
    


if __name__ == "__main__":
    main()