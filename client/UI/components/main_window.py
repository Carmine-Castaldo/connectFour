import tkinter as tk
from tkinter import ttk
from UI.components import config as cfg

class MainWindow(tk.Tk):
    
    def __init__(self, on_close_callback):
        super().__init__()
        
        self.title(cfg.WINDOW_TITLE)
        self.configure(bg=cfg.COLOR_BG)
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", on_close_callback)

        self.overrideredirect(True)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.setup_geometry()
        self.setup_styles()

        self.main_container = tk.Frame(
            self, 
            bg=cfg.COLOR_BG, 
            highlightbackground=cfg.COLOR_TEXT_NEON,
            highlightcolor=cfg.COLOR_TEXT_NEON, 
            highlightthickness=5,
            bd=0
        )
        self.main_container.grid(row=0, column=0, sticky="nsew")

        self.bind("<Button-1>", self.start_move)
        self.bind("<B1-Motion>", self.do_move)

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('default')
        style.configure(
            "Custom.Vertical.TScrollbar",
            background=cfg.COLOR_BG,        
            troughcolor=cfg.COLOR_BG,       
            bordercolor=cfg.COLOR_BG,       
            arrowcolor=cfg.COLOR_TEXT_NEON 
        )
        style.map(
            "Custom.Vertical.TScrollbar",
            background=[('active', cfg.COLOR_TEXT_PINK)]
        )

    def start_move(self, event):
        widget_class = event.widget.winfo_class()
        if widget_class in ('Button', 'Scrollbar', 'TScrollbar', 'Canvas'):
            if hasattr(self, '_x'): delattr(self, '_x')
            if hasattr(self, '_y'): delattr(self, '_y')
            return
        self._x = event.x
        self._y = event.y

    def do_move(self, event):
        if not hasattr(self, '_x') or not hasattr(self, '_y'):
            return
        x = event.x_root - self._x
        y = event.y_root - self._y
        self.geometry(f"+{x}+{y}")

    def setup_geometry(self):
        self.minsize(1000, 900)
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        w = min(int(screen_width * 0.8), 1020)
        h = min(int(screen_height * 0.9), 980)
        x = (screen_width - w) // 2
        y = max(0, (screen_height - h) // 2)
        
        self.geometry(f"{w}x{h}+{x}+{y}")