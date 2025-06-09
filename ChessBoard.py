from constants import STARTING_FEN
from move import Move
class ChessBoard:
    def __init__(self,fen=STARTING_FEN):
        self.fen = fen
        self._parse_fen()

    def _parse_fen(self):
       
        # Teile den FEN-String in seine 6 Bestandteile auf
        fen_parts = self.fen.split()

        # 1. Teil: Die Figurenpositionen
        self.board = []
        board_rows = fen_parts[0].split('/')
        for row_str in board_rows:
            new_row = []
            for char in row_str:
                if char.isdigit():
                    new_row.extend(['.'] * int(char))
                else:
                    new_row.append(char)
            self.board.append(new_row)

        # 2. Teil: Wer ist am Zug
        self.turn = fen_parts[1]

        # 3. Teil: Rochaderechte
        self.castling_rights=['K' in fen_parts[2],'Q' in fen_parts[2],'k' in fen_parts[2], 'q' in fen_parts[2]]
        if len(fen_parts[3])==1:
            self.en_passant = [-1,-1]
        else: 
            self.en_passant=[ord(fen_parts[3][0])-ord('a'), fen_parts[3][1]-1]

        self.halfmove_clock = int(fen_parts[4])
        self.fullmove_number = int(fen_parts[5])

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
            
            print(("  "+" ".join(self.board[k])))
        print("-------------------")
        print("  a b c d e f g h\n")

    def get_FEN(self):
        fen=''
        for i, row in enumerate(self.board):
            count=0
            for piece in row:
                if piece=='.':
                    count=count+1
                    continue
                if count>0:
                    fen=fen+str(count)+piece
                    count=0
                else:
                    fen=fen+piece
            if count>0:
                fen=fen+str(count)+'/'
            else:       
                 if i!= 7:
                    fen=fen+'/'    
        fen=fen+' '
        fen=fen+ self.turn
        fen=fen+' '
        if self.castling_rights[0]:
            fen=fen+'K'   
        if self.castling_rights[1]:
            fen=fen+'Q'     
        if self.castling_rights[2]:
            fen=fen+'k'
        if self.castling_rights[3]:
            fen=fen+'q'
        fen=fen+' '
        fen=fen+str(self.halfmove_clock)
        fen=fen+' '
        fen=fen+str(self.fullmove_number)
        return fen            

    def get_legal_moves(self):
        moves=[]
        for row in range(8):
            for col in range(8):
                piece=self.board[row][col]
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
                if piece=='R' or piece=='r':
                    self._generate_rook_moves(moves,row,col,piece)
                if piece=='B' or piece=='b':
                    self._generate_bishop_moves(moves,row,col,piece)
                if piece=='K' or piece=='k':
                    self._generate_king_moves(moves,row,col,piece)
        return moves
  
    def _generate_pawn_moves(self,moves,row,col, piece):
        is_white=piece.isupper()
        direction = -1 if is_white else 1
        if row+direction<0:
            return moves
        try:
            if self.board[row+direction][col]=='.':
                moves.append(Move(row,col,row+direction,col,piece))
                try:
                    if row==3.5-2.5*direction and self.board[row+2*direction][col]=='.':
                        moves.append(Move(row,col,row+2*direction,col,piece))
                except IndexError:
                    pass
        except IndexError:
            pass
        try:
            if col-1>=0 and self.board[row+direction][col-1].isupper()!=is_white and self.board[row+direction][col-1]!='.':
                moves.append(Move(row,col,row+direction,col-1,piece,self.board[row+direction][col-1]))
        except IndexError:
            pass
        try:
            if self.board[row+direction][col+1].isupper()!=is_white and self.board[row+direction][col+1]!='.':
                moves.append(Move(row,col,row+direction,col+1,self.board[row+direction][col+1]))
        except IndexError:
            pass
        #If en passant is possible
        if [row+direction,col+1]==self.en_passant:
            moves.append(Move(row,col,row+direction,col+1,piece,self.board[row][col+1]))
        if [row+direction,col-1]==self.en_passant:
            moves.append(Move(row,col,row+direction,col-1,piece,self.board[row,col-1]))
    def _generate_knight_moves(self,moves,row,col,piece):
        is_white=piece.isupper()
        l=[[1,2],[2,1],[2,-1],[1,-2],[-1,-2],[-2,-1],[-2,1],[-1,2]]
        for coord in l:
            if 0<=row+coord[0]<=7 and 0<=col+coord[1]<=7 and self.board[row+coord[0]][col+coord[1]]=='.':
                    moves.append(Move(row,col,row+coord[0],col+coord[1],piece))
                    continue
            if 0<=row+coord[0]<=7 and 0<=col+coord[1]<=7 and self.board[row+coord[0]][col+coord[1]].isupper()!=is_white:
                 moves.append(Move(row,col,row+coord[0],col+coord[1],piece,self.board[row+coord[0]][col+coord[1]]))
            
            
    def _generate_rook_moves(self,moves,row,col,piece):
        is_white=piece.isupper()
        directons=[[0,1],[1,0],[0,-1],[-1,0]]
        for d in directons:
            for i in range(1,8):
                r,c=row+i*d[0], col+i*d[1]
                if not (0<=r<=7 and 0<=c<=7):
                    break
                target_field=self.board[r][c]
                if target_field=='.':
                     moves.append(Move(row,col,r,c,piece))
                     continue
                is_target_white=target_field.isupper()
                if is_white !=is_target_white:
                     moves.append(Move(row,col,r,c,piece,target_field))
                break
    def _generate_bishop_moves(self,moves,row,col,piece):
        is_white=piece.isupper()
        directions=[[1,1],[1,-1],[-1,-1],[-1,1]]
        for d in directions:
            for i in range(1,8):
                r,c=row+i*d[0], col+i*d[1]
                if not (0<=r<=7 and 0<=c<=7):
                    break
                target_field=self.board[r][c]
                if target_field=='.':
                     moves.append(Move(row,col,r,c,piece))
                     continue
                is_target_white=target_field.isupper()
                if is_white !=is_target_white:
                     moves.append(Move(row,col,r,c,piece,target_field))
                break
    def _generate_queen_moves(self,moves,row,col,piece):
        self._generate_bishop_moves(moves,row,col,piece)
        self._generate_rook_moves(moves,row,col,piece)
    def _generate_king_moves(self,moves,row,col,piece):
        is_white=piece.isupper()
        directions=[[0,1],[1,1],[1,0],[1,-1],[0,-1],[-1,-1],[-1,0],[-1,1]]
        for d in directions:
            if 0<=row+d[0]<=7 and 0<=col+d[1]<=7:
                target_field=self.board[row+d[0]][col+d[1]]
                if target_field=='.':
                    moves.append(Move(row,col,row+d[0],col+d[1],piece))
                    continue
                elif target_field.isupper()!=is_white:
                    moves.append(Move(row,col,row+d[0],col+d[1],piece,target_field))
        if is_white and self.castling_rights[0]:
            if self.board[row][col+1]=='.' and self.board[row][col+2]=='.':
                moves.append(Move(row,col,row,col+2,piece,is_castle=True))
        if is_white and self.castling_rights[1]:
            if self.board[row][col-1]=='.' and self.board[row][col-2]=='.' and self.board[row][col-3]=='.':
                moves.append(Move(row,col,row,col-2,piece,is_castle=True))

    def make_move(self,move: Move):
        piece=self.board[move.start_row][move.start_col]
        self.board[move.start_row][move.start_col]='.'
        self.board[move.end_row][move.end_col]=piece
        
        if self.turn=='w':
            self.turn='b'
        else:
            self.turn='w'
        self.fen=self.get_FEN()

