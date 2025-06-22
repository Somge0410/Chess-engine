ROW_TO_ALGEBRAIC={0:'8', 1:'7', 2:'6', 3:'5', 4:'4', 5:'3', 6:'2', 7:'1'}
COL_TO_ALGEBRAIC={0 :'a', 1:'b', 2:'c',3:'d',4:'e',5:'f',6:'g',7:'h'}
def coord_to_algebraic(r,c):
        files ="abcdefgh"
        ranks="87654321"
        return f"{files[c]}{ranks[r]}"

class Move:
    def __init__(self, position, start_row,start_col,end_row,end_col,\
                  is_castle=False,is_en_passant=False, promotion_piece=None):
        self.start_row=start_row
        self.start_col=start_col
        self.end_row=end_row
        self.end_col=end_col
        self.piece_moved=position.board[start_row][start_col]
        self.piece_captured=None if position.board[end_row][end_col]=='.' else position.board[end_row][end_col]
        self.is_castle=is_castle
        self.is_en_passant=is_en_passant
        self.promotion_piece=promotion_piece
        self.old_castling_rights=position.castling_rights
        self.old_en_passant_rights=position.en_passant
        self.row_direction=1 if end_row-start_row>=0 else -1
        self.col_direction=1 if end_col-start_col>=0 else -1
    def get_string(self):
        return f"{self.piece_moved}"+COL_TO_ALGEBRAIC[self.end_col]+ROW_TO_ALGEBRAIC[self.end_row]
    def is_double_p_move(self):
        if self.piece_moved.upper()=='P' and abs(self.start_row-self.end_row)==2:
            return True
        else:
            return False
    def __eq__(self,other):
        if not isinstance(other,Move):
            return False
        return self.start_row == other.start_row and \
                self.start_col==other.start_col and \
                self.end_row == other.end_row and \
                self.end_col == other.end_col and\
                self.promotion_piece== other.promotion_piece
   
    
    def to_san(self):
        if self.is_castle:
            return "0-0" if self.end_col==6 else "0-0-0"
        piece_symbol=self.piece_moved.upper()
        if piece_symbol=='P':
            piece_symbol=''
        capture_symbol='x' if self.piece_captured else ''
        if piece_symbol=="" and capture_symbol=='x':
            piece_symbol=coord_to_algebraic(self.start_row,self.start_col)[0]
        dest_square =coord_to_algebraic(self.end_row,self.end_col)
        promotion_str=f"={self.promotion_piece}" if self.promotion_piece else ""

        return f"{piece_symbol}{capture_symbol}{dest_square}{promotion_str}"
