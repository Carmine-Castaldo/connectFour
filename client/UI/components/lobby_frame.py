import tkinter as tk
from tkinter import ttk
from UI.components import config as cfg
from UI.components.match_card import MatchCard  
from UI.components.button import MyButton 

class LobbyFrame(tk.Frame):
    def __init__(self, parent, known_matches, on_create_callback, on_exit_callback, on_join_callback):
        super().__init__(parent, bg=cfg.COLOR_BG)
        
        self.known_matches = known_matches
        self.on_create = on_create_callback
        self.on_exit = on_exit_callback
        self.on_join = on_join_callback
        self.match_cards = {}

        self.setup_ui()

    def setup_ui(self):
        title_label = tk.Label(self, text=cfg.TXT_TITLE, font=cfg.FONT_TITLE, fg=cfg.COLOR_TEXT_PINK, bg=cfg.COLOR_BG)
        title_label.pack(pady=(10, 15))
        
        self.rooms_outer = tk.LabelFrame(self, text="  ACTIVE LOBBIES  ", font=cfg.FONT_LABEL_MEDIUM, 
                                         fg=cfg.COLOR_TEXT_NEON, bg=cfg.COLOR_BG, bd=0, relief="flat")
        self.rooms_outer.pack(fill="both", expand=True, padx=5, pady=10)
        
        self.rooms_outer.columnconfigure(0, weight=1)
        self.rooms_outer.columnconfigure(1, weight=0)
        self.rooms_outer.rowconfigure(0, weight=1)
        
        self.lobby_canvas = tk.Canvas(self.rooms_outer, bg=cfg.COLOR_BG, highlightthickness=0)   
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

        self.render_matches()
        
        self.status_label = tk.Label(self, text=cfg.TXT_LOBBY_STATUS_DEFAULT, font=cfg.FONT_LABEL_SMALL, fg=cfg.COLOR_TEXT_MUTED, bg=cfg.COLOR_BG)
        self.status_label.pack(pady=10)
        
        btn_container = tk.Frame(self, bg=cfg.COLOR_BG)
        btn_container.pack(pady=(5, 15))
        
        btn_create = MyButton(btn_container, text=cfg.TXT_CREATE_BTN, variant="neon", command=self.on_create)
        btn_create.pack(side="left", padx=20, ipadx=15, ipady=5)
        
        btn_exit = MyButton(btn_container, text="EXIT", variant="pink", command=self.on_exit)
        btn_exit.pack(side="left", padx=20, ipadx=25, ipady=5)

    def render_matches(self):
        for widget in self.rooms_container.winfo_children():
            widget.destroy()
        self.match_cards.clear()

        for m_id, status in reversed(list(self.known_matches.items())):
            self.match_cards[m_id] = MatchCard(self.rooms_container, m_id, status, self.on_join)

    def update_status(self, new_text, color=cfg.COLOR_TEXT_NEON):
        if hasattr(self, 'status_label'):
            self.status_label.config(text=new_text, fg=color)