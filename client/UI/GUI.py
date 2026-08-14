import tkinter as tk
from tkinter import messagebox
import queue
import re
import os
from UI import config as cfg

class GUI:
    def __init__(self, network_controller):
        self.network = network_controller
    
        self.network.on_message_callback = self.enqueue_message
        self.gui_queue = queue.Queue()
        
        self.game_on = False
        self.my_turn = False
        self.my_game = False
        self.last_game = None
        self.rematch_cancelled = False
        self.challenger_fd = "UNKNOWN"
        self.pending_join_request = False
        self.root = tk.Tk()
        self.root.title(cfg.WINDOW_TITLE)
        self.root.geometry(cfg.WINDOW_GEOMETRY)
        self.root.configure(bg=cfg.COLOR_BG)
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.board = [[0 for _ in range(7)] for _ in range(6)]
        self.circles = [[None for _ in range(7)] for _ in range(6)] 
        self.lobby_frame = None
        self.known_matches = {}
        self.current_match_id = None
        self.game_frame = None
        
        self.show_lobby_screen()
        
        self.root.after(100, self.process_queue)

    def enqueue_message(self, msg):
        self.gui_queue.put(msg)

    def process_queue(self):
        try:
            while True:
                msg = self.gui_queue.get_nowait()
                try:
                    self.handle_server_message(msg)
                except tk.TclError:

                    pass
        except queue.Empty:
            pass
        self.root.after(100, self.process_queue)

    def show_lobby_screen(self):
        self.my_game = False
        self.current_match_id = None
        self.my_turn = False

        if self.game_frame:
            self.game_frame.destroy()
            self.game_frame = None
        if self.lobby_frame:
            self.lobby_frame.destroy()
            self.lobby_frame = None
            
        self.lobby_frame = tk.Frame(self.root, bg=cfg.COLOR_BG)
        self.lobby_frame.pack(expand=True, fill="both", padx=20, pady=20)
        
        title_label = tk.Label(self.lobby_frame, text=cfg.TXT_TITLE, font=cfg.FONT_TITLE, fg=cfg.COLOR_TEXT_PINK, bg=cfg.COLOR_BG)
        title_label.pack(pady=20)
        
        btn_create = tk.Button(self.lobby_frame, text=cfg.TXT_CREATE_BTN, font=cfg.FONT_BTN_LARGE, 
                               bg=cfg.COLOR_BG, fg=cfg.COLOR_TEXT_NEON, activebackground=cfg.COLOR_BTN_ACTIVE,
                               activeforeground=cfg.COLOR_BG, bd=2, relief="flat", highlightbackground=cfg.COLOR_BTN_BORDER,
                               command=self.on_create_click)
        btn_create.pack(pady=10)
        
        self.rooms_outer = tk.LabelFrame(self.lobby_frame, text="ACTIVE LOBBIES", font=cfg.FONT_LABEL_MEDIUM, 
                                         fg=cfg.COLOR_TEXT_NEON, bg=cfg.COLOR_BG, bd=2, relief="groove")
        self.rooms_outer.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.lobby_canvas = tk.Canvas(self.rooms_outer, bg=cfg.COLOR_BG, highlightthickness=0)
        self.lobby_scrollbar = tk.Scrollbar(self.rooms_outer, orient="vertical", command=self.lobby_canvas.yview)
        
        self.rooms_container = tk.Frame(self.lobby_canvas, bg=cfg.COLOR_BG)
        

        self.rooms_container.bind(
            "<Configure>",
            lambda e: self.lobby_canvas.configure(scrollregion=(0, 0, e.width, e.height))
        )
        
        self.canvas_window = self.lobby_canvas.create_window((0, 0), window=self.rooms_container, anchor="nw")
        
        self.lobby_canvas.bind(
            "<Configure>",
            lambda e: self.lobby_canvas.itemconfig(self.canvas_window, width=e.width)
        )
        
        self.lobby_canvas.configure(yscrollcommand=self.lobby_scrollbar.set)
        
        self.lobby_canvas.pack(side="left", fill="both", expand=True)
        self.lobby_scrollbar.pack(side="right", fill="y")
        
        self.match_cards = {}
        for m_id, status in self.known_matches.items():
            self.draw_match_card(m_id, status)
        
        self.status_label = tk.Label(self.lobby_frame, text=cfg.TXT_LOBBY_STATUS_DEFAULT, font=cfg.FONT_LABEL_SMALL, fg=cfg.COLOR_TEXT_MUTED, bg=cfg.COLOR_BG)
        self.status_label.pack(pady=15)

    def on_create_click(self):
        self.reset_board()
        self.my_game = True
        self.status_label.config(text=cfg.MSG_CREATING, fg=cfg.COLOR_TEXT_NEON)
        self.network.create_match() 


    def make_move(self, col):
        print(f"MOVE {col}")
        self.network.move(str(col)) 
        self.disable_buttons()

    def on_closing(self):
        try:
            self.network.disconnect() 
        except:
            pass
        os._exit(0)

    def on_quit_match(self):
        self.game_on = False
        if self.current_match_id is not None:
            self.known_matches[self.current_match_id] = "TERMINATED"
        self.current_match_id = None
        self.network.quit() 
        self.show_lobby_screen()

    def show_game_screen(self):
        if self.game_frame:
            self.game_frame.destroy()
            self.game_frame = None
        if self.lobby_frame:
            self.lobby_frame.destroy()
            self.lobby_frame = None
            
        self.game_frame = tk.Frame(self.root, bg=cfg.COLOR_BG)
        self.game_frame.pack(expand=True, fill="both")
        
        self.turn_label = tk.Label(self.game_frame, text="READY...", font=cfg.FONT_LABEL_LARGE, fg=cfg.COLOR_TEXT_WHITE, bg=cfg.COLOR_BG)
        self.turn_label.pack(pady=15)
        
        self.button_frame = tk.Frame(self.game_frame, bg=cfg.COLOR_BG)
        self.button_frame.pack()
        
        self.col_buttons = []
        for col in range(7):
            btn = tk.Button(self.button_frame, text="V", font=cfg.FONT_BTN_LARGE, width=3, 
                            bg=cfg.COLOR_BG, fg=cfg.COLOR_TEXT_NEON, activebackground=cfg.COLOR_TEXT_NEON,
                            activeforeground=cfg.COLOR_BG, bd=2, relief="flat", highlightbackground=cfg.COLOR_BTN_BORDER,
                            command=lambda c=col: self.make_move(c))
            btn.grid(row=0, column=col, padx=14, pady=5)
            self.col_buttons.append(btn)
            
        self.canvas = tk.Canvas(self.game_frame, width=490, height=420, bg=cfg.COLOR_BG_BOARD, highlightthickness=4, highlightbackground=cfg.COLOR_CABINET_BLUE)
        self.canvas.pack(pady=10)
        
        btn_quit = tk.Button(self.game_frame, text=cfg.TXT_QUIT_BTN, font=cfg.FONT_BTN_SMALL, 
                            bg=cfg.COLOR_BG, fg=cfg.COLOR_TEXT_PINK, activebackground=cfg.COLOR_TEXT_PINK,
                            activeforeground=cfg.COLOR_BG, bd=2, relief="flat", highlightbackground=cfg.COLOR_TEXT_PINK,
                            command=self.on_quit_match)
        btn_quit.pack(pady=10)
            
        self.draw_graphic_board()

        if self.my_turn:
            self.turn_label.config(text=cfg.MSG_YOUR_TURN, fg=cfg.COLOR_TEXT_NEON)
            self.enable_buttons()
        else:
            self.turn_label.config(text=cfg.MSG_WAIT_TURN, fg=cfg.COLOR_TEXT_PINK)
            self.disable_buttons()

    def draw_graphic_board(self):
        self.canvas.delete("all")
        for r in range(6):
            for c in range(7):
                x1, y1 = c * 70 + 10, r * 70 + 10
                x2, y2 = x1 + 50, y1 + 50
                self.canvas.create_oval(x1, y1, x2, y2, fill=cfg.COLOR_CIRCLE_EMPTY, outline=cfg.COLOR_CABINET_BLUE, width=3)
                self.circles[r][c] = (x1, y1, x2, y2) 

    def update_board(self, msg):
        parts = msg.strip().split()
        if len(parts) == 4:
            player = int(parts[1])  
            row = int(parts[2])     
            col = int(parts[3])     
            self.board[row][col] = player

    def update_board_graphic(self, row, col, player):
        if self.circles[row][col] is None:
            return
            
        x1, y1, x2, y2 = self.circles[row][col]
        if player == 1:
            color_dark = cfg.COLOR_P1_DARK
            color_light = cfg.COLOR_P1_LIGHT
        else:
            color_dark = cfg.COLOR_P2_DARK
            color_light = cfg.COLOR_P2_LIGHT
        
        self.canvas.create_oval(x1, y1, x2, y2, fill=color_dark, outline="#000000", width=2)
        self.canvas.create_oval(x1+3, y1+3, x2-3, y2-3, fill=color_light, outline="", width=0)
        self.canvas.create_oval(x1+8, y1+8, x1+16, y1+16, fill="#ffffff", outline="", width=0)



    def reset_graphic_board(self):
        self.reset_board()
        if getattr(self, 'canvas', None) is not None:
            self.draw_graphic_board()

    def sync_board_graphic(self):
        self.draw_graphic_board()
        for r in range(6):
            for c in range(7):
                val = self.board[r][c]
                if val != 0:
                    self.update_board_graphic(r, c, val)



    def enable_buttons(self):
        i = 0
        for btn in self.col_buttons:
            if self.board[0][i] == 0:
                btn.config(state="normal", fg=cfg.COLOR_TEXT_NEON)
            i+=1

    def disable_buttons(self):
        for btn in self.col_buttons:
            btn.config(state="disabled", fg=cfg.COLOR_TEXT_MUTED)


    def handle_server_message(self, msg):
        msg = msg.strip()

        if msg.startswith("THE MATCH") and "IS CREATED" in msg:   
            match_id_list = re.findall(r'\d+', msg)
            if match_id_list:
                print("MATCH_ID_FOUND %d", match_id_list)
                m_id = match_id_list[0]
                self.known_matches[m_id] = "AVAILABLE"
                if getattr(self, 'my_game', False) and self.current_match_id is None:
                    self.current_match_id = m_id
                
                if getattr(self, 'my_game', False):
                    self.status_label.config(text=cfg.MSG_WAITING_OPPONENT.format(match_id=m_id), fg=cfg.COLOR_TEXT_NEON)
                else:
                    self.status_label.config(text=cfg.MSG_NEW_ROOM_AVAILABLE.format(match_id=m_id), fg=cfg.COLOR_TEXT_PINK)
                if self.lobby_frame:
                    self.draw_match_card(m_id, "AVAILABLE")
            
        elif "IS STARING" in msg or "IS STARTING" in msg:
            match_id_list = re.findall(r'\d+', msg)
            if match_id_list:
                m_id = match_id_list[0]
                self.known_matches[m_id] = "PLAYING"
                if self.lobby_frame and m_id in self.match_cards:
                    self.match_cards[m_id]["frame"].config(bg=cfg.COLOR_BG, highlightbackground=cfg.COLOR_TEXT_MUTED)
                    self.match_cards[m_id]["lbl_id"].config(bg=cfg.COLOR_BG, fg=cfg.COLOR_TEXT_MUTED)
                    self.match_cards[m_id]["lbl_status"].config(text="PLAYING", fg=cfg.COLOR_TEXT_PINK, bg=cfg.COLOR_BG)
                    self.match_cards[m_id]["btn_join"].config(state="disabled", fg=cfg.COLOR_TEXT_MUTED, bg=cfg.COLOR_BG)
    
        elif msg.startswith("THE GAME") and "IS OVER" in msg:
            match_id_list = re.findall(r'\d+', msg)
            if match_id_list:
                m_id = match_id_list[0]
                self.known_matches[m_id] = "TERMINATED"
                if self.lobby_frame and m_id in self.match_cards:
                    self.match_cards[m_id]["frame"].config(bg=cfg.COLOR_BG, highlightbackground=cfg.COLOR_TEXT_MUTED)
                    self.match_cards[m_id]["lbl_id"].config(bg=cfg.COLOR_BG, fg=cfg.COLOR_TEXT_MUTED)
                    self.match_cards[m_id]["lbl_status"].config(text="TERMINATED", fg=cfg.COLOR_TEXT_MUTED, bg=cfg.COLOR_BG)
                    self.match_cards[m_id]["btn_join"].config(state="disabled", fg=cfg.COLOR_TEXT_MUTED, bg=cfg.COLOR_BG)
        elif msg == "YOUR TURN":
            self.my_turn = True
            self.game_on = True
            if self.game_frame is None:
                self.show_game_screen()
            else:
                self.turn_label.config(text=cfg.MSG_YOUR_TURN, fg=cfg.COLOR_TEXT_NEON)
                self.enable_buttons()

        elif msg == "WAIT TURN":
            self.my_turn = False
            self.game_on = True
            if self.game_frame is None:
                self.show_game_screen()
            else:
                self.turn_label.config(text=cfg.MSG_WAIT_TURN, fg=cfg.COLOR_TEXT_PINK)
                self.disable_buttons()

        elif msg.startswith("UPDATE_BOARD"):
            self.update_board(msg) 
            self.sync_board_graphic()
            if getattr(self, 'turn_label', None) is not None:
                if self.my_turn:
                    self.turn_label.config(text=cfg.MSG_YOUR_TURN, fg=cfg.COLOR_TEXT_NEON)
                    self.enable_buttons()
                else:
                    self.turn_label.config(text=cfg.MSG_WAIT_TURN, fg=cfg.COLOR_TEXT_PINK)
                    self.disable_buttons()
            
        elif msg.startswith("JOIN_REQUEST"):
            if not getattr(self, 'my_game', False):
                return
            parts = msg.split()
            self.challenger_fd = parts[1] if len(parts) > 1 else "UNKNOWN"
            self.pending_join_request = True
            accepted = messagebox.askyesno(
                cfg.POPUP_TITLE_CHALLENGE, 
                cfg.POPUP_MSG_CHALLENGE.format(fd=self.challenger_fd)
            )
            if accepted:
                self.network.accept() 
                self.pending_join_request = False
            else:
                self.network.reject() 
                self.pending_join_request = False
                self.status_label.config(text=cfg.MSG_REJECTED, fg=cfg.COLOR_TEXT_PINK)
        elif msg in ["WIN", "LOSE", "DRAW", "OPPONENT_DISCONNECTED"]:
            self.game_on = False
            self.last_game = msg
            self.disable_buttons()
            self.reset_board()
            
            if self.current_match_id is not None:
                self.known_matches[self.current_match_id] = "TERMINATED"
                
            if msg == "WIN":
                message = cfg.POPUP_MSG_WIN
            elif msg == "LOSE":
                message = cfg.POPUP_MSG_LOSE
            elif msg == "DRAW":
                message = cfg.POPUP_MSG_DRAW
            else: 
                message = cfg.POPUP_MSG_DISCONNECTED
                self.last_game = None
                self.show_disconnect_win_popup()

            scelta = None
            if self.last_game is not None:
                scelta = messagebox.askyesno(cfg.POPUP_TITLE_END, message)
            if scelta:
                self.network.send_msg("REMATCH_ACCEPT") 
                if getattr(self, 'turn_label', None) is not None:
                    self.turn_label.config(text=cfg.MSG_REMATCH_WAIT, fg=cfg.COLOR_TEXT_WHITE)
            else:
                self.network.send_msg("REMATCH_DECLINE")
                self.current_match_id = None
                self.show_lobby_screen()

        elif msg == "OPPONENT_WANTS_REMATCH":
            if getattr(self, 'turn_label', None) is not None:
                self.turn_label.config(text=cfg.MSG_OPPONENT_ASK_REMATCH, fg=cfg.COLOR_TEXT_NEON)

        elif msg == "REMATCH_START":
            self.game_on = True
            self.reset_board()
            self.sync_board_graphic()
            if getattr(self, 'turn_label', None) is not None:
                self.turn_label.config(text=cfg.MSG_REMATCH_ACCEPTED, fg=cfg.COLOR_TEXT_NEON)

        elif msg in ["REMATCH_DECLINED", "REMATCH_CANCELLED"]:
            self.rematch_cancelled = True
            self.game_on = False
            if self.current_match_id is not None:
                self.known_matches[self.current_match_id] = "TERMINATED"
            self.current_match_id = None
            messagebox.showinfo(cfg.POPUP_TITLE_REMATCH_CANCEL, cfg.POPUP_MSG_REMATCH_CANCEL)
            self.show_lobby_screen()
        elif msg.startswith("ROOM"):
            self.update_match_card_busy(msg)
        else:
            if getattr(self, 'status_label', None) is not None:
                self.status_label.config(text=msg, fg=cfg.COLOR_TEXT_WHITE)

    def start(self):
        self.root.mainloop()

    def reset_board(self):
        self.board = [[0 for _ in range(7)] for _ in range(6)]

    def update_match_card_started(self, msg):
        parts = msg.strip().split()
        if len(parts) < 2:
            return
        match_id = parts[1]
        if match_id not in self.match_cards:
            return
        card_data = self.match_cards[match_id]
        
        card_data["frame"].config(bg=cfg.COLOR_BG, highlightbackground=cfg.COLOR_TEXT_MUTED)
        card_data["lbl_id"].config(bg=cfg.COLOR_BG, fg=cfg.COLOR_TEXT_MUTED)
        card_data["lbl_status"].config(text="PLAYING", fg=cfg.COLOR_TEXT_PINK, bg=cfg.COLOR_BG)
        card_data["btn_join"].config(state="disabled", fg=cfg.COLOR_TEXT_MUTED, bg=cfg.COLOR_BG)

    def on_join_card_click(self, match_id):
        self.reset_board()
        self.my_game = False
        self.status_label.config(text=cfg.MSG_JOINING.format(match_id=match_id), fg=cfg.COLOR_TEXT_PINK)
        self.network.join_match(str(match_id))


    def draw_match_card(self, match_id, status):
        card = tk.Frame(self.rooms_container, bg=cfg.COLOR_BG_BOARD, bd=1, relief="solid", highlightbackground=cfg.COLOR_CABINET_BLUE, highlightthickness=1)
        card.pack(fill="x", padx=10, pady=5)
        
        lbl_id = tk.Label(card, text=f"ROOM #{match_id}", font=cfg.FONT_LABEL_MEDIUM, fg=cfg.COLOR_TEXT_WHITE, bg=cfg.COLOR_BG_BOARD)
        lbl_id.pack(side="left", padx=10, pady=5)
        
        if status == "AVAILABLE":
            status_text = "AVAILABLE"
            status_color = cfg.COLOR_TEXT_NEON
            btn_state = "normal"
        elif status == "PLAYING":
            status_text = "PLAYING"
            status_color = cfg.COLOR_TEXT_PINK
            btn_state = "disabled"
        else:
            status_text = "TERMINATED"
            status_color = cfg.COLOR_TEXT_MUTED
            btn_state = "disabled"
            
        lbl_status = tk.Label(card, text=status_text, font=cfg.FONT_LABEL_SMALL, fg=status_color, bg=cfg.COLOR_BG_BOARD)
        lbl_status.pack(side="left", padx=20, pady=5)
        
        btn_join = tk.Button(card, text="JOIN", font=cfg.FONT_BTN_SMALL, bg=cfg.COLOR_BG, fg=cfg.COLOR_TEXT_NEON, 
                             activebackground=cfg.COLOR_TEXT_NEON, activeforeground=cfg.COLOR_BG, bd=1, relief="flat", 
                             state=btn_state,
                             command=lambda: self.on_join_card_click(match_id))
        btn_join.pack(side="right", padx=10, pady=5)
        
        self.match_cards[match_id] = {
            "frame": card,
            "lbl_id": lbl_id,
            "lbl_status": lbl_status,
            "btn_join": btn_join
        }

    def show_disconnect_win_popup(self):
            self.disable_buttons()
        
            popup = tk.Toplevel(self.root)
            popup.title("Partita Terminata")
            popup.geometry("380x220")
            popup.configure(bg=cfg.COLOR_BG)
            popup.resizable(False, False)
        
            popup.transient(self.root)
            popup.grab_set()
            
            popup.geometry("+{}+{}".format(
                self.root.winfo_x() + 50,
                self.root.winfo_y() + 100
            ))

            lbl_msg = tk.Label(
                popup, 
                text="L'avversario ha abbandonato.\nHAI VINTO! ", 
                font=cfg.FONT_LABEL_MEDIUM, 
                fg=cfg.COLOR_TEXT_NEON, 
                bg=cfg.COLOR_BG,
                justify="center"
            )
            lbl_msg.pack(pady=35)
            
            btn_ok = tk.Button(
                popup, 
                text="OK", 
                font=cfg.FONT_BTN_LARGE, 
                bg=cfg.COLOR_BG, 
                fg=cfg.COLOR_TEXT_PINK, 
                activebackground=cfg.COLOR_BTN_ACTIVE,
                activeforeground=cfg.COLOR_BG, 
                bd=2, 
                relief="flat", 
                highlightbackground=cfg.COLOR_BTN_BORDER,
                command=lambda: [popup.destroy(), self.show_lobby_screen()]
            )
            btn_ok.pack(pady=10)    
    def update_match_card_busy(self, msg):
        try:
            parts = msg.strip().split()
            if len(parts) < 2:
                return
            match_id_str = parts[1]
            match_id_int = int(match_id_str)
            is_busy = "BUSY" in msg

            if hasattr(self, 'match_cards'):
                card = self.match_cards.get(match_id_int) or self.match_cards.get(match_id_str)
                if card:

                    frame = card.get("frame")
                    if frame and not frame.winfo_exists():
                        self.match_cards.pop(match_id_int, None)
                        self.match_cards.pop(match_id_str, None)
                        return

                    btn = card.get("btn_join")      
                    lbl = card.get("lbl_status")  
                    if is_busy:
            
                        if btn:
                            btn.config(state="disabled", text="BUSY")
                        if lbl:
                            lbl.config(text="Occupata...", fg=cfg.COLOR_TEXT_PINK)
                    else:
                        
                        if btn:
                            btn.config(state="normal", text="JOIN")
                        if lbl:
                            lbl.config(text="In attesa", fg=cfg.COLOR_TEXT_NEON)
                else:
                    print(f"Card non trovata per match_id {match_id_str}. Chiavi presenti: {list(self.match_cards.keys())}")
        except Exception as e:
            print(f"Errore update_match_card_busy: {e}")
