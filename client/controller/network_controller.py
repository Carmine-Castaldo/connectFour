
import socket
import threading

class NetworkClient:

    def __init__(self, host='127.0.0.1', port=8080):
        self.host = host
        self.port = port
        self.socket = None
        
    def connect(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.host, self.port))

        thread_connection = threading.Thread(target=self.listen_server, daemon=True)
        thread_connection.start()


    def listen_server(self):
        while True:
            self.recv_msg()
            if not self.msg_recv:
                print("Connessione interrota")
                self.running = False
                #self.disconnect() da vedere
                break

            self.handle_msg()

                
    def handle_msg(self):
        #
        pass

    def recv_msg(self):
        self.msg_recv = self.socket.recv(1024).decode('utf-8')
        

    def send_msg(self, msg):
        self.socket.sendall(msg.encode('utf-8'))
        
    def create_match(self):
        self.send_msg('CREATE')

    def join_match(self, id_match: int):
        self.send_msg(f'JOIN{id_match}')
       
    def move(self, col: int):
        self.send_msg(f'MOVE {col}')
        
    def disconnect(self):
        self.send_msg('DISCONNECT')
        


