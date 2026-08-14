class Board:
    def __init__(self, rows=6, cols=7):
        self.rows = rows
        self.cols = cols
        self.grid = [[0 for _ in range(cols)]for _ in range(rows)]
    def reset(self):
        self.grid = [[0 for _ in range(self.cols)]for _ in range(self.rows)]

    def update(self, row, col, player):
        self.grid[row][col] = player
        
    def get_cell(self, row, col):
        return self.grid[row][col]

