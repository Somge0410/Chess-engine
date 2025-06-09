class Move:
    def __init__(self, start_row,start_col,end_row,end_col,piece_moved,piece_captured=None, is_castle=False):
        self.start_row=start_row
        self.start_col=start_col
        self.end_row=end_row
        self.end_col=end_col
        self.piece_moved=piece_moved
        self.piece_captured=piece_captured
        self.is_castle=is_castle
    def get_string(self):
        return f"Move {self.piece_moved} from ({self.start_row},{self.start_col}) to (({self.end_row},{self.end_col})"