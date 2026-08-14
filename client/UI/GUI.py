import tkinter as tk
from tkinter import ttk
import queue
import re
import os, platform
from UI.components import config as cfg 
from UI.components.board import Board
from UI.components.disc import Disc
from UI.components.popup import Popup


class GUI:
    def __init__(self, network_controller):
        self.network = network_controller
        self.network.on_message_callback = self.enqueue_message
        self.gui_queue = queue.Queue()
        if hasattr(self.network, 'safe_queue'):
            while not self.network.safe_queue.empty():
                msg = self.network.safe_queue.get()
                self.enqueue_message(msg)
                
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

        self.root.overrideredirect(True)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        self.main_container = tk.Frame(
            self.root, 
            bg=cfg.COLOR_BG, 
            highlightbackground=cfg.COLOR_TEXT_NEON,
            highlightcolor=cfg.COLOR_TEXT_NEON, 
            highlightthickness=5,
            bd=0
        )

        self.main_container.grid(row=0, column=0, sticky="nsew")
        self.root.bind("<Button-1>", self.start_move)
        self.root.bind("<B1-Motion>", self.do_move)

        self.circles = [[None for _ in range(7)] for _ in range(6)] 
        self.lobby_frame = None
        self.known_matches = {}
        self.current_match_id = None
        self.game_frame = None
        self.board = Board()

        self.style = ttk.Style()
        self.style.theme_use('default')
        self.style.configure(
            "Custom.Vertical.TScrollbar",
            background=cfg.COLOR_BG,        
            troughcolor=cfg.COLOR_BG,       
            bordercolor=cfg.COLOR_BG,       
            arrowcolor=cfg.COLOR_TEXT_NEON 
        )
        self.style.map(
            "Custom.Vertical.TScrollbar",
            background=[('active', cfg.COLOR_TEXT_PINK)]
        )
        
        self.load_arcade_font()
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
            
        self.lobby_frame = tk.Frame(self.main_container, bg=cfg.COLOR_BG)
        self.lobby_frame.grid(row=0, column=0, sticky="nsew", padx=30, pady=20)
        
        self.main_container.rowconfigure(0, weight=1)
        self.main_container.columnconfigure(0, weight=1)
        
        title_label = tk.Label(self.lobby_frame, text=cfg.TXT_TITLE, font=cfg.FONT_TITLE, fg=cfg.COLOR_TEXT_PINK, bg=cfg.COLOR_BG)
        title_label.pack(pady=(10, 15))
        
        self.rooms_outer = tk.LabelFrame(self.lobby_frame, text="  ACTIVE LOBBIES  ", font=cfg.FONT_LABEL_MEDIUM, 
                                         fg=cfg.COLOR_TEXT_NEON, bg=cfg.COLOR_BG, bd=0, relief="flat")
        self.rooms_outer.pack(fill="both", expand=True, padx=5, pady=10)
        
        self.rooms_outer.columnconfigure(0, weight=1)
        self.rooms_outer.columnconfigure(1, weight=0)
        self.rooms_outer.rowconfigure(0, weight=1)
        self.lobby_canvas = tk.Canvas(self.rooms_outer, bg=cfg.COLOR_BG, highlightthickness=0, height=500)        
        self.lobby_scrollbar = ttk.Scrollbar(
            self.rooms_outer, 
            orient="vertical", 
            command=self.lobby_canvas.yview, 
            style="Custom.Vertical.TScrollbar"
        )
        
        self.lobby_canvas.grid(row=0, column=0, sticky="nsew")
        self.lobby_scrollbar.grid(row=0, column=1, sticky="ns")
        
        self.rooms_container = tk.Frame(self.lobby_canvas, bg=cfg.COLOR_BG)
        self.rooms_container.bind(
            "<Configure>",
            lambda e: self.lobby_canvas.configure(scrollregion=self.lobby_canvas.bbox("all"))
        )
        self.canvas_window = self.lobby_canvas.create_window((0, 0), window=self.rooms_container, anchor="nw")
        
        self.lobby_canvas.bind(
            "<Configure>",
            lambda e: self.lobby_canvas.itemconfig(self.canvas_window, width=e.width)
        )
        
        self.lobby_canvas.configure(yscrollcommand=self.lobby_scrollbar.set)
        self.match_cards = {}
        for m_id, status in reversed(list(self.known_matches.items())):
            self.draw_match_card(m_id, status)
            
        self.status_label = tk.Label(self.lobby_frame, text=cfg.TXT_LOBBY_STATUS_DEFAULT, font=cfg.FONT_LABEL_SMALL, fg=cfg.COLOR_TEXT_MUTED, bg=cfg.COLOR_BG)
        self.status_label.pack(pady=10)
        btn_container = tk.Frame(self.lobby_frame, bg=cfg.COLOR_BG)
        btn_container.pack(pady=(5, 15))
        
        btn_create = tk.Button(btn_container, text=cfg.TXT_CREATE_BTN, font=cfg.FONT_BTN_LARGE, 
                               bg=cfg.COLOR_BG, fg=cfg.COLOR_TEXT_NEON, activebackground=cfg.COLOR_BTN_ACTIVE,
                               activeforeground=cfg.COLOR_BG, bd=2, relief="flat", highlightbackground=cfg.COLOR_BTN_BORDER,
                               command=self.on_create_click)
        btn_create.pack(side="left", padx=20, ipadx=15, ipady=5)
        
        btn_exit = tk.Button(btn_container, text="EXIT", font=cfg.FONT_BTN_LARGE, 
                             bg=cfg.COLOR_BG, fg=cfg.COLOR_TEXT_PINK, activebackground=cfg.COLOR_TEXT_PINK,
                             activeforeground=cfg.COLOR_BG, bd=2, relief="flat", highlightbackground=cfg.COLOR_TEXT_PINK,
                             command=self.on_closing)
        btn_exit.pack(side="left", padx=20, ipadx=25, ipady=5)

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
        self.network.disconnect() 
        os._exit(0)

    def on_quit_match(self):
        self.game_on = False
        if self.current_match_id is not None:
            self.known_matches[self.current_match_id] = "TERMINATED"
        self.current_match_id = None
        self.network.quit() 
        self.show_lobby_screen()

    def show_game_screen(self):
        if self.lobby_frame:
            self.lobby_frame.destroy()
            self.lobby_frame = None
        if self.game_frame:
            self.game_frame.destroy()
            self.game_frame = None
            
        self.game_frame = tk.Frame(self.main_container, bg=cfg.COLOR_BG)
        self.game_frame.grid(row=0, column=0, sticky="nsew")
        
        self.main_container.rowconfigure(0, weight=1)
        self.main_container.columnconfigure(0, weight=1)
        
        self.turn_label = tk.Label(self.game_frame, text="PARTITA IN CORSO", font=cfg.FONT_LABEL_MEDIUM, fg=cfg.COLOR_TEXT_NEON, bg=cfg.COLOR_BG)
        self.turn_label.pack(pady=10)
        
        self.canvas = tk.Canvas(self.game_frame, width=980, height=840, bg=cfg.COLOR_BG_BOARD, highlightthickness=0)
        self.canvas.pack(pady=10)
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<Motion>", self.on_canvas_hover)
        self.draw_graphic_board()
        
        btn_abandon = tk.Button(
            self.game_frame, 
            text="ABANDON MATCH", 
            font=cfg.FONT_BTN_LARGE, 
            bg=cfg.COLOR_BG, 
            fg=cfg.COLOR_TEXT_PINK, 
            activebackground=cfg.COLOR_TEXT_PINK,
            activeforeground=cfg.COLOR_BG, 
            bd=20, 
            relief="flat", 
            highlightbackground=cfg.COLOR_TEXT_PINK,
            command=self.on_abandon_click 
        )
        btn_abandon.pack(pady=(15, 20), ipadx=15, ipady=3)

    def draw_graphic_board(self):
        if not hasattr(self, 'canvas') or self.canvas is None or not self.canvas.winfo_exists():
                return
        self.canvas.delete("all")
        for r in range(self.board.rows):
            for c in range(self.board.cols):
                disc = Disc(self.canvas, r, c)
                disc.draw(self.board.get_cell(r, c))

    def update_board(self, msg):
        parts = msg.strip().split()
        if len(parts) == 4:
            player = int(parts[1])  
            row = int(parts[2])     
            col = int(parts[3])     
            self.board.update(row,col,player)

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

    def enable_buttons(self):
        if hasattr(self, 'canvas') and self.canvas.winfo_exists():
            self.canvas.config(cursor="hand2")

    def disable_buttons(self):
        if hasattr(self, 'canvas') and self.canvas.winfo_exists():
            self.canvas.config(cursor="")
            self.canvas.delete("hover_highlight")

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
            self.draw_graphic_board()
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

            def on_join_response(accepted):
                self.active_popup = None
                if accepted:
                    self.network.accept() 
                    self.pending_join_request = False
                else:
                    self.network.reject() 
                    self.pending_join_request = False
                    self.status_label.config(text=cfg.MSG_REJECTED, fg=cfg.COLOR_TEXT_PINK)

            self.active_popup = Popup(
                self.root, 
                cfg.POPUP_TITLE_CHALLENGE, 
                cfg.POPUP_MSG_CHALLENGE.format(fd=self.challenger_fd),
                popup_type="yesno", 
                callback=on_join_response
            )
        elif msg in ["WIN", "LOSE", "DRAW", "OPPONENT_DISCONNECTED"]:
            self.game_on = False
            self.last_game = msg
            self.disable_buttons()
            self.root.after(200, lambda: self.show_endgame_popup(msg))

        elif msg == "OPPONENT_WANTS_REMATCH":
            if getattr(self, 'turn_label', None) is not None:
                self.turn_label.config(text=cfg.MSG_OPPONENT_ASK_REMATCH, fg=cfg.COLOR_TEXT_NEON)

        elif msg == "REMATCH_START":
            self.game_on = True
            self.reset_board()
            self.draw_graphic_board()
            if getattr(self, 'turn_label', None) is not None:
                self.turn_label.config(text=cfg.MSG_REMATCH_ACCEPTED, fg=cfg.COLOR_TEXT_NEON)

        elif msg in ["REMATCH_DECLINED", "REMATCH_CANCELLED"]:
            self.rematch_cancelled = True
            self.game_on = False
            if self.current_match_id is not None:
                self.known_matches[self.current_match_id] = "TERMINATED"
            self.current_match_id = None

            if getattr(self, 'active_popup', None) is not None:
                try:
                    self.active_popup.top.grab_release()
                    self.active_popup.top.destroy()
                except Exception:
                    pass
                self.active_popup = None

            def on_cancel_ack(_):
                self.active_popup = None
                self.show_lobby_screen()
                
            self.active_popup = Popup(
                self.root, 
                cfg.POPUP_TITLE_REMATCH_CANCEL, 
                cfg.POPUP_MSG_REMATCH_CANCEL, 
                popup_type="ok", 
                callback=on_cancel_ack
            )
        elif msg.startswith("ROOM"):
            print(f"msg: {msg}\n")
            try:
                parts = msg.strip().split()
                if len(parts) >= 3:
                    print(f"msg: {msg}\n")
                    match_id_str = parts[1]
                    match_id_int = int(match_id_str)
                    is_creator = getattr(self, 'my_game', False) and str(self.current_match_id) == str(match_id_str)
                    if not is_creator:
                        if match_id_int not in self.match_cards and match_id_str not in self.match_cards:
                            if self.lobby_frame:
                                self.draw_match_card(match_id_str, "AVAILABLE")
                    self.update_match_card_busy(msg)                    
            except Exception as e:
                print(f"Errore nella gestione del messaggio ROOM: {e}")
        else:
            if getattr(self, 'status_label', None) is not None:
                self.status_label.config(text=msg, fg=cfg.COLOR_TEXT_WHITE)

    def start(self):
        self.root.mainloop()

    def reset_board(self):
        self.board.reset()

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
        card = tk.Frame(self.rooms_container, bg=cfg.COLOR_BG_BOARD, bd=1, relief="flat", highlightbackground=cfg.COLOR_CABINET, highlightthickness=1)
        card.pack(fill="x", padx=15, pady=8)
        
        lbl_id = tk.Label(card, text=f"ROOM #{match_id}", font=cfg.FONT_LABEL_MEDIUM, fg=cfg.COLOR_TEXT_WHITE, bg=cfg.COLOR_BG_BOARD)
        lbl_id.pack(side="left", padx=15, pady=10)
        
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
        lbl_status.pack(side="left", padx=20, pady=10)
        
        btn_join = tk.Button(card, text="JOIN", font=cfg.FONT_BTN_SMALL, bg=cfg.COLOR_BG, fg=cfg.COLOR_TEXT_NEON, 
                             activebackground=cfg.COLOR_TEXT_NEON, activeforeground=cfg.COLOR_BG, bd=1, relief="flat", 
                             state=btn_state,
                             command=lambda: self.on_join_card_click(match_id))
        btn_join.pack(side="right", padx=15, pady=10)
        
        self.match_cards[match_id] = {
            "frame": card,
            "lbl_id": lbl_id,
            "lbl_status": lbl_status,
            "btn_join": btn_join
        }

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
                    print(f"Card non trovata per match_id {match_id_str}. Chiavi: {list(self.match_cards.keys())}")
        except Exception as e:
            print(f"Errore update_match_card_busy: {e}")


    def on_canvas_click(self, event):
        if not self.my_turn:
            return
      
        col = event.x // 140
        if 0 <= col < 7:
            if self.board.get_cell(0, col) != 0:
                return
            self.canvas.delete("hover_highlight")
            self.my_turn = False
            self.make_move(col)
        

    def on_canvas_hover(self, event):
        if not self.my_turn:
            self.canvas.delete("hover_highlight")
            self.canvas.config(cursor="")
            return
        col = event.x // 140
    
        if 0 <= col < 7:
            if self.board.get_cell(0, col) != 0:
                            self.canvas.delete("hover_highlight")
                            self.canvas.config(cursor="")
                            return
            self.canvas.config(cursor="hand2")
            self.canvas.delete("hover_highlight")
            my_color = cfg.COLOR_TEXT_PINK if getattr(self, 'my_game', False) else cfg.COLOR_TEXT_NEON
            self.canvas.create_rectangle(
                col * 140 + 4, 4,
                (col + 1) * 140 - 4, 806,
                outline=my_color,
                fill=my_color,
                stipple="gray12",
                width=3,
                tags="hover_highlight"
            )
        else:
            self.canvas.delete("hover_highlight")
            self.canvas.config(cursor="")


    def on_canvas_leave(self, event):
        self.canvas.delete("hover_highlight")

    def load_arcade_font(self):
        
        font_filename = "ARCADECLASSIC.TTF"

        if not os.path.exists(font_filename):
            print(f" {font_filename} NOT FOUND")
            return "Arial"
            
        try:
            if platform.system() == "Linux":
                home_dir = os.path.expanduser("~")
                user_fonts_dir = os.path.join(home_dir, ".fonts")
                
                if not os.path.exists(user_fonts_dir):
                    os.makedirs(user_fonts_dir)
                    
                dest_font_path = os.path.join(user_fonts_dir, font_filename)
                if not os.path.exists(dest_font_path):
                    import shutil
                    shutil.copy(font_filename, dest_font_path)
                    os.system("fc-cache -f")
                
        except Exception as e:
            print(f"ERROR FONT: {e}")
            
            
        return "ArcadeClassic"


    def show_endgame_popup(self, msg):
        if self.current_match_id is not None:
            self.known_matches[self.current_match_id] = "TERMINATED"
            
        if msg == "WIN":
            message = cfg.POPUP_MSG_WIN
            p_type = "yesno"
        elif msg == "LOSE":
            message = cfg.POPUP_MSG_LOSE
            p_type = "yesno"
        elif msg == "DRAW":
            message = cfg.POPUP_MSG_DRAW
            p_type = "yesno"
        else: 
            message = "WINNER\n\n OPPONENT HAS LEFT THE ROOM.!"
            p_type = "OK"
        border_color = "#990033" if self.my_game else "#006699"

        def on_popup_closed(scelta_utente):
            self.active_popup = None
            self.reset_board()
            if getattr(self, 'canvas', None) is not None:
                self.draw_graphic_board()
                
            if p_type == "OK":
                self.current_match_id = None
                self.show_lobby_screen()
                return
                
            if scelta_utente:
                self.network.send_msg("REMATCH_ACCEPT") 
                if getattr(self, 'turn_label', None) is not None:
                    self.turn_label.config(text=cfg.MSG_REMATCH_WAIT, fg=cfg.COLOR_TEXT_WHITE)
            else:
                self.network.send_msg("REMATCH_DECLINE")
                self.current_match_id = None
                self.show_lobby_screen()

        
        self.active_popup = Popup(self.root, cfg.POPUP_TITLE_END, message, popup_type=p_type, callback=on_popup_closed, color=border_color)



    def start_move(self, event):
        widget_class = event.widget.winfo_class()
        if widget_class in ('Button', 'Scrollbar', 'TScrollbar', 'Canvas'):
            if hasattr(self, '_x'):
                delattr(self, '_x')
            if hasattr(self, '_y'):
                delattr(self, '_y')
            return
            
        self._x = event.x
        self._y = event.y

    def do_move(self, event):
        if not hasattr(self, '_x') or not hasattr(self, '_y'):
            return
            
        x = event.x_root - self._x
        y = event.y_root - self._y
        self.root.geometry(f"+{x}+{y}")

    def on_abandon_click(self):
        if self.network:
            self.network.send_msg("QUIT_MATCH")
            
        self.current_match_id = None
        self.my_game = False
        self.reset_board()
        self.show_lobby_screen()