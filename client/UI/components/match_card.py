import tkinter as tk
from UI.components import config as cfg
from UI.components.button import MyButton

class MatchCard:
    def __init__(self, parent, match_id, status, join_callback):
        self.match_id = match_id
        self.join_callback = join_callback

        self.frame = tk.Frame(parent, bg=cfg.COLOR_BG_BOARD, bd=1, relief="flat", highlightbackground=cfg.COLOR_CABINET, highlightthickness=1)
        self.frame.pack(fill="x", padx=15, pady=8)
        
        self.lbl_id = tk.Label(self.frame, text=f"ROOM #{match_id}", font=cfg.FONT_LABEL_MEDIUM, fg=cfg.COLOR_TEXT_WHITE, bg=cfg.COLOR_BG_BOARD)
        self.lbl_id.pack(side="left", padx=15, pady=10)
        
        self.lbl_status = tk.Label(self.frame, font=cfg.FONT_LABEL_SMALL, bg=cfg.COLOR_BG_BOARD)
        self.lbl_status.pack(side="left", padx=20, pady=10)
        
        self.btn_join = MyButton(self.frame, text="JOIN", variant="NEON", size="SMALL", command=lambda: self.join_callback(self.match_id))
        self.btn_join.pack(side="right", padx=15, pady=10)
                
        self.update(status)

    def update(self, status):
        if status == "AVAILABLE":
            self.lbl_status.config(text="AVAILABLE", fg=cfg.COLOR_TEXT_NEON, bg=cfg.COLOR_BG_BOARD)
            self.btn_join.config(state="normal", text="JOIN", fg=cfg.COLOR_TEXT_NEON, bg=cfg.COLOR_BG)
            self.frame.config(bg=cfg.COLOR_BG_BOARD, highlightbackground=cfg.COLOR_CABINET)
            self.lbl_id.config(bg=cfg.COLOR_BG_BOARD, fg=cfg.COLOR_TEXT_WHITE)
            
        elif status == "CONNECTING":  
            self.lbl_status.config(text="CONNECTING...", fg=cfg.COLOR_TEXT_PINK, bg=cfg.COLOR_BG_BOARD)
            self.btn_join.config(state="disabled", text="WAIT", fg=cfg.COLOR_TEXT_MUTED, bg=cfg.COLOR_BG)
            self.frame.config(bg=cfg.COLOR_BG_BOARD, highlightbackground=cfg.COLOR_CABINET)
            self.lbl_id.config(bg=cfg.COLOR_BG_BOARD, fg=cfg.COLOR_TEXT_WHITE)
            
        elif status == "PLAYING":
            self.frame.config(bg=cfg.COLOR_BG, highlightbackground=cfg.COLOR_TEXT_MUTED)
            self.lbl_id.config(bg=cfg.COLOR_BG, fg=cfg.COLOR_TEXT_MUTED)
            self.lbl_status.config(text="PLAYING", fg=cfg.COLOR_TEXT_PINK, bg=cfg.COLOR_BG)
            self.btn_join.config(state="disabled", text="JOIN", fg=cfg.COLOR_TEXT_MUTED, bg=cfg.COLOR_BG)
            
        elif status == "TERMINATED":
            self.frame.config(bg=cfg.COLOR_BG, highlightbackground=cfg.COLOR_TEXT_MUTED)
            self.lbl_id.config(bg=cfg.COLOR_BG, fg=cfg.COLOR_TEXT_MUTED)
            self.lbl_status.config(text="TERMINATED", fg=cfg.COLOR_TEXT_MUTED, bg=cfg.COLOR_BG)
            self.btn_join.config(state="disabled", text="JOIN", fg=cfg.COLOR_TEXT_MUTED, bg=cfg.COLOR_BG)


    def check_exists(self):
        return self.frame.winfo_exists()
        
    def destroy(self):
        self.frame.destroy()