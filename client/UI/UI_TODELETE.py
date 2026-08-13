from controller.network_controller import NetworkClient
import time
import threading
import os

class UITODELETE:
    
    def __init__(self, network):
        self.network = network
        self.game_on = False
        self.my_turn = False
        self.my_game = False
        self.board = [[0 for _ in range(7)] for _ in range(6)]
        self.response_event = threading.Event()
        self.challenger_fd = None
        self.pending_join_request = False
        self.last_game = None
        self.rematch_cancelled = False

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

    
    def _handle_out_of_game_input(self):
        msg = input("Inserisci Azione: ").strip()
        if msg:
            self.handle_input(msg)

    def _handle_in_game_turn(self):
        col_str = input("Scegli la colonna (0-6): ").strip()
        
        if not self.game_on:
            return

        if col_str.isdigit() and 0 <= int(col_str) <= 6:
            self.handle_input(f"MOVE {col_str}")
            self.my_turn = False 
        elif col_str == 'QUIT':
            self.handle_input(col_str)
        else:
            print("Scegli una colonna valida tra 0 e 6")

    def input_terminal(self):
        while True:
            if not self.game_on:
                if getattr(self, 'last_game', None) is not None:
                    self.handle_game_over()
                else:
                    self._handle_out_of_game_input()
            elif self.my_turn:
                self._handle_in_game_turn()
            else:
                time.sleep(0.2)   
        print("Connessione Interrotta")


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

        elif msg in ["WIN", "LOSE", "DRAW", "OPPONENT_DISCONNECTED"]:
            self.last_game = msg
            if msg == "WIN":
                print("WIN\n")
            elif msg == "LOSE":
                print("LOSE\n")
            elif msg == "DRAW":
                print("DRAW\n")   
            else: 
                print("OPPONENT DISCONNECTED, YOU WIN\n")
                self.last_game = None

            self.reset_board()  
            self.game_on = False 
            self.rematch_cancelled = False 
            self.response_event.set()            
        elif msg.startswith("JOIN_REQUEST"):
            parts = msg.split()
            self.challenger_fd = parts[1] if len(parts) > 1 else "UNKNOWN"
            self.pending_join_request = True
            self.response_event.set()
        elif msg == "REMATCH_START":
            self.game_on = True
            self.reset_board()
            print("\nSTARTIGN THE REMATCH")
            self.response_event.set()

        elif msg == "OPPONENT_WANTS_REMATCH":
            print("\nOPPONENT ASK FOR A REMATCH")

        elif msg == "REMATCH_DECLINED":
            print("\nREMATCH DECLINED")
            self.rematch_cancelled = True
            self.game_on = False
            self.response_event.set()

        else:
            print(f"\n{msg}")
            print("Inserisci azione: ", end="", flush=True)

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
            self.network.disconnect()
            os._exit(0)
        elif command == 'CREATE':
            self.reset_board()
            self.my_game = True
            self.response_event.clear()
            self.network.create_match()

            ans = self.response_event.wait(timeout=2.0)
            if ans:
                self.wait_for_challenger()
                print('CREATE\n')
            else:
                self.my_game = False
        elif command == 'QUIT':
            self.game_on = False
            self.clear_screen()
            self.network.quit()
            
        
    def wait_for_challenger(self):
        self.pending_join_request = False
        self.game_on = True 
        while self.game_on:
            self.response_event.wait()
            self.response_event.clear()
            if getattr(self, 'pending_join_request', False):
                print(f"\n JOIN REQUEST FROM {self.challenger_fd})")
                
                scelta = ""
                while scelta not in ["ACCEPT", "REJECT"]:
                    scelta = input("DO U ACCEPT? (ACCEPT/REJECT): ").strip()
                
                if scelta == 'ACCEPT':
                    self.network.accept()
                    self.pending_join_request = False
                    break 
                else:
                    self.network.reject()
                    self.pending_join_request = False
                    self.draw("WAITING FOR OPPONENT MOVE") 
                    
    def handle_game_over(self):
        self.last_game = None
        ans = ""
        while ans not in ["REMATCH", "EXIT"]:
            ans = input("\nDo you want a rematch? (REMATCH/EXIT): ").strip()

        if ans == 'REMATCH':
            if self.rematch_cancelled:
                print("REMATCH REJECTED")
                return False
            
            print("WAITING FOR OPPONENT")
            self.response_event.clear()
            self.network.send_msg("REMATCH_ACCEPT")
            self.response_event.wait()
            return self.game_on  
        
        else:
            self.network.send_msg("REMATCH_DECLINE")
            self.game_on = False
            return False 
