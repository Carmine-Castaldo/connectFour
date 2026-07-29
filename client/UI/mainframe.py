from network_controller import NetworkClient

class UI:
    network: NetworkClient 

    def draw(self):
        #disegna la pagina (griglia, info ecc...)
        pass

    def move(self, col: int):
        #modifica la griglia e chiama il network controller per mandare la mossa al server
        pass

    def handle_msg(self, msg):
        if msg == 'MOVE':
            #l'avversario ha fatto la sua mossa si deve disegnare
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

    def handle_input(self):
        #move, disconnection, join, create, ... ? 
        pass

