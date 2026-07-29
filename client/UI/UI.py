from controller.network_controller import NetworkClient

class UI:
    
    def __init__(self, network):
        self.network = network
 

    def draw(self):
        #disegna la pagina (griglia, info ecc...)
        pass

    #TO DELETE
    def input_terminal(self):
        while True:
            msg = input("Inserisci Azione:")
            self.handle_input(msg)
        

    def move(self, col: int):
        #modifica la griglia e chiama il network controller per mandare la mossa al server
        pass

    def handle_msg(self, msg):
        print(f"\n[SERVER -> CLIENT]: {msg.strip()}")
        if msg.startswith('MOVE'):
            #l'avversario ha fatto la sua mossa si deve disegnare
            pass
        elif msg.startswith('JOIN'):
            pass
        elif msg == 'WIN':
            #
            pass
        elif msg == 'LOSE':
            #odio
            pass
        elif msg == 'DRAW':
            #
            pass
        elif msg == 'DISCONNECT':
            #
            pass
        # dovrrebbero esserci anche le notifiche per le partite terminate/in corso

    def handle_input(self, msg):
        parts = msg.strip().split()
        if not parts:
            return
        
        command = parts[0].upper()

        if command == 'MOVE':
            if len(parts) > 1 and parts[1].isdigit():
                col = parts[1]
                print(f'MOVE {col}')
                self.network.move(col)
            
        elif command == 'JOIN':
            if len(parts) > 1 and parts[1].isdigit():
                id_match = parts[1]
                print(f'JOIN {id_match}')
                self.network.join_match(id_match)
            
        elif command == 'DISCONNECT':
            print('DISCONNECT')
            self.network.disconnect()
            
        elif command == 'CREATE':
            self.network.create_match()
            print('CREATE')
        #move, disconnection, join, create, ... ? 
        

