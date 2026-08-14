import tkinter as tk
from UI.components import config as cfg

class Popup:
    def __init__(self, parent, title, message, popup_type="ok", callback=None, color=cfg.COLOR_TEXT_PINK):
        self.top = tk.Toplevel(parent)
        self.top.configure(bg=cfg.COLOR_BG)
        self.top.overrideredirect(True)
        self.callback = callback
        self.main_frame = tk.Frame(
            self.top, 
            bg=cfg.COLOR_BG, 
            highlightbackground=color, 
            highlightcolor=color, 
            highlightthickness=4                     
        )
        self.main_frame.pack(fill="both", expand=True)
        
        self._build_ui(title, message, popup_type)
        
        self.top.update_idletasks() 
        
        width = self.top.winfo_reqwidth()
        height = self.top.winfo_reqheight()
        
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (width // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (height // 2)
        
        self.top.geometry(f"+{x}+{y}")
        self.top.transient(parent)
        self.top.grab_set()
        
    def _build_ui(self, title, message, popup_type):
        lbl_title = tk.Label(
            self.main_frame,
            text=title.upper(),
            font=cfg.FONT_LABEL_LARGE, 
            fg=cfg.COLOR_TEXT_NEON,
            bg=cfg.COLOR_BG
        )
        lbl_title.pack(pady=(20, 10))
        
        lbl_msg = tk.Label(
            self.main_frame, 
            text=message, 
            font=cfg.FONT_LABEL_MEDIUM, 
            fg=cfg.COLOR_TEXT_WHITE, 
            bg=cfg.COLOR_BG,
            justify="center"
        )
        lbl_msg.pack(pady=(10, 30), padx=40)
        btn_frame = tk.Frame(self.main_frame, bg=cfg.COLOR_BG)
        btn_frame.pack(pady=(0, 25))
        
        if popup_type == "yesno":
            btn_yes = tk.Button(
                btn_frame, text="YES", font=cfg.FONT_BTN_LARGE, 
                bg=cfg.COLOR_BG, fg=cfg.COLOR_TEXT_PINK, 
                activebackground=cfg.COLOR_BTN_ACTIVE, activeforeground=cfg.COLOR_BG, 
                bd=2, relief="flat", highlightbackground=cfg.COLOR_BTN_BORDER,
                command=lambda: self._close(True)
            )
            btn_yes.pack(side="left", padx=20)
            
            btn_no = tk.Button(
                btn_frame, text="NO", font=cfg.FONT_BTN_LARGE, 
                bg=cfg.COLOR_BG, fg=cfg.COLOR_TEXT_NEON, 
                activebackground=cfg.COLOR_BTN_ACTIVE, activeforeground=cfg.COLOR_BG, 
                bd=2, relief="flat", highlightbackground=cfg.COLOR_BTN_BORDER,
                command=lambda: self._close(False)
            )
            btn_no.pack(side="right", padx=20)
            
        else:
            btn_ok = tk.Button(
                btn_frame, text="OK", font=cfg.FONT_BTN_LARGE, 
                bg=cfg.COLOR_BG, fg=cfg.COLOR_TEXT_PINK, 
                activebackground=cfg.COLOR_BTN_ACTIVE, activeforeground=cfg.COLOR_BG, 
                bd=2, relief="flat", highlightbackground=cfg.COLOR_BTN_BORDER,
                command=lambda: self._close(True)
            )
            btn_ok.pack()

    def _close(self, result):
        self.top.grab_release() 
        self.top.destroy()
        if self.callback:
            self.callback(result)