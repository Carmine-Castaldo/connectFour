from UI.components import config as cfg

class Disc:
    def __init__(self, canvas, row, col):
        self.canvas = canvas
        self.row = row
        self.col = col
        self.center_x = col * cfg.CELL_WIDTH + (cfg.CELL_WIDTH / 2)
        self.center_y = row * cfg.CELL_HEIGHT + (cfg.CELL_HEIGHT / 2)
        self.x1 = self.center_x - (cfg.DIAMETER / 2)
        self.y1 = self.center_y - (cfg.DIAMETER / 2)
        self.x2 = self.center_x + (cfg.DIAMETER / 2)
        self.y2 = self.center_y + (cfg.DIAMETER / 2)
        
    def draw(self, player):
        if player == 0:
            self.canvas.create_oval(
                self.x1, self.y1, self.x2, self.y2, 
                fill=cfg.COLOR_CIRCLE_EMPTY, 
                outline=cfg.COLOR_CABINET, 
                width=4
            )
            return
        if player == 1:
            base_color = cfg.COLOR_TEXT_PINK
            dark_color = getattr(cfg, 'COLOR_P1_DARK', "#990033")
            light_color = "#ff80aa" 
        else:
            base_color = cfg.COLOR_TEXT_NEON
            dark_color = getattr(cfg, 'COLOR_P2_DARK', "#006699")
            light_color = "#80ffff" 

        self.canvas.create_oval(
            self.x1, self.y1, self.x2, self.y2, 
            fill=base_color, outline=base_color, width=4
        )
        
        self.canvas.create_oval(self.x1 + 4, self.y1 + 4, self.x2 + 2, self.y2 + 2, fill="#05050d", outline="")
        self.canvas.create_oval(self.x1, self.y1, self.x2, self.y2, fill=dark_color, outline=dark_color)
        self.canvas.create_oval(self.x1 + 3, self.y1 + 3, self.x2 - 3, self.y2 - 3, fill=base_color, outline="")

        r_val_1 = cfg.DIAMETER * 0.12
        self.canvas.create_oval(self.x1 + r_val_1, self.y1 + r_val_1, self.x2 - r_val_1, self.y2 - r_val_1, fill=dark_color, outline="")
        
        r_val_2 = cfg.DIAMETER * 0.20
        self.canvas.create_oval(self.x1 + r_val_2, self.y1 + r_val_2, self.x2 - r_val_2, self.y2 - r_val_2, fill=base_color, outline="")
        
        hl1_w = cfg.DIAMETER * 0.26
        hl1_h = cfg.DIAMETER * 0.16
        hx1 = self.center_x - (cfg.DIAMETER * 0.22) - (hl1_w / 2)
        hy1 = self.center_y - (cfg.DIAMETER * 0.24) - (hl1_h / 2)
        self.canvas.create_oval(hx1, hy1, hx1 + hl1_w, hy1 + hl1_h, fill=cfg.COLOR_TEXT_WHITE, outline="")
        
        hl2_size = cfg.DIAMETER * 0.10
        bx1 = self.center_x + (cfg.DIAMETER * 0.22) - (hl2_size / 2)
        by1 = self.center_y + (cfg.DIAMETER * 0.22) - (hl2_size / 2)
        self.canvas.create_oval(bx1, by1, bx1 + hl2_size, by1 + hl2_size, fill=light_color, outline="")


    
