import tkinter as tk
from tkinter import ttk
import queue, re, os, platform
from UI.components.board import Board
from UI.components.button import MyButton
from UI.components.disc import Disc
from UI.components.main_window import MainWindow
from UI.components.popup import Popup
from UI.components.match_card import MatchCard
from UI.components.lobby_frame import LobbyFrame
from UI.components import config as cfg


class GUI:
    def __init__(self, network_controller):
        
        self.network = network_controller
        self.network.on_message_callback = self.enqueue_message
        self.gui_queue = queue.Queue()

        if hasattr(self.network, 'safe_queue'):
            while not self.network.safe_queue.empty():
                self.enqueue_message(self.network.safe_queue.get())
    
        self.my_turn = False
        self.my_game = False
        self.challenger_fd = "UNKNOWN"
        self.known_matches = {}
        self.current_match_id = None

        self.board = Board()
        self.root = MainWindow(on_close_callback=self.on_closing)
        
        self.main_container = self.root.main_container
        self.lobby_frame = None
        self.game_frame = None
        
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
            
        self.lobby_frame = LobbyFrame(
            parent=self.main_container,
            known_matches=self.known_matches,
            on_create_callback=self.on_create_click,
            on_exit_callback=self.on_closing,
            on_join_callback=self.on_join_card_click
        )
        
        self.lobby_frame.grid(row=0, column=0, sticky="nsew", padx=30, pady=20)
        self.main_container.rowconfigure(0, weight=1)
        self.main_container.columnconfigure(0, weight=1)

    def on_create_click(self):
        self.my_game=True
        if self.lobby_frame:
            self.lobby_frame.update_status(cfg.MSG_CREATING, color=cfg.COLOR_TEXT_NEON)
        self.network.create_match()

    def make_move(self, col):
        print(f"MOVE {col}")
        self.network.move(str(col)) 
        self.disable_buttons()

    def on_closing(self):
        self.network.disconnect() 
        os._exit(0)

    def on_quit_match(self):
        if self.current_match_id is not None:
            self.known_matches[self.current_match_id] = "TERMINATED"
        self.current_match_id = None
        self.network.quit() 
        self.show_lobby_screen()

    def show_game_screen(self):
        self.reset_board()
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
        self.turn_label.pack(pady=5)

        self.canvas = tk.Canvas(self.game_frame, width=980, height=840, bg=cfg.COLOR_BG_BOARD, highlightthickness=0)
        self.canvas.pack(pady=5)
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<Motion>", self.on_canvas_hover)
        self.draw_graphic_board()
        
        btn_abandon = MyButton(self.game_frame, text="ABANDON MATCH", variant="pink", command=self.on_abandon_click)
        btn_abandon.pack(pady=(5, 10), ipadx=15, ipady=3)

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
            self.board.update(row, col, player)

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
            self._handle_match_created(msg)
        elif "IS STARTING" in msg:
            self._handle_match_status(msg, "PLAYING")
        elif msg.startswith("THE GAME") and "IS OVER" in msg:
            self._handle_match_status(msg, "TERMINATED")
        elif msg in ["YOUR TURN", "WAIT TURN"]:
            self._handle_turn_change(msg == "YOUR TURN")
        elif msg.startswith("UPDATE_BOARD"):
            self._handle_board_update(msg)
        elif msg.startswith("JOIN_REQUEST"):
            self._handle_join_request(msg)
        elif msg in ["WIN", "LOSE", "DRAW", "OPPONENT_DISCONNECTED"]:
            self._handle_endgame(msg)
        elif msg in ["OPPONENT_WANTS_REMATCH", "REMATCH_START", "REMATCH_DECLINED"]:
            self._handle_rematch_events(msg)
        elif msg.startswith("ROOM"):
            self._handle_room_status(msg)
        else:
            if getattr(self, 'status_label', None) is not None:
                self.lobby_frame.update_status(msg,cfg.COLOR_TEXT_WHITE)

    def _handle_match_created(self, msg):
        match_id_list = re.findall(r'\d+', msg)
        if match_id_list:
            m_id = match_id_list[0]
            self.known_matches[m_id] = "AVAILABLE"
            
            if getattr(self, 'my_game', False) and self.current_match_id is None:
                self.current_match_id = m_id
            
            if self.lobby_frame:
                if getattr(self, 'my_game', False):
                    self.lobby_frame.update_status(
                        cfg.MSG_WAITING_OPPONENT.format(match_id=m_id), 
                        color=cfg.COLOR_TEXT_NEON
                    )
                else:
                    self.lobby_frame.update_status(
                        cfg.MSG_NEW_ROOM_AVAILABLE.format(match_id=m_id), 
                        color=cfg.COLOR_TEXT_PINK
                    )
                    self.lobby_frame.match_cards[m_id] = MatchCard(
                        self.lobby_frame.rooms_container, 
                        m_id, 
                        "AVAILABLE", 
                        self.on_join_card_click
                    )

    def _handle_match_status(self, msg, status):
        match_id_list = re.findall(r'\d+', msg)
        if not match_id_list:
            return
            
        m_id = match_id_list[0]
        self.known_matches[m_id] = status
        if self.lobby_frame:
            match_id_int = int(m_id) if m_id.isdigit() else m_id
            match_id_str = str(m_id)

            card = self.lobby_frame.match_cards.get(match_id_int) or self.lobby_frame.match_cards.get(match_id_str)
            if card:
                card.update(status)

    def _handle_turn_change(self, is_my_turn):
        self.my_turn = is_my_turn

        if self.game_frame is None:
            self.show_game_screen()
        else:
            if self.my_turn:
                self.turn_label.config(text=cfg.MSG_YOUR_TURN, fg=cfg.COLOR_TEXT_NEON)
                self.enable_buttons()
            else:
                self.turn_label.config(text=cfg.MSG_WAIT_TURN, fg=cfg.COLOR_TEXT_PINK)
                self.disable_buttons()

    def _handle_board_update(self, msg):
        self.update_board(msg) 
        self.draw_graphic_board()
        if getattr(self, 'turn_label', None) is not None:
            if self.my_turn:
                self.turn_label.config(text=cfg.MSG_YOUR_TURN, fg=cfg.COLOR_TEXT_NEON)
                self.enable_buttons()
            else:
                self.turn_label.config(text=cfg.MSG_WAIT_TURN, fg=cfg.COLOR_TEXT_PINK)
                self.disable_buttons()

    def _handle_join_request(self, msg):
        if not getattr(self, 'my_game', False):
            return
            
        parts = msg.split()
        self.challenger_fd = parts[1] if len(parts) > 1 else "UNKNOWN"

        def on_join_response(accepted):
            self.active_popup = None
            if accepted:
                self.network.accept() 
            else:
                self.network.reject() 
                if self.lobby_frame and hasattr(self.lobby_frame, 'update_status'):
                    self.lobby_frame.update_status(cfg.MSG_REJECTED, color=cfg.COLOR_TEXT_PINK)
                elif getattr(self, 'status_label', None):
                    self.status_label.config(text=cfg.MSG_REJECTED, fg=cfg.COLOR_TEXT_PINK)


        self.active_popup = Popup(
            self.root, 
            cfg.POPUP_TITLE_CHALLENGE, 
            cfg.POPUP_MSG_CHALLENGE.format(fd=self.challenger_fd),
            popup_type="yesno", 
            callback=on_join_response
        )

    def _handle_endgame(self, msg):
        if getattr(self, 'active_popup', None) is not None:
            try:
                self.active_popup.top.grab_release()
                self.active_popup.top.destroy()
            except Exception:
                pass
            self.active_popup = None
        self.disable_buttons()
        self.root.after(200, lambda: self.show_endgame_popup(msg))

    def _handle_rematch_events(self, msg):
        if msg == "OPPONENT_WANTS_REMATCH":
            if getattr(self, 'turn_label', None) is not None:
                self.turn_label.config(text=cfg.MSG_OPPONENT_ASK_REMATCH, fg=cfg.COLOR_TEXT_NEON)
                
        elif msg == "REMATCH_START":
            self.reset_board()
            self.draw_graphic_board()
            if getattr(self, 'turn_label', None) is not None:
                self.turn_label.config(text=cfg.MSG_REMATCH_ACCEPTED, fg=cfg.COLOR_TEXT_NEON)
                
        elif msg == "REMATCH_DECLINED":
    
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

    def _handle_room_status(self, msg):
        parts = msg.split()
        if len(parts) < 3:
            return

        m_id = parts[1]
        status = parts[2]
        
        self.known_matches[m_id] = status

        if self.lobby_frame:
            match_id_int = int(m_id) if m_id.isdigit() else m_id
            match_id_str = str(m_id)

            card_exists = (match_id_int in self.lobby_frame.match_cards) or (match_id_str in self.lobby_frame.match_cards)

            if card_exists:
                card = self.lobby_frame.match_cards.get(match_id_int) or self.lobby_frame.match_cards.get(match_id_str)
                if card:
                    card.update(status)
            else:

                self.lobby_frame.match_cards[m_id] = MatchCard(
                    self.lobby_frame.rooms_container, 
                    m_id, 
                    status, 
                    self.on_join_card_click
                )

    def start(self):
        self.root.mainloop()

    def reset_board(self):
        self.board.reset()

    def on_join_card_click(self, match_id):
        self.reset_board()
        self.my_game = False
        
        if self.lobby_frame:
            self.lobby_frame.update_status(
                cfg.MSG_JOINING.format(match_id=match_id), 
                color=cfg.COLOR_TEXT_PINK
            )
            
        self.network.join_match(match_id)

    def update_match_card(self, msg):
        parts = msg.strip().split()
        if len(parts) < 2:
            return
            
        match_id_str = parts[1]
        try:
            match_id_int = int(match_id_str)
        except ValueError:
            match_id_int = match_id_str

        card = self.match_cards.get(match_id_int) or self.match_cards.get(match_id_str)
        
        if card:
            if not card.check_exists():
                self.match_cards.pop(match_id_int, None)
                self.match_cards.pop(match_id_str, None)
                return
        
            msg_upper = msg.upper()
            if "PLAYING" in msg_upper or "STARTING" in msg_upper:
                card.update("PLAYING")
            elif "TERMINATED" in msg_upper or "OVER" in msg_upper:
                card.update("TERMINATED")
            elif "AVAILABLE" in msg_upper:
                card.update("AVAILABLE")
            else:
                card.update("CONNECTING")

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
                col * 140 + 4, 2,
                (col + 1) * 140 - 6, 810, 
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
        if getattr(self, 'active_popup', None) is not None:
            try:
                self.active_popup.top.grab_release()
                self.active_popup.top.destroy()
            except Exception:
                pass
            self.active_popup = None

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

    def on_abandon_click(self):
        if self.network:
            self.network.send_msg("QUIT_MATCH")
        self.current_match_id = None
        self.my_game = False
        self.reset_board()
        self.show_lobby_screen()
