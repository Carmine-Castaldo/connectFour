import tkinter as tk
from UI.components import config as cfg
class MyButton(tk.Button):
    def __init__(self, parent, text, command=None, variant="neon", size="large", **kwargs):
        if variant == "pink":
            self.main_color = cfg.COLOR_TEXT_PINK
        elif variant == "muted":
            self.main_color = cfg.COLOR_TEXT_MUTED
        else:
            self.main_color = cfg.COLOR_TEXT_NEON

        font = cfg.FONT_BTN_LARGE if size == "large" else cfg.FONT_BTN_SMALL
    
        super().__init__(
            parent, 
            text=text, 
            font=font, 
            bg=cfg.COLOR_BG, 
            fg=self.main_color, 
            activebackground=self.main_color,
            activeforeground=cfg.COLOR_BG, 
            bd=2, 
            relief="flat", 
            highlightbackground=self.main_color,
            command=command,
            **kwargs
        )