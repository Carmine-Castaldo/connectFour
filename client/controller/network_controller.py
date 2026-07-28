
import socket
import threading

class NetworkClient:

    def init(self, host='127.0.0.1', port=8080):
        self.host = host
        self.port = port
        self.socket = None
        self.running = False
        

    def connect(self):
        #TO DO
        pass

    def recv_msg(self):
        #TO DO
        pass

    def send_msg(self):
        #TO DO
        pass
    def create_match(self):
        #TO DO
        pass

    def join_match(self):
        #TO DO
        pass
       
    def move(self, col: int):
        #TO DO
        pass

    def disconnect(self):
        #TO DO 
        pass


