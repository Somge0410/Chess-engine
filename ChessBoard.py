from constants import STARTING_FEN
from move import Move
from evaluation import PIECE_VALUES, get_game_phase_percentage, get_positional_score
class ChessBoard:
    def __init__(self,hasher,fen=STARTING_FEN):
        self.fen = fen
        self.hasher=hasher
        self._parse_fen()
        self.zobrist_hash=self.hasher.calculate_hash(self)
        self.material_score=0
        self.pst_score=0
        #self._initialize_scores()
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
        self.castling_rights=fen_parts[2]
        if len(fen_parts[3])==1:
            self.en_passant = None
        else: 
            self.en_passant=(7- int(fen_parts[3][1])+1,ord(fen_parts[3][0])-ord('a'))
        self.halfmove_clock = int(fen_parts[4])
        self.fullmove_number = int(fen_parts[5])
        self.white_king_pos=self.piece_index('K')
        self.black_king_pos=self.piece_index('k')
    def _initialize_scores(self):
        phase=get_game_phase_percentage(self)
        for r in range(8):
            for c in range(8):
                piece=self.board[r][c]
                if piece!='.':
                    self.material_score+=PIECE_VALUES[piece]
                    self.pst_score+=get_positional_score(piece,r,c,phase)

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
        fen=fen+self.castling_rights
        fen=fen+' '
        fen=fen+str(self.halfmove_clock)
        fen=fen+' '
        fen=fen+str(self.fullmove_number)
        return fen            

    def get_pseudo_legal_moves(self):
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
                     self._generate_pawn_moves(moves,row,col)
                if piece=='N' or piece=='n':
                    self._generate_knight_moves(moves,row,col,piece)
                if piece=='R' or piece=='r':
                    self._generate_rook_moves(moves,row,col,piece)
                if piece=='B' or piece=='b':
                    self._generate_bishop_moves(moves,row,col,piece)
                if piece=='K' or piece=='k':
                    self._generate_king_moves(moves,row,col,piece)
                if piece.upper()=='Q':
                    self._generate_queen_moves(moves,row,col,piece)
        return moves
    def get_legal_moves(self):
        pseudo_legal_moves=self.get_pseudo_legal_moves()
        legal_moves_unfiltered=[]
        king='K' if self.turn=='w' else 'k'
        for move in pseudo_legal_moves:
            self.make_move(move)
            king_pos=self.white_king_pos if king=='K' else self.black_king_pos
            opponent_color='b' if self.turn=='b' else 'w'
            is_in_check=self.is_square_attacked(king_pos[0],king_pos[1],opponent_color)
            caslte_through_check=False
            if move.is_castle:
                direction=-1 if (move.end_col-move.start_col)>0 else 1
                if self.is_square_attacked(move.start_row,move.end_col+direction,opponent_color) or self.is_square_attacked(move.start_row,move.start_col,opponent_color):
                    caslte_through_check=True
            if not is_in_check and not caslte_through_check:
                legal_moves_unfiltered.append(move)
            self.undo_move(move)
        return legal_moves_unfiltered
    def _generate_pawn_moves(self,moves,row,col):
        is_white=self.board[row][col].isupper()
        direction = -1 if is_white else 1
        start_rank=6 if is_white else 1
        end_rank=0 if is_white else 7
        target_r,target_c=row+direction,col
        if 0<=target_r<=7 and self.board[target_r][target_c]=='.':
            if target_r==end_rank:
                for promotion_piece in "QRBN":
                    final_piece=promotion_piece if is_white else promotion_piece.lower()
                    moves.append(Move(self,row,col,target_r,target_c,promotion_piece=final_piece))
            else:
                moves.append(Move(self,row,col,target_r,target_c))
            if row==start_rank:
                target_r_double=row+2*direction
                if self.board[target_r_double][col]=='.':
                    moves.append(Move(self,row,col,target_r_double,col))
        for dc in [-1,1]:
            target_r,target_c=row+direction,col+dc
            if 0<=target_r<=7 and 0<=target_c<=7:
                target_piece=self.board[target_r][target_c]
                if target_piece!='.' and target_piece.isupper()!= is_white:
                    if target_r==end_rank:
                        for promotion_piece in "QRBN":
                            final_piece=promotion_piece if is_white else promotion_piece.lower()
                            moves.append(Move(self,row,col,target_r,target_c,promotion_piece=final_piece))
                    else: moves.append(Move(self,row,col,target_r,target_c))
        if self.en_passant!=None:
            for dc in [-1,1]:
                if row+direction==self.en_passant[0] and col+dc==self.en_passant[1]:
                    moves.append(Move(self,row,col,self.en_passant[0],self.en_passant[1],is_en_passant=True))

    def _generate_knight_moves(self,moves,row,col,piece):
        is_white=piece.isupper()
        l=[[1,2],[2,1],[2,-1],[1,-2],[-1,-2],[-2,-1],[-2,1],[-1,2]]
        for coord in l:
            if 0<=row+coord[0]<=7 and 0<=col+coord[1]<=7 and self.board[row+coord[0]][col+coord[1]]=='.':
                    moves.append(Move(self,row,col,row+coord[0],col+coord[1]))
                    continue
            if 0<=row+coord[0]<=7 and 0<=col+coord[1]<=7 and self.board[row+coord[0]][col+coord[1]].isupper()!=is_white:
                 moves.append(Move(self,row,col,row+coord[0],col+coord[1]))
            
            
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
                     moves.append(Move(self,row,col,r,c))
                     continue
                is_target_white=target_field.isupper()
                if is_white !=is_target_white:
                     moves.append(Move(self,row,col,r,c))
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
                     moves.append(Move(self,row,col,r,c))
                     continue
                is_target_white=target_field.isupper()
                if is_white !=is_target_white:
                     moves.append(Move(self,row,col,r,c))
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
                    moves.append(Move(self,row,col,row+d[0],col+d[1]))
                    continue
                elif target_field.isupper()!=is_white:
                    moves.append(Move(self,row,col,row+d[0],col+d[1]))
        if is_white and 'K' in self.castling_rights:
            if self.board[row][col+1]=='.' and self.board[row][col+2]=='.':
                moves.append(Move(self,row,col,row,col+2,is_castle=True))
        if is_white and 'Q'in self.castling_rights:
            if self.board[row][col-1]=='.' and self.board[row][col-2]=='.' and self.board[row][col-3]=='.':
                moves.append(Move(self,row,col,row,col-2,is_castle=True))
        
        if not is_white and 'k' in self.castling_rights:
            if self.board[row][col+1]=='.' and self.board[row][col+2]=='.':
                moves.append(Move(self,row,col,row,col+2,is_castle=True))
        if not is_white and 'q' in self.castling_rights:
            if self.board[row][col-1]=='.' and self.board[row][col-2]=='.' and self.board[row][col-3]=='.':
                moves.append(Move(self,row,col,row,col-2,is_castle=True))

    def make_move(self,move: Move):
        self.zobrist_hash^=self.hasher.black_to_move_key

        for char in self.castling_rights:
            if char in self.hasher.castling_keys:
                self.zobrist_hash^=self.hasher.castling_keys[char]
        
        if self.en_passant is not None:
            self.zobrist_hash^=self.hasher.en_passant_keys[self.en_passant[1]]

        start_sq=move.start_row*8+move.start_col
        end_sq=move.end_row*8+move.end_col
        
        self.board[move.start_row][move.start_col]='.'
        self.zobrist_hash^=self.hasher.piece_keys[(move.piece_moved,start_sq)] 

        if move.piece_moved.upper()=='K':
            if move.piece_moved.isupper():
                self.white_king_pos=(move.end_row,move.end_col)
            else:
                self.black_king_pos=(move.end_row,move.end_col)

        if move.piece_captured!=None:
            if move.is_en_passant:
                square=move.start_row*8+move.end_col
                self.zobrist_hash^=self.hasher.piece_keys[(move.piece_captured,square)]
                self.board[move.start_row][move.end_col]='.'
            else:
                self.zobrist_hash^=self.hasher.piece_keys[(move.piece_captured,end_sq)]
        
        final_piece=move.promotion_piece if move.promotion_piece!= None else move.piece_moved
        self.zobrist_hash^=self.hasher.piece_keys[(final_piece,end_sq)]
        self.board[move.end_row][move.end_col]=final_piece

        if move.is_castle:
            if move.end_col == 6: # Kurze Rochade (König auf g)
                rook_start_idx, rook_end_idx = move.start_row * 8 + 7, move.start_row * 8 + 5
                rook_piece = self.board[move.start_row][7] # Holen uns den Turm vom neuen Feld
                self.zobrist_hash ^= self.hasher.piece_keys[(rook_piece, rook_start_idx)]
                self.zobrist_hash ^= self.hasher.piece_keys[(rook_piece, rook_end_idx)]
                self.board[move.start_row][7] = '.'
                self.board[move.start_row][5] = rook_piece
            elif move.end_col == 2: # Lange Rochade (König auf c)
                rook_start_idx, rook_end_idx = move.start_row * 8 + 0, move.start_row * 8 + 3
                rook_piece = self.board[move.start_row][0]
                self.zobrist_hash ^= self.hasher.piece_keys[(rook_piece, rook_start_idx)]
                self.zobrist_hash ^= self.hasher.piece_keys[(rook_piece, rook_end_idx)]
                self.board[move.start_row][0] = '.'
                self.board[move.start_row][3] = rook_piece
        if move.is_en_passant:
            self.board[move.start_row][move.start_col+move.col_direction]='.'
            other_pawn='p' if move.piece_moved.isupper() else 'P'
            self.zobrist_hash^=self.hasher.piece_keys[(other_pawn,start_sq+move.col_direction)]
        self.update_castling_rights(move)
        # Füge die NEUEN Rochaderechte zum Hash hinzu
        if self.castling_rights!= None:
            for char in self.castling_rights:
                if char in self.hasher.castling_keys:
                    self.zobrist_hash ^= self.hasher.castling_keys[char]

        self.en_passant = None
        if move.is_double_p_move():
            self.en_passant =(move.start_row+move.row_direction,move.start_col)
            self.zobrist_hash ^= self.hasher.en_passant_keys[move.start_col]

        
        
        

        # Spieler am Zug und Zähler aktualisieren
        self.turn = 'b' if self.turn == 'w' else 'w'

       
    def undo_move(self, move: Move):
        start_sq=move.start_row*8+move.start_col
        end_sq=move.end_row*8+move.end_col
        self.turn='w' if self.turn=='b' else 'b'
        self.zobrist_hash^=self.hasher.black_to_move_key

        for char in self.castling_rights:
            if char in self.hasher.castling_keys:
                self.zobrist_hash^=self.hasher.castling_keys[char]


        piece_reached=move.piece_moved if move.promotion_piece==None else move.promotion_piece
        piece_started=move.piece_moved

        self.board[move.end_row][move.end_col]='.'
        self.zobrist_hash^=self.hasher.piece_keys[(piece_reached,end_sq)]

        self.board[move.start_row][move.start_col]=piece_started
        self.zobrist_hash^=self.hasher.piece_keys[(piece_started,start_sq)]

        if move.piece_moved.upper()=='K':
            if move.piece_moved.isupper():
                self.white_king_pos=(move.start_row,move.start_col)
            else:
                self.black_king_pos=(move.start_row,move.start_col)

        if move.piece_captured!=None:
            self.board[move.end_row][move.end_col]=move.piece_captured
            self.zobrist_hash^=self.hasher.piece_keys[(move.piece_captured,end_sq)]
        
        if move.is_en_passant:
            pawn='p' if self.turn=='w' else 'P'
            self.board[move.start_row][move.end_col]=pawn
            square=start_sq+move.end_col-move.start_col
            self.zobrist_hash^=self.hasher.piece_keys[(pawn,square)]

        if move.is_castle:
            rook='R' if self.turn=='w' else 'r'
            r=7 if self.turn=='w' else 0
            c=7 if move.col_direction>0 else 0
            end_square=r*8+c
            start_square=start_sq+move.col_direction
            self.board[r][move.start_col+move.col_direction]='.'
            self.zobrist_hash^=self.hasher.piece_keys[(rook,start_square)]
            self.board[r][c]=rook
            self.zobrist_hash^=self.hasher.piece_keys[(rook,end_square)]

        self.castling_rights=move.old_castling_rights
        for char in self.castling_rights:
                if char in self.hasher.castling_keys:
                    self.zobrist_hash ^= self.hasher.castling_keys[char]
        if self.en_passant is not None:
            self.zobrist_hash^=self.hasher.en_passant_keys[self.en_passant[1]]
        self.en_passant=move.old_en_passant_rights
        if self.en_passant is not None:
            self.zobrist_hash^=self.hasher.en_passant_keys[self.en_passant[1]]


          
    def is_square_attacked(self, r, c, attacker_color):
        """Prüft, ob das Feld (r, c) vom Spieler der 'attacker_color' angegriffen wird."""
        is_attacker_white = (attacker_color == 'w')
        # Bauernangriffe prüfen
        pawn_direction = 1 if is_attacker_white else -1
        for dc in [-1, 1]:
            if 0 <= r + pawn_direction < 8 and 0 <= c + dc < 8:
                piece = self.board[r + pawn_direction][c + dc]
                expected_pawn = 'P' if is_attacker_white else 'p'
                if piece == expected_pawn:
                    return True

        # Springerangriffe prüfen
        knight_offsets = [(1, 2), (2, 1), (2, -1), (1, -2), (-1, -2), (-2, -1), (-2, 1), (-1, 2)]
        expected_knight = 'N' if is_attacker_white else 'n'
        for dr, dc in knight_offsets:
            if 0 <= r + dr < 8 and 0 <= c + dc < 8 and self.board[r + dr][c + dc] == expected_knight:
                return True

        # Gleitende Figuren (Turm, Läufer, Dame)
        sliding_directions = {
            'r': [(0, 1), (0, -1), (1, 0), (-1, 0)],
            'b': [(1, 1), (1, -1), (-1, 1), (-1, -1)],
        }
        expected_rook = 'R' if is_attacker_white else 'r'
        expected_bishop = 'B' if is_attacker_white else 'b'
        expected_queen = 'Q' if is_attacker_white else 'q'

        for piece_type, directions in sliding_directions.items():
            for dr, dc in directions:
                for i in range(1, 8):
                    tr, tc = r + i * dr, c + i * dc
                    if not (0 <= tr < 8 and 0 <= tc < 8): break
                    
                    target = self.board[tr][tc]
                    if target != '.':
                        if target == expected_queen or \
                        (piece_type == 'r' and target == expected_rook) or \
                        (piece_type == 'b' and target == expected_bishop):
                            return True
                        break # Blockiert

        # König-Angriffe prüfen
        expected_king = 'K' if is_attacker_white else 'k'
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0: continue
                if 0 <= r + dr < 8 and 0 <= c + dc < 8 and self.board[r + dr][c + dc] == expected_king:
                    return True
                    
        return False

    def piece_index(self, piece):
        for r in range(8):
            for c in range(8):
                if self.board[r][c]==piece:
                    return (r,c)
        return None
    def in_check(self):
        king_pos=self.white_king_pos if self.turn=='w' else self.black_king_pos
        attacker='b' if self.turn=='w' else 'w'
        return self.is_square_attacked(king_pos[0],king_pos[1],attacker)
    
    def update_castling_rights(self,move: Move):
        if move.piece_moved.upper()=='K':
            if move.piece_moved.isupper():
                self.castling_rights=self.castling_rights.replace('K','')
                self.castling_rights=self.castling_rights.replace('Q','')
            else:
                self.castling_rights=self.castling_rights.replace('k','')
                self.castling_rights=self.castling_rights.replace('q','')
        elif move.piece_moved=='R':
            if move.start_col==7:
                self.castling_rights=self.castling_rights.replace('K','')
            elif move.start_col==0:
                self.castling_rights=self.castling_rights.replace('Q','')
        elif move.piece_moved=='r':
            if move.start_col==7:
                self.castling_rights=self.castling_rights.replace('k','')
            elif move.start_col==0:
                    self.castling_rights=self.castling_rights.replace('q','')
        if move.piece_captured!=None:
            if move.piece_captured.upper()=='R':
                capture_col=move.end_col
                is_capture_white= True if move.piece_captured.isupper() else False
                if is_capture_white:
                    if capture_col==0:
                        self.castling_rights=self.castling_rights.replace('Q','')
                    if capture_col==7:
                        self.castling_rights=self.castling_rights.replace('K','')
                else:
                    if capture_col==0:
                        self.castling_rights=self.castling_rights.replace('q','')
                    if capture_col==7:
                        self.castling_rights=self.castling_rights.replace('k','')
    def parse_move(self,san_string):
        legal_moves=self.get_legal_moves()
        for move in legal_moves:
            if move.to_san()== san_string:
                return move
        return None
    def puts_in_check(self,move:Move):
        self.make_move(move)
        if self.in_check():
            self.undo_move(move)
            return True
        else:
            self.undo_move(move)
            return False
