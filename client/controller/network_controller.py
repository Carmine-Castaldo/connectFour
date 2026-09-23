
import socket, os
import threading, queue
from controller.network_interface import INetworkController 

class NetworkController(INetworkController):
 
    def __init__(self, on_message_callback=None, host='127.0.0.1', port=8080):
        self.on_message_callback = on_message_callback
        self.safe_queue = queue.Queue()
        self.host = host
        self.port = port
        self.socket = None
        self.running = False
        
    def connect(self):
        try: 
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.running = True

            thread_connection = threading.Thread(target=self.listen_server, daemon=True)
            thread_connection.start()
            print("Connessione stabilita")
            return True
        except Exception: 
            print("Connessione fallita")
            os._exit(0)
            return False


    def listen_server(self):
        data_buffer = ""
        while self.running:
            try:
                chunk = self.socket.recv(1024).decode('utf-8')
                if not chunk:
                    print("Connessione interrotta")
                    self.running = False
                    os._exit(0)
                    break
                
                data_buffer += chunk
                while "\n" in data_buffer:
                    line, data_buffer = data_buffer.split("\n", 1)
                    line = line.strip()
                    if line:
                        if self.on_message_callback:
                            self.on_message_callback(line)
                        else:
                            self.safe_queue.put(line)
                            
            except Exception as e:
                print(f"Errore di connessione: {e}")
                self.running = False
                os._exit(0)
                break
                
    def recv_msg(self):
        self.msg_recv = self.socket.recv(1024).decode('utf-8')

    def send_msg(self, msg):
        print(f'SENDING {msg}')
        msg_to_send = f"{msg}\n"
        self.socket.sendall(msg_to_send.encode('utf-8'))
        
    def create_match(self):
        self.send_msg('CREATE')

    def join_match(self, id_match: int):
        self.send_msg(f'JOIN {id_match}')

    def move(self, col: int):
        self.send_msg(f'MOVE {col}')

    def quit(self):
        self.send_msg("QUIT")

    def disconnect(self):
        self.send_msg('DISCONNECT')
        
    def accept(self):
        self.send_msg("ACCEPT")

    def reject(self):
        self.send_msg("REJECT")