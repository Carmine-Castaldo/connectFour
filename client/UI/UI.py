from controller.network_controller import NetworkClient
import time
import threading
import os

class UI:
    
    def __init__(self, network):
        self.network = network
        self.game_on = False
        self.my_turn = False
        self.my_game = False
        self.board = [[0 for _ in range(7)] for _ in range(6)]
        self.response_event = threading.Event()

    def reset_board(self):
        self.board = [[0 for _ in range(7)] for _ in range(6)]
        self.game_on = False
        self.my_turn = False

    def draw(self, status_msg=''):
        self.clear_screen()
        print("\n   0   1   2   3   4   5   6  ")
        print(" +---" * 7 + "+")
        for row in self.board:
            row_str = " |"
            for cell in row:
                if cell == 1:
                    symbol = " X " 
                elif cell == 2:
                    symbol = " O "      
                else:
                    symbol = "   "
                row_str += symbol + "|"
            print(row_str)
            print(" ----" * 7 + "-")
        print()
        if status_msg:
            print(f"{status_msg}\n")


    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def update_board(self, msg: str):
    
        parts = msg.strip().split()
        if len(parts) == 4:
            player = int(parts[1])  
            row = int(parts[2])     
            col = int(parts[3])     
            self.board[row][col] = player

    #TO DELETE
    def input_terminal(self):
        while True:
            if not self.game_on:
                msg = input("Inserisci Azione: ").strip()
                if msg:
                    self.handle_input(msg)
            else:

                if self.my_turn:
                    col_str = input("Scegli la colonna (0-6): ").strip()
                    
                    if not self.game_on:
                        continue

                    if col_str.isdigit() and 0 <= int(col_str) <= 6:
                        self.handle_input(f"MOVE {col_str}")
                        self.my_turn = False 
                    else:
                        print("Scegli una colonna valida tra 0 e 6")
                else:    
                    time.sleep(0.2)    


    def handle_msg(self, msg):
        msg = msg.strip()
                
        if msg.startswith("UPDATE_BOARD"):
            self.update_board(msg)
            status_msg = "YOUR TURN\n" if self.my_turn else "WAITING OPPONENT\n"
            self.draw(status_msg)

        elif msg == "YOUR TURN":
            self.my_turn = True
            self.game_on = True
            self.draw("IT IS YOUR TURN")
            self.response_event.set()
        elif msg == "WAIT TURN":
            self.my_turn = False
            self.game_on = True
            self.draw("WAITING FOR OPPONENT MOVE")
            self.response_event.set()
        elif msg in ["WIN", "LOSE", "DRAW"]:

            if msg == "WIN":
                print("WIN\n")
            elif msg == "LOSE":
                print("LOSE\n")
            elif msg == "DRAW":
                print("DRAW\n")    
            self.reset_board()  
            
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
            self.reset_board()
            if len(parts) > 1 and parts[1].isdigit():
                id_match = parts[1]
                self.my_game = False
                print(f'JOIN {id_match}')
                self.response_event.clear()
                self.network.join_match(id_match)
                self.response_event.wait(timeout=2.0)
                
            
        elif command == 'DISCONNECT':
            print('DISCONNECT')
            self.network.disconnect()
            
        elif command == 'CREATE':
            self.reset_board()
            self.my_game = True
            self.response_event.clear()
            self.network.create_match()
            self.response_event.wait(timeout=2.0)
            print('CREATE\n')
        #move, disconnection, join, create, ... ? 
        

                        

