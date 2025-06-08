from constants import STARTING_FEN

class ChessPosition:
    def __init__(self,fen=STARTING_FEN):
        if not ChessPosition.is_valid_pos(fen):
            raise ValueError(f"Der bereitgestellte String ist keine gültige FEN-Notation: '{fen}'")
        self.pos=[[fen[i*8+k] for k in range(8)] for i in range(8)]
        self.turn=fen[64]
        self.castling_rights=fen[65:69]
        h=int(fen[69:71])
        self.enpassant=[(h-(h %8))/8, h%8]
        self.move_number=fen[70]
        self.halfmove_count=fen[72]
        #self.pos_string=self.pos+self.turn+self.castling_rights+str(self.enpassant)+self.move_number+self.halfmove_count

    
    @staticmethod
    def is_valid_pos(fen_string):
        try:
            if len(fen_string)< len(STARTING_FEN):
                return False
        except( ValueError, IndexError):
            return False
        return True


    def display(self):
        print("\n--- Aktuelles Spielfeld ---")
        print(f"Am Zug: {'Weiß' if self.turn == 'w' else 'Schwarz'}")
        print("  a b c d e f g h")
        print("-------------------")
        for k in range(8):
            
            print(("  "+" ".join(self.pos[7-k])))
        print("-------------------")
        print("  a b c d e f g h\n")

    def get_legal_moves(self):
        moves=[]
        for row in range(8):
            for col in range(8):
                piece=self.pos[row][col]
                if piece=='.':
                    continue
                is_white_piece=piece.isupper()
                if (self.turn=='w' and not is_white_piece) or \
                    (self.turn=='b' and is_white_piece):
                    continue
                if piece=='P' or piece=='p':
                     self._generate_pawn_moves(moves,row,col,piece)
                if piece=='N' or piece=='n':
                    self._generate_knight_moves(moves,row,col,piece)
        return moves
  
    def _generate_pawn_moves(self,moves,row,col, piece):
        is_white=piece.isupper()
        direction = 1 if is_white else -1
        if row+direction<0:
            return moves
        try:
            if self.pos[row+direction][col]=='.':
                moves.append(f"({row},{col})-({row+direction},{col})")
                try:
                    if row==3.5-2.5*direction and self.pos[row+2*direction][col]=='.':
                        moves.append(f"({row},{col})-({row+2*direction},{col})")
                except IndexError:
                    pass
        except IndexError:
            pass
        try:
            if col-1>=0 and self.pos[row+direction][col-1].isupper()!=is_white and self.pos[row+direction][col-1]!='.':
                moves.append(f"({row},{col})-({row+direction},{col-1})")
        except IndexError:
            pass
        try:
            if self.pos[row+direction][col+1].isupper()!=is_white and self.pos[row+direction][col+1]!='.':
                moves.append(f"({row},{col})-({row+direction},{col+1})")
        except IndexError:
            pass
        #If en passant is possible
        if [row+direction,col+1]==self.enpassant:
            moves.append(f"({row},{col})-({row+direction},{col+1})")
        if [row+direction,col-1]==self.enpassant:
            moves.append(f"({row},{col})-({row+direction},{col-1})")
            
    def _generate_knight_moves(self,moves,row,col,piece):
        is_white=piece.isupper()
        l=[[1,2],[2,1],[2,-1],[1,-2],[-1,-2],[-2,-1],[-2,1],[-1,2]]
        for coord in l:
            if 0<=row+coord[0]<=7 and 0<=col+coord[1]<=7 and\
                (self.pos[row+coord[0]][col+coord[1]]=='.' or self.pos[row+coord[0]][col+coord[1]].isupper()!=is_white):
                    moves.append(f"({row},{col}),({row+coord[0]},{col+coord[1]})")
            
        
    