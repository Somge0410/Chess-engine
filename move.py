ROW_TO_ALGEBRAIC={0:'8', 1:'7', 2:'6', 3:'5', 4:'4', 5:'3', 6:'2', 7:'1'}
COL_TO_ALGEBRAIC={0 :'a', 1:'b', 2:'c',3:'d',4:'e',5:'f',6:'g',7:'h'}
def coord_to_algebraic(r,c):
        files ="abcdefgh"
        ranks="87654321"
        return f"{files[c]}{ranks[r]}"
WHITE, BLACK=0,1
class Move:
    def __init__(self, position, from_square, to_square,\
                  is_castle=False,is_en_passant=False, promotion_piece=None):
        self.from_square=from_square
        self.to_square=to_square
        self.piece_moved=position.get_piece_on_square(from_square)
        piece_on_square=position.get_piece_on_square(to_square)
        self.piece_captured=None if piece_on_square=='.' else piece_on_square
        self.is_castle=is_castle
        self.is_en_passant=is_en_passant
        self.promotion_piece=promotion_piece
        self.old_castling_rights=position.castling_rights
        self.old_en_passant_rights=position.en_passant_rights
        self.color= WHITE if self.piece_moved.isupper() else BLACK
        self.capture_color=WHITE if self.color==BLACK else BLACK
    def is_double_p_move(self):
        if self.piece_moved.upper()=='P' and abs(self.to_square-self.from_square)==16:
            return True
        else:
            return False
    def __eq__(self,other):
        if not isinstance(other,Move):
            return False
        return self.from_square == other.from_square and \
                self.to_square == other.to_square and \
                self.piece_moved==other.piece_moved and \
                self.promotion_piece== other.promotion_piece
    def __hash__(self):
        # Create a tuple of the essential, immutable properties of the move and hash it.
        return hash((self.from_square, self.to_square, self.promotion_piece))
    
    @property
    def piece_moved_type(self):
        list=['P','N','B','R','Q','K','p','n','b','r','q','k']
        return list.index(self.piece_moved)
def parse_move(move_str:str,position):
    move_list=position.get_legal_moves()
    for move in move_list:
        if move_str==position.to_san(move,move_list):
            return move
    return None