from constants import (STARTING_FEN,RAY_ATTACKS,KNIGHT_ATTACKS,KING_ATTACKS,PAWN_ATTACKS,NOT_FILE_A,
                       NOT_FILE_H,NOT_FILE_GH,NOT_FILE_AB,FILES,PIECE_MAP,COLOR_MAP,BOARD_ALL_SET,
                       KING_ZONE_MASKS,LSB_LOOKUP_TABLE)
WHITE, BLACK=0,1
PAWN,KNIGHT,BISHOP,ROOK,QUEEN,KING=0,1,2,3,4,5
PIECE_TYPE_MAP={
    'P': PAWN, 'N': KNIGHT, 'B': BISHOP, 'R':ROOK,'Q':QUEEN, 'K':KING,
    
    'p': PAWN, 'n': KNIGHT, 'b': BISHOP, 'r':ROOK,'q':QUEEN, 'k':KING
}
PIECE_CHAR_LIST='PNBRQK'
from numpy import floor
from move import Move
from zobrist import ZobristHasher
from collections import defaultdict
from numba import jit
from evaluation import (PIECE_PST,PIECE_VALUES)

class BitboardChessBoard:
    def __init__(self,fen=STARTING_FEN):
        self.piece_bitboards=[[0]*6 for _ in range(2)]
        self.color_bitboards=[0,0]
        self.pos_count=defaultdict(int)

        self._parse_fen(fen)
        # initialize color bitboards
        for num in [0,1,2,3,4,5]:
            self.color_bitboards[0]|=self.piece_bitboards[0][num]
            self.color_bitboards[1]|=self.piece_bitboards[1][num]
        self.occupied=self.color_bitboards[0] | self.color_bitboards[1]

        #initialize Map of pieces
        self.square_to_PIECE_MAP=[None]*64
        for color in range(2):
            for piece in range(6):
                for square_index in self.get_set_bit_indices_efficient(self.piece_bitboards[color][piece]):
                    piece_char=PIECE_CHAR_LIST[piece] if color==WHITE else PIECE_CHAR_LIST[piece].lower()
                    self.square_to_PIECE_MAP[square_index]=piece_char
        #initialize zobrist hash
        self.hasher=ZobristHasher()
        self.zobrist_hash=self.hasher.calculate_hash(self)

        #initialize game score partly
        self.game_phase=self.get_game_phase()
        self.material_score=self.get_material_score()
        self.positional_score_mg=self.get_positional_score_mg()
        self.positional_score_eg=self.get_positional_score_eg()
        self.positional_score=self.positional_score_mg*self.game_phase+self.positional_score_eg*(1-self.game_phase)
        
        #make a list of moves made
        self.last_move_list=[]
    def __eq__(self,other):
        self_state = (self.piece_bitboards,
        self.turn,
        # Sort castling rights string to ensure 'KQ' == 'QK'
        "".join(sorted(self.castling_rights)), 
        self.en_passant_rights,
        self.half_move_clock,
        self.move_number
    )

    # 3. Create the same tuple for the `other` object.
        other_state = (
            other.piece_bitboards,
            other.turn,
            "".join(sorted(other.castling_rights)),
            other.en_passant_rights,
            other.half_move_clock,
            other.move_number)
        return self_state==other_state
    
    # Public core methods:
    def make_move(self, move:Move):
        self.update_material_score(move)
        self.update_positional_score(move)
        self.update_rights_and_hash(move)
        self.update_bitboards(move)
        self.update_piece_map(move)
        self.update_positional_hash_count()
        self.last_move_list.append(move)
    def undo_move(self,move:Move):
        self.update_positional_hash_count(undo=True)
        self.update_material_score(move,True)
        self.update_positional_score(move,True)
        self.update_rights_and_hash(move,True)
        self.update_bitboards(move)
        self.update_piece_map(move,undo=True)
        self.last_move_list.pop()
        

    def make_null_move(self):
        """Switches the side to play and returns the original en passant square."""
        # 1. Remember the old en passant square
        original_en_passant_square = self.en_passant_rights

        # 2. If an en passant square existed, XOR its hash key out
        if self.en_passant_rights is not None:
            self.zobrist_hash ^= self.hasher.en_passant_keys[self.en_passant_rights % 8]
        self.en_passant_rights = None

        # 3. Flip the side to play
        self.turn = BLACK if self.turn == WHITE else WHITE
        self.zobrist_hash ^= self.hasher.black_to_move_key

        # 4. Return the saved value
        return original_en_passant_square

    def undo_null_move(self, original_en_passant_square):
        """Switches the side back and restores the original en passant square."""
        # 1. Flip the side back
        self.turn = BLACK if self.turn == WHITE else WHITE
        self.zobrist_hash ^= self.hasher.black_to_move_key

        # 2. Restore the original en passant square
        self.en_passant_rights = original_en_passant_square

        # 3. If it wasn't None, XOR its hash key back in to restore the hash
        if self.en_passant_rights is not None:
            self.zobrist_hash ^= self.hasher.en_passant_keys[self.en_passant_rights % 8]
        
    def update_rights_and_hash(self,move: Move,undo=False):
        #update turn
        self.zobrist_hash^=self.hasher.black_to_move_key
        self.turn=WHITE if self.turn==BLACK else BLACK
        #update hash rights
        self.update_hash_rights()
        #update the castle rights and en passant rights of the Board
        self.update_castle_rights(move,undo=undo)
        self.update_en_passant_rights(move,undo=undo)
        self.update_hash_rights()
        #update position
        self.update_hash_position(move)
    
    def update_hash_rights(self):
        #FGive or remove all the old rights from the hash:
        for char in self.castling_rights:
            if char in self.hasher.castling_keys:
                self.zobrist_hash^=self.hasher.castling_keys[char]
        
        if self.en_passant_rights is not None:
            self.zobrist_hash^=self.hasher.en_passant_keys[self.en_passant_rights%8]
    def update_castle_rights(self,move: Move,undo=False):
        if undo==False:
                #first what happens if it is white's move
            if move.color==WHITE and any(char.isupper() for char in self.castling_rights):
                #if king moved, remove all castling rights
                if move.piece_moved=='K':
                    self.castling_rights=self.castling_rights.replace('Q','')
                    self.castling_rights=self.castling_rights.replace('K','')
                #what happens if one of the rooks moved
                elif move.piece_moved=='R':
                    if move.from_square==0:
                        self.castling_rights=self.castling_rights.replace('Q','')
                    if move.from_square==7:
                        self.castling_rights=self.castling_rights.replace('K','')
            #now what happens if it is black's move
            elif move.color==BLACK and any(char.islower() for char in self.castling_rights):
                #what happens if the king moved
                if move.piece_moved=='k':
                    self.castling_rights=self.castling_rights.replace('q','')
                    self.castling_rights=self.castling_rights.replace('k','')
                #what happens if one of the rook moved
                elif move.piece_moved=='r':
                    if move.from_square==56:
                        self.castling_rights=self.castling_rights.replace('q','')
                    if move.from_square==63:
                        self.castling_rights=self.castling_rights.replace('k','')
            #now check if a rook is captured and remove the castling right
            if move.color==WHITE and any(char.islower() for char in self.castling_rights) and move.piece_captured=='r':
                if move.to_square==56:
                    self.castling_rights=self.castling_rights.replace('q','')
                elif move.to_square==63:
                    self.castling_rights=self.castling_rights.replace('k','')
            elif move.color==BLACK and any(char.isupper() for char in self.castling_rights) and move.piece_captured=='R':
                if move.to_square==0:
                    self.castling_rights=self.castling_rights.replace('Q','')
                elif move.to_square==7:
                    self.castling_rights=self.castling_rights.replace('K','')
        else:
            self.castling_rights=move.old_castling_rights
    def update_en_passant_rights(self,move: Move, undo=False):
        if undo==False:
                
            self.en_passant_rights=None
            if move.is_double_p_move():
                self.en_passant_rights=move.to_square-8 if move.color==WHITE else move.to_square+8
        else: 
            self.en_passant_rights=move.old_en_passant_rights
    def update_hash_position(self,move: Move):
        piece_reached=move.promotion_piece if move.promotion_piece else move.piece_moved
        self.zobrist_hash^=self.hasher.piece_keys[(move.piece_moved,move.from_square)]
        self.zobrist_hash^=self.hasher.piece_keys[(piece_reached,move.to_square)]
        if move.piece_captured:
            self.zobrist_hash^=self.hasher.piece_keys[(move.piece_captured,move.to_square)]
        if move.is_en_passant:
            pawn='P' if move.color==BLACK else 'p'
            to_square=move.to_square-8 if move.color==WHITE else move.to_square+8
            self.zobrist_hash^=self.hasher.piece_keys[(pawn,to_square)]
        if move.is_castle:
            king_side=True if move.to_square>move.from_square else False
            old_rook_square=move.to_square+1 if king_side else move.to_square-2
            new_rook_square=move.to_square-1 if king_side else move.to_square+1
            rook='R' if move.color==WHITE else 'r'
            self.zobrist_hash^=self.hasher.piece_keys[(rook,old_rook_square)]
            self.zobrist_hash^=self.hasher.piece_keys[(rook,new_rook_square)]
    def update_bitboards(self,move:Move):
        move_piece=move.piece_moved
        piece_reached= move.promotion_piece if move.promotion_piece else move_piece
        self.piece_bitboards[move.color][PIECE_TYPE_MAP[move_piece]]^=1<<move.from_square
        self.color_bitboards[move.color]^=1<<move.from_square
        self.occupied^=1<<move.from_square

        self.piece_bitboards[move.color][PIECE_TYPE_MAP[piece_reached]]^=1<<move.to_square
        self.color_bitboards[move.color]^=1<<move.to_square
        self.occupied^=1<<move.to_square
        if move.piece_captured:
            other_color=BLACK if move.color==WHITE else WHITE
            self.piece_bitboards[other_color][PIECE_TYPE_MAP[move.piece_captured]]^=1<<move.to_square
            self.color_bitboards[other_color]^=1<<move.to_square
            self.occupied^=1<<move.to_square
        
        if move.is_en_passant:
            other_color=BLACK if move.color==WHITE else WHITE
            pawn='P' if other_color==WHITE else 'p'
            pawn_square=move.to_square-8 if move.color==WHITE else move.to_square+8
            self.piece_bitboards[other_color][PIECE_TYPE_MAP[pawn]]^=1<<pawn_square
            self.color_bitboards[other_color]^=1<<pawn_square
            self.occupied^=1<<pawn_square

        if move.is_castle:
            king_side=True if move.to_square>move.from_square else False
            old_rook_square=move.to_square+1 if king_side else move.to_square-2
            new_rook_square=move.to_square-1 if king_side else move.to_square+1
            rook='R' if move.color==WHITE else 'r'
                
            self.piece_bitboards[move.color][PIECE_TYPE_MAP[rook]]^=(1<<old_rook_square)|(1<< new_rook_square)
            self.color_bitboards[move.color]^=(1<<old_rook_square)|(1<< new_rook_square)
            self.occupied^=(1<<old_rook_square)|(1<< new_rook_square)
    def update_piece_map(self,move:Move,undo=False):
        
        if undo==False:
            self.square_to_PIECE_MAP[move.from_square]=None
            piece_reached=move.promotion_piece if move.promotion_piece else move.piece_moved
            self.square_to_PIECE_MAP[move.to_square]=piece_reached
            if move.is_en_passant:
                pawn_square=move.to_square-8 if move.color==WHITE else move.to_square+8
                self.square_to_PIECE_MAP[pawn_square]=None

            if move.is_castle:
                
                king_side=True if move.to_square>move.from_square else False
                old_rook_square=move.to_square+1 if king_side else move.to_square-2
                new_rook_square=move.to_square-1 if king_side else move.to_square+1
                rook='R' if move.color==WHITE else 'r'
                
                self.square_to_PIECE_MAP[old_rook_square]=None
                self.square_to_PIECE_MAP[new_rook_square]=rook
        else:
            self.square_to_PIECE_MAP[move.from_square]=move.piece_moved
            piece_captured=move.piece_captured if move.piece_captured else None
            self.square_to_PIECE_MAP[move.to_square]=piece_captured
            if move.is_en_passant:
                pawn_square=move.to_square-8 if move.color==WHITE else move.to_square+8
                pawn='P' if move.color==BLACK else 'p'
                self.square_to_PIECE_MAP[pawn_square]=pawn

            if move.is_castle:
                
                king_side=True if move.to_square>move.from_square else False
                old_rook_square=move.to_square+1 if king_side else move.to_square-2
                new_rook_square=move.to_square-1 if king_side else move.to_square+1
                rook='R' if move.color==WHITE else 'r'
                
                self.square_to_PIECE_MAP[old_rook_square]=rook
                self.square_to_PIECE_MAP[new_rook_square]=None
    def update_positional_hash_count(self,undo=False):
        numb=-1 if undo else 1
        self.pos_count[self.get_position_count_hash()]+=numb






    def get_legal_moves(self):
        moves=[]
        color = self.turn
        king_square = self.get_lsb(self.piece_bitboards[color][KING])
        pinned_info = self.get_pinned_pieces_info(color)
        checkers_bb=self.get_attackers(king_square, BLACK if color==WHITE else WHITE)
        num_checkers=bin(checkers_bb).count('1')

        if num_checkers>1:
            moves+=self.get_king_moves(color)
        elif num_checkers ==1:
            moves+=self.get_king_moves(color)

            checker_sq=self.get_lsb(checkers_bb)
            checker=self.square_to_PIECE_MAP[checker_sq]

            remedy_mask=(1<< checker_sq)

            if checker.upper() in 'QRB':
                remedy_mask|=RAY_ATTACKS['line'][king_square][checker_sq]
            moves+=self.get_queen_moves(color,pinned_info,remedy_mask)
            moves+=self.get_rook_moves(color,pinned_info,remedy_mask)
            moves+=self.get_knight_moves(color,pinned_info,remedy_mask)
            moves+=self.get_bishop_moves(color,pinned_info,remedy_mask)
            if self.en_passant_rights is not None and checker.upper()=='P':
                remedy_mask|=1<< self.en_passant_rights
            moves+=self.get_pawn_moves(color,pinned_info,remedy_mask)
        else:
            moves+=self.get_queen_moves(color,pinned_info)
            moves+=self.get_rook_moves(color,pinned_info)
            moves+=(self.get_king_moves(color))
            moves+=self.get_knight_moves(color,pinned_info)
            moves+=self.get_bishop_moves(color,pinned_info)
            moves+=(self.get_pawn_moves(color,pinned_info))
        return moves
    def to_san(self,move:Move, all_legal_moves: list[Move]):
        if move.is_castle:
            return "O-O" if move.to_square %8 ==6 else "O-O-O"
        piece_symbol=move.piece_moved.upper()
        dest_square=self._square_to_algebraic(move.to_square)
        capture_symbol='x' if move.piece_captured else ''
        if piece_symbol=='P':
            if capture_symbol:
                start_file=self._square_to_algebraic(move.from_square)[0]
                base_notation=f"{start_file}{capture_symbol}{dest_square}"
            else:
                base_notation=dest_square
            if move.promotion_piece:
                base_notation+=f"={move.promotion_piece.upper()}"
        else:
            disambiguation_str=""
            competitors=[other_move for other_move in all_legal_moves
                         if other_move.piece_moved.upper()==piece_symbol and\
                            other_move.to_square == move.to_square and \
                            other_move.from_square != move.from_square
                         ]
            if competitors:
                from_rank, from_file =move.from_square//8, move.from_square %8
                same_file=any(other_move.from_square %8 == from_file for other_move in competitors)
                if not same_file:
                    disambiguation_str=self._square_to_algebraic(move.from_square)[0]
                else:
                    disambiguation_str=self._square_to_algebraic(move.from_square)
            base_notation=f"{piece_symbol}{disambiguation_str}{capture_symbol}{dest_square}"
        return base_notation
   


    # Move Generation:
    def get_pinned_pieces_info(self,color):
        pinned_info={}

        bb=self.piece_bitboards[color][KING]
        king_square=self.get_msb(bb)
        if king_square==-1:
            print('oops')
            for move in self.last_move_list:
                print(move.piece_moved)
                print('from')
                print(self._square_to_algebraic(move.from_square))
                print('to')
                print(self._square_to_algebraic(move.to_square))
            raise KeyError
        own_pieces=self.color_bitboards[color]
        enemy_pieces=self.color_bitboards[BLACK] if color==WHITE else self.color_bitboards[WHITE]
        for direction in range(8):
            ray=RAY_ATTACKS[direction][king_square]
            first_blocker_sq=self.get_first_blocker_square_on_ray(ray,True) if direction<=3 else self.get_first_blocker_square_on_ray(ray,False)
            if first_blocker_sq==-1:
                continue
            first_blocker_bb=1<< first_blocker_sq
            if first_blocker_bb & own_pieces:
                second_blocker_sq=self.get_second_blcoker_square_on_ray(ray,forwards=True,first_blocker_sq=first_blocker_sq) if direction<=3 else self.get_second_blcoker_square_on_ray(ray,forwards=False,first_blocker_sq=first_blocker_sq) 
                if second_blocker_sq==-1:
                    continue
                second_blocker_bb=1<<second_blocker_sq
                if second_blocker_bb & enemy_pieces:
                     if direction in [1,3,5,7]:
                        if second_blocker_bb & (self.piece_bitboards[WHITE][QUEEN]|self.piece_bitboards[WHITE][ROOK]|self.piece_bitboards[BLACK][QUEEN]|self.piece_bitboards[BLACK][ROOK]):
                            pinned_info[first_blocker_sq]=RAY_ATTACKS['line'][king_square][second_blocker_sq]^(1<< king_square)

                     if direction in [0,2,4,6]:
                        if second_blocker_bb & (self.piece_bitboards[WHITE][BISHOP] | self.piece_bitboards[WHITE][QUEEN]| self.piece_bitboards[BLACK][BISHOP]|self.piece_bitboards[BLACK][QUEEN]):
                            pinned_info[first_blocker_sq]=RAY_ATTACKS['line'][king_square][second_blocker_sq]^(1<< king_square)
        return pinned_info


    def get_piece_on_square(self,square_index):
        return self.square_to_PIECE_MAP[square_index]
    def get_knight_moves(self,color,pinned_pieces,remedy_mask=BOARD_ALL_SET,captures_only=False):
        moves=[]
        knights=self.piece_bitboards[color][KNIGHT]
        own_pieces=self.color_bitboards[color]
        for square in self.get_set_bit_indices_efficient(knights):
            if square in pinned_pieces:
                continue
            possible_moves=KNIGHT_ATTACKS[square] & ~own_pieces
            possible_moves&=remedy_mask
            if captures_only:
                captures_only_mask=self.color_bitboards[BLACK] if color==WHITE else self.color_bitboards[WHITE]
                possible_moves&=captures_only_mask
                
            while possible_moves:
                to_square=self.get_lsb(possible_moves)
                moves.append(Move(self,square,to_square))
                possible_moves &= (possible_moves^(1<< to_square))
        return moves
    def get_bishop_moves(self,color,pinned_pieces,remedy_mask=BOARD_ALL_SET,captures_only=False):
        moves=[]
        bishops=self.piece_bitboards[color][BISHOP]
        BISHOP_DIRECTIONS=[0,2,4,6]
        self._generate_sliding_moves(moves,bishops,BISHOP_DIRECTIONS,color,pinned_pieces,remedy_mask,captures_only)
        return moves
    def get_rook_moves(self,color,pinned_pieces,remedy_mask=BOARD_ALL_SET,captures_only=False):
        moves=[]
        rooks=self.piece_bitboards[color][ROOK]
        ROOK_DIRECTIONS=[1,3,5,7]
        self._generate_sliding_moves(moves,rooks,ROOK_DIRECTIONS,color,pinned_pieces,remedy_mask,captures_only)
        return moves   
    def get_queen_moves(self,color,pinned_pieces,remedy_mask=BOARD_ALL_SET,captures_only=False):
        moves=[]
        queens=self.piece_bitboards[color][QUEEN]
        QUEEN_DIRECTIONS=[0,1,2,3,4,5,6,7]
        self._generate_sliding_moves(moves,queens,QUEEN_DIRECTIONS,color,pinned_pieces,remedy_mask,captures_only)
        return moves 
    def get_king_moves(self,color,captures_only=False):
        moves=[]
        king_sq=self.get_set_bit_indices_efficient(self.piece_bitboards[color][KING])[0]
        own_pieces=self.color_bitboards[color]
        opponent_attacks=self.black_attacks if color==WHITE else self.white_attacks
        possible_moves=(KING_ATTACKS[king_sq]&~own_pieces)&~opponent_attacks
        if captures_only:
                captures_only_mask=self.color_bitboards[BLACK] if color==WHITE else self.color_bitboards[WHITE]
                possible_moves&=captures_only_mask
        for m in self.get_set_bit_indices_efficient(possible_moves):
            moves.append(Move(self,king_sq,m))
        if captures_only==False:
            if color==WHITE:
                if 'K' in self.castling_rights:
                    if (opponent_attacks|self.occupied) & (3<< king_sq+1)==0 and ((RAY_ATTACKS['line'][king_sq+1][6] &self.occupied)==0):
                        moves.append(Move(self,king_sq,king_sq+2,is_castle=True))
                if 'Q' in self.castling_rights:
                    if (opponent_attacks|self.occupied) & (3<< king_sq-2)==0  and ((RAY_ATTACKS['line'][king_sq-1][1] &self.occupied)==0):
                        moves.append(Move(self,king_sq,king_sq-2,is_castle=True))
            else:
                if 'k' in self.castling_rights:
                    if (opponent_attacks|self.occupied) & (3<< king_sq+1)==0  and ((RAY_ATTACKS['line'][king_sq+1][62] &self.occupied)==0):
                        moves.append(Move(self,king_sq,king_sq+2,is_castle=True))
                if 'q' in self.castling_rights:
                    if (opponent_attacks| self.occupied) & (3<< king_sq-2)==0  and ((RAY_ATTACKS['line'][king_sq-1][57] &self.occupied)==0):
                        moves.append(Move(self,king_sq,king_sq-2,is_castle=True))
        return moves
    
    def get_pawn_moves(self,color,pinned_info,remedy_mask=BOARD_ALL_SET,captures_only=False):
        moves=[]
        if captures_only:
            self._generate_pawn_captures(moves,color,pinned_info,remedy_mask)
        else:
            self._generate_pawn_pushes(moves,color,pinned_info,remedy_mask)
            self._generate_pawn_captures(moves,color,pinned_info,remedy_mask)
            self._generate_en_passant(moves,color,pinned_info,remedy_mask)

        return moves

    def get_attackers(self,target_square:int, by_color):
        attackers=0
        if by_color==WHITE:
            enemy_pawns=self.piece_bitboards[WHITE][PAWN]
            enemy_knights=self.piece_bitboards[WHITE][KNIGHT]
            enemy_rooks_queens=self.piece_bitboards[WHITE][ROOK]| self.piece_bitboards[WHITE][QUEEN]
            enemy_bishops_queens=self.piece_bitboards[WHITE][BISHOP]| self.piece_bitboards[WHITE][QUEEN]
            pawn_attacks=PAWN_ATTACKS[BLACK][target_square]
        else:
            
            enemy_pawns=self.piece_bitboards[BLACK][PAWN]
            enemy_knights=self.piece_bitboards[BLACK][KNIGHT]
            enemy_rooks_queens=self.piece_bitboards[BLACK][ROOK]| self.piece_bitboards[BLACK][QUEEN]
            enemy_bishops_queens=self.piece_bitboards[BLACK][BISHOP]| self.piece_bitboards[BLACK][QUEEN]
            pawn_attacks=PAWN_ATTACKS[WHITE][target_square]
        attackers|= KNIGHT_ATTACKS[target_square] & enemy_knights
        attackers|=pawn_attacks & enemy_pawns
        for direction in range(8):
            ray = RAY_ATTACKS[direction][target_square]
            blockers_on_ray = ray & self.occupied

            if blockers_on_ray:
                first_blocker_square = self.get_lsb(blockers_on_ray) if direction <= 3 else self.get_msb(blockers_on_ray)
            
                is_diagonal = direction in [0, 2, 4, 6]
                if is_diagonal:
                    if (1 << first_blocker_square) & enemy_bishops_queens:
                        attackers |= (1 << first_blocker_square)
                else:
                    if (1 << first_blocker_square) & enemy_rooks_queens:
                        attackers |= (1 << first_blocker_square)
        return attackers
    def _add_promotion_moves(self,moves,from_square,to_square):
        color=self.turn
        promotion_pieces='QRNB' if color==WHITE else "qrbn"
        for piece_char in promotion_pieces:
            moves.append(Move(self,from_square,to_square,promotion_piece=piece_char))
    def _generate_pawn_pushes(self,moves,color,pinned_info,remedy_mask):
        own_pawns=self.piece_bitboards[color][PAWN]
        number=8 if color==WHITE else -8 
        single_pushes= (own_pawns << 8) &~ self.occupied if color==WHITE else (own_pawns>>8) &~self.occupied
        for to_square in self.get_set_bit_indices_efficient(single_pushes& remedy_mask):
            from_square=to_square-number
            is_legal=True
            if from_square in pinned_info:
                pin_ray=pinned_info[from_square]
                if not ((1<< to_square) & pin_ray):
                    is_legal=False
            if is_legal:
                if color==WHITE and to_square>=56:
                    self._add_promotion_moves(moves,from_square,to_square)
                elif color==BLACK and to_square<=7:
                    self._add_promotion_moves(moves,from_square,to_square)
                else:
                    moves.append(Move(self,from_square,to_square))
                # Now create double pawn moves
                start_rank=1 if color==WHITE else 6
                if from_square //8==start_rank and (((1<< to_square+number)&~self.occupied)&remedy_mask):
                    moves.append(Move(self,from_square,to_square+number))
    def _generate_pawn_captures(self,moves,color,pinned_info,remedy_mask):
        if color==WHITE:
            own_pawns=self.piece_bitboards[WHITE][PAWN]
            enemy_pieces=self.color_bitboards[BLACK]
            promotion_rank=6
            captures=self.white_pawn_attacks & enemy_pieces & remedy_mask
        else:
            own_pawns=self.piece_bitboards[BLACK][PAWN]
            enemy_pieces=self.color_bitboards[WHITE]
            promotion_rank=1
            captures=self.black_pawn_attacks & enemy_pieces & remedy_mask
        while captures:
            to_square=self.get_lsb(captures)
            if color==WHITE:
                possible_attackers=(((1<< to_square)>>9 & NOT_FILE_H)|((1<< to_square)>>7 & NOT_FILE_A)) & own_pawns
            else:
                possible_attackers=(((1<< to_square)<<7 & NOT_FILE_H)|((1<< to_square)<<9 & NOT_FILE_A) ) & own_pawns
            while possible_attackers:
                from_square=self.get_lsb(possible_attackers)
                is_legal=True
                if from_square in pinned_info:
                    if not ((1 << to_square) & pinned_info[from_square]):
                        is_legal = False
                if is_legal:
                    if from_square//8==promotion_rank:
                        self._add_promotion_moves(moves,from_square,to_square)
                    else:
                        moves.append(Move(self,from_square,to_square))
                possible_attackers&=possible_attackers-1
            captures&=captures-1







    def _generate_en_passant(self,moves,color,pinned_info,remedy_mask):
         if self.en_passant_rights is not None:
            
            own_pawns=self.piece_bitboards[color][PAWN]
            if 1<< self.en_passant_rights & remedy_mask!=0:
                en_passant=self.en_passant_rights 
                direction=1 if color==WHITE else -1
                bb=own_pawns&((1<< (en_passant-direction*9))| (1<< (en_passant-direction*7)))
                for from_square in self.get_set_bit_indices_efficient(bb):
                    is_legal=True
                    if from_square in pinned_info:
                        pin_ray=pinned_info[from_square]
                        if not ((1<< en_passant) & pin_ray):
                         is_legal=False
                    if is_legal:
                        moves.append(Move(self,from_square,en_passant,is_en_passant=True))
    def _generate_sliding_moves(self,moves,piece_bb,directions,color,pinned_info,remedy_mask,captures_only=False):
        own_pieces=self.color_bitboards[color]
        for square in self.get_set_bit_indices_efficient(piece_bb):
            possible_moves=0
            if square in pinned_info:
                rays=0
                for dir in directions:
                    rays|=RAY_ATTACKS[dir][square]
                possible_moves|=(pinned_info[square]^(1<<square))&rays
            else:
                for direction in directions:
                    ray=RAY_ATTACKS[direction][square]
                    blockers_on_ray=ray & self.occupied
                    if blockers_on_ray==0:
                        possible_moves|=ray
                    else:
                        first_blocker_square=self.get_lsb(blockers_on_ray) if direction<=3 else self.get_msb(blockers_on_ray)
                        possible_moves|=(ray^RAY_ATTACKS[direction][first_blocker_square])
                        if own_pieces & (1<<first_blocker_square):
                            continue
                        else:
                            possible_moves|=(1<< first_blocker_square)
            possible_moves&=~own_pieces
            if captures_only:
                captures_only_mask=self.color_bitboards[BLACK] if color==WHITE else self.color_bitboards[WHITE]
                possible_moves&=captures_only_mask
            for m in self.get_set_bit_indices_efficient(possible_moves&remedy_mask):
                moves.append(Move(self,square,m)) 
    def get_captures(self):
        moves=[]
        color = self.turn
        king_square = self.get_lsb(self.piece_bitboards[color][KING])
        pinned_info = self.get_pinned_pieces_info(color)
        checkers_bb=self.get_attackers(king_square, BLACK if color==WHITE else WHITE)
        num_checkers=bin(checkers_bb).count('1')

        if num_checkers>1:
            moves+=self.get_king_moves(color,captures_only=True)
        elif num_checkers ==1:
            moves+=self.get_king_moves(color,captures_only=True)

            checker_sq=self.get_lsb(checkers_bb)
            checker=self.square_to_PIECE_MAP[checker_sq]

            remedy_mask=(1<< checker_sq)

            if checker.upper() in 'QRB':
                remedy_mask|=RAY_ATTACKS['line'][king_square][checker_sq]
            moves+=self.get_queen_moves(color,pinned_info,remedy_mask)
            moves+=self.get_rook_moves(color,pinned_info,remedy_mask)
            moves+=self.get_knight_moves(color,pinned_info,remedy_mask)
            moves+=self.get_bishop_moves(color,pinned_info,remedy_mask)
            if self.en_passant_rights is not None and checker.upper()=='P':
                remedy_mask|=1<< self.en_passant_rights
            moves+=self.get_pawn_moves(color,pinned_info,remedy_mask)
        else:
            moves+=self.get_queen_moves(color,pinned_info,captures_only=True)
            moves+=self.get_rook_moves(color,pinned_info,captures_only=True)
            moves+=self.get_knight_moves(color,pinned_info,captures_only=True)
            moves+=self.get_bishop_moves(color,pinned_info,captures_only=True)
            moves+=(self.get_pawn_moves(color,pinned_info,captures_only=True))
            moves+=(self.get_king_moves(color,captures_only=True))
        return moves

    # FEN-Parsing (Internal helpers)
    def _parse_fen(self,fen):
        fen_parts=fen.split(' ')
        self._parse_fen_pieces(fen_parts[0])
        self._parse_fen_turn(fen_parts[1])
        self._parse_fen_castling_rights(fen_parts[2])
        self.en_passant_rights=None if fen_parts[3]=='-' else 8*(int(fen_parts[3][1])-1)+FILES[fen_parts[3][0]]
        self.half_move_clock=int(fen_parts[4])
        self.move_number=int(fen_parts[5])
    def _parse_fen_pieces(self,piece_placement):
        
        rank =7
        file=0
        for char in piece_placement:
            if char =='/':
                rank-=1
                file=0
            elif char.isdigit():
                file+=int(char)
            else:
                square_index=rank*8+file
                color_index=WHITE if char.isupper() else BLACK
                piece_type_index=PIECE_TYPE_MAP[char.upper()]
                self.piece_bitboards[color_index][piece_type_index]|=(1<< square_index)
                file+=1
    def _parse_fen_turn(self,fen_turn):
        self.turn=WHITE if fen_turn=='w' else BLACK
    def _parse_fen_castling_rights(self,fen_rights):
        self.castling_rights=''
        for char in fen_rights:
            if char!='-':
                self.castling_rights+=char
    
    
   
    # Utility and helper methods:
    def display_bitboard(self,bb):
        print('-'*20)
        for r in range(7,-1,-1):
            
            for f in range(8):
                square_index=r*8+f
                if (bb>> square_index) &1:
                    print('1',end=' ')
                else:
                    print('.',end=' ')
            print(f"  {r+1}")
        print("\na b c d e f g h")
        print("-"*20)
    def coord_to_algebraic(self,r,c):
        files ="abcdefgh"
        ranks="12345678"
        return f"{files[c]}{ranks[r]}"
    def _square_to_algebraic(self,square):
        return self.coord_to_algebraic(square//8,square%8)
    
    def get_game_phase(self):
        INITIAL_PHASE_VALUE=24

        knight_phase=bin(self.piece_bitboards[WHITE][KNIGHT]| self.piece_bitboards[BLACK][KNIGHT]).count('1')*1
        bishop_phase=bin(self.piece_bitboards[WHITE][BISHOP]|self.piece_bitboards[BLACK][BISHOP]).count('1')*1
        rook_phase=bin(self.piece_bitboards[WHITE][ROOK]|self.piece_bitboards[BLACK][ROOK]).count('1')*2
        queen_phase=bin(self.piece_bitboards[WHITE][QUEEN]| self.piece_bitboards[BLACK][QUEEN]).count('1')*4
        current_phase=knight_phase+bishop_phase+rook_phase+queen_phase

        return min(current_phase,INITIAL_PHASE_VALUE)/ INITIAL_PHASE_VALUE

    def get_all_piece_bitboards(self):
        return {
            'P': self.piece_bitboards[WHITE][PAWN], 'N': self.piece_bitboards[WHITE][KNIGHT], 'B': self.piece_bitboards[WHITE][BISHOP],
            'R': self.piece_bitboards[WHITE][ROOK], 'Q': self.piece_bitboards[WHITE][QUEEN], 'K': self.piece_bitboards[WHITE][KING],
            'p': self.piece_bitboards[BLACK][PAWN], 'n': self.piece_bitboards[BLACK][KNIGHT], 'b': self.piece_bitboards[BLACK][BISHOP],
            'r': self.piece_bitboards[BLACK][ROOK], 'q': self.piece_bitboards[BLACK][QUEEN], 'k': self.piece_bitboards[BLACK][KING],
        }
    def get_material_score(self):
        score=0
        score += bin(self.piece_bitboards[WHITE][PAWN]).count('1')   * PIECE_VALUES['P']
        score += bin(self.piece_bitboards[WHITE][KNIGHT]).count('1') * PIECE_VALUES['N']
        score += bin(self.piece_bitboards[WHITE][BISHOP]).count('1') * PIECE_VALUES['B']
        score += bin(self.piece_bitboards[WHITE][ROOK]).count('1')   * PIECE_VALUES['R']
        score += bin(self.piece_bitboards[WHITE][QUEEN]).count('1')  * PIECE_VALUES['Q']
        
        score += bin(self.piece_bitboards[BLACK][PAWN]).count('1')   * PIECE_VALUES['p']
        score += bin(self.piece_bitboards[BLACK][KNIGHT]).count('1') * PIECE_VALUES['n']
        score += bin(self.piece_bitboards[BLACK][BISHOP]).count('1') * PIECE_VALUES['b']
        score += bin(self.piece_bitboards[BLACK][ROOK]).count('1')   * PIECE_VALUES['r']
        score += bin(self.piece_bitboards[BLACK][QUEEN]).count('1')  * PIECE_VALUES['q']
        return score
    def get_positional_score(self):
        
        return self.get_positional_score_mg*self.game_phase+self.get_positional_score_eg*(1-self.game_phase)
    def get_positional_score_mg(self):
        score=0.0
        for piece_char, piece_bb in self.get_all_piece_bitboards().items():
            pst_mg=PIECE_PST[piece_char]
            for square in self.get_set_bit_indices_efficient(piece_bb):
                score+=pst_mg[square]
        return score
    def get_positional_score_eg(self):
        score=0.0
        for piece_char, piece_bb in self.get_all_piece_bitboards().items():
            pst_mg=PIECE_PST[piece_char+'_end']
            for square in self.get_set_bit_indices_efficient(piece_bb):
                score+=pst_mg[square]
        return score
    def update_game_phase(self,move,undo_move=False):
        if move.piece_captured==None:
            return
        weight=1 if undo_move else -1
        if move.piece_captured.upper() in "BN":
            self.game_phase+=weight*1/24
        if move.piece_captured.upper()=='R':
            self.game_phase+=weight*2/24
        if move.piece_captured.upper()=='Q':
            self.game_phase+=weight*4/24
        return
    def update_material_score(self,move,undo_move=False):
        weight=-1 if undo_move else 1
        if move.piece_captured:
            self.material_score-=weight*PIECE_VALUES[move.piece_captured]  
        if move.promotion_piece:
            self.material_score+=weight*PIECE_VALUES[move.promotion_piece]      
    def update_positional_score(self,move,undo_move=False):
        self.update_positional_score_mg(move,undo_move)
        self.update_positional_score_eg(move,undo_move)
        self.update_game_phase(move,undo_move)
        self.positional_score=self.positional_score_mg*self.game_phase+self.positional_score_eg*(1-self.game_phase)
    def update_positional_score_mg(self,move,undo_move=False):
        piece_moved=move.piece_moved
        piece_reached=move.promotion_piece if move.promotion_piece else move.piece_moved
        weight=-1 if undo_move else 1
        self.positional_score_mg-=weight*PIECE_PST[piece_moved][move.from_square]
        self.positional_score_mg+=weight*PIECE_PST[piece_reached][move.to_square]
        if move.piece_captured:
            captured_piece=move.piece_captured
            self.positional_score_mg-=weight*PIECE_PST[captured_piece][move.to_square]
        if move.is_en_passant:
            pawn='p' if piece_moved.isupper() else 'P'
            self.positional_score_mg-=weight*PIECE_PST[pawn][move.from_square+(move.to_square%8 - move.from_square %8)]
    def update_positional_score_eg(self,move,undo_move=False):
        piece_moved=move.piece_moved
        piece_reached=move.promotion_piece if move.promotion_piece else move.piece_moved
        weight=-1 if undo_move else 1
        self.positional_score_eg-=weight*PIECE_PST[piece_moved+'_end'][move.from_square]
        self.positional_score_eg+=weight*PIECE_PST[piece_reached+'_end'][move.to_square]
        if move.piece_captured:
            captured_piece=move.piece_captured
            self.positional_score_eg-=weight*PIECE_PST[captured_piece+'_end'][move.to_square]
        if move.is_en_passant:
            pawn='p' if piece_moved.isupper() else 'P'
            self.positional_score_eg-=weight*PIECE_PST[pawn+'_end'][move.from_square+(move.to_square%8 - move.from_square %8)]

    @staticmethod
    def get_set_bit_indices_efficient(bb: int):
        indices=[]
        while bb>0:
            indices.append(BitboardChessBoard.get_lsb(bb))

            bb&=(bb-1)
        return indices
    def square_to_coords(self,square: int):
        file=(square % 8)+1
        rank=int(floor(square/ 8))+1
        return (rank,file)
    
    @staticmethod
    def get_lsb(bb:int):
        if bb==0:
            return -1
        return (bb & -bb).bit_length()-1  
    @staticmethod
    def get_msb(bb:int):
        if bb ==0:
            return -1
        return bb.bit_length()-1 
    def display(self,bb=None):
        if bb is None:
            bb=self.occupied
        bb_str= f'{bb:064b}'
        print("\n--- Aktuelles Spielfeld ---")
        print(f"Am Zug: {'Weiß' if self.turn == WHITE else 'Schwarz'}")
        print("  a b c d e f g h")
        print("-------------------")
        rank=''
        for number,char in enumerate(bb_str):
            if number%8 ==0:
                print(("  "+" ".join(rank[::-1])))
                rank=''
            rank+='.' if char=='0' else self.square_to_PIECE_MAP[63-number]
        
        print(("  "+" ".join(rank[::-1])))
        print("-------------------")
        print("  a b c d e f g h\n")
    def is_in_check(self):
        is_in_check=False
        king_bb=self.piece_bitboards[self.turn][KING]
        opponent_attacks=self.black_attacks if self.turn==WHITE else self.white_attacks
        if king_bb&opponent_attacks:
            is_in_check=True
        return is_in_check
    def puts_in_check(self,move: Move):
        piece_moved=move.piece_moved
        move_color=WHITE if piece_moved.isupper() else BLACK
        enemy_king_square=self.get_lsb(self.piece_bitboards[BLACK][KING]) if move.piece_moved.isupper() else self.get_lsb(self.piece_bitboards[WHITE][KING])
        BISHQUEEN='BQ' if move_color==WHITE else 'bq'
        ROOKQUEEN='RQ' if move_color==WHITE else 'rq'
        if piece_moved.upper()=='P':
            if 1<<move.to_square& self.possible_pawn_attack_squares(enemy_king_square,move_color):
                return True
        if piece_moved.upper()=='N':
            if 1<<move.to_square & self.possible_knight_attack_squares(enemy_king_square):
                return True
        if piece_moved.upper()=='B':
            if 1<< move.to_square & self.possible_bishop_attack_squares(enemy_king_square):
                return True
        if piece_moved.upper()=='R':
            if 1<<move.to_square & self.possible_rook_attack_squares(enemy_king_square):
                return True
        if piece_moved.upper()=='Q':
            if 1<<move.to_square & self.possible_queen_attack_squares(enemy_king_square):
                return True
        for direction in [0,1,2,3,4,5,6,7]:
            forwards=True if direction<=3 else False
            if move.from_square==self.get_first_blocker_square_on_ray(RAY_ATTACKS[direction][enemy_king_square],forwards):
                second_blocker_sq=self.get_second_blcoker_square_on_ray(RAY_ATTACKS[direction][enemy_king_square],first_blocker_sq=move.from_square)
                if second_blocker_sq==-1 or (1<<move.to_square & RAY_ATTACKS[direction][enemy_king_square]!=0):
                    continue
                if direction in [0,2,4,6] and self.square_to_PIECE_MAP[second_blocker_sq] in BISHQUEEN:
                    return True
                if direction in [1,3,5,6] and self.square_to_PIECE_MAP[second_blocker_sq] in ROOKQUEEN:
                    return True
        return False
    def has_enough_material_for_nmp(self):
        # Determine which player's pieces to check
        if self.turn == WHITE:
            # Check if White has any piece other than pawns or a king
            # A simple check is for rooks or queens
            if self.piece_bitboards[WHITE][ROOK] or self.piece_bitboards[WHITE][QUEEN]:
                return True
            # A more robust check might count minor pieces
            if bin(self.piece_bitboards[WHITE][KNIGHT]).count('1') + bin(self.piece_bitboards[WHITE][BISHOP]).count('1') > 1:
                return True
        else: # Black's turn
            if self.piece_bitboards[BLACK][ROOK] or self.piece_bitboards[BLACK][QUEEN]:
                return True
            if bin(self.piece_bitboards[BLACK][KNIGHT]).count('1') + bin(self.piece_bitboards[BLACK][BISHOP]).count('1') > 1:
                return True
                
        # If none of the above, material is low, so don't use NMP
        return False
    def get_first_blocker_square_on_ray(self,ray: int,forwards=True):
        blockers_on_ray=ray & self.occupied
        return self.get_lsb(blockers_on_ray) if forwards else self.get_msb(blockers_on_ray)
    def get_second_blcoker_square_on_ray(self,ray:int,forwards=True,first_blocker_sq=None):
        if first_blocker_sq==None:
            first_blocker_sq=self.get_first_blocker_square_on_ray(ray,forwards)
        
        return self.get_first_blocker_square_on_ray(ray^(1<<first_blocker_sq),forwards)
   
    def possible_bishop_attack_squares(self,square):
        attack_squares=0
        for directions in [0,2,4,6]:
            forward=True if directions<=2 else False
            first_blocker_sq=self.get_first_blocker_square_on_ray(RAY_ATTACKS[directions][square],forward)
            if first_blocker_sq==-1:
                attack_squares|=RAY_ATTACKS[directions][square]
            else:
                attack_squares|=RAY_ATTACKS[directions][square]^RAY_ATTACKS[directions][first_blocker_sq]
        return attack_squares
    def possible_rook_attack_squares(self,square):
        attack_squares=0
        for directions in [1,3,5,7]:
            forward=True if directions<=3 else False
            first_blocker_sq=self.get_first_blocker_square_on_ray(RAY_ATTACKS[directions][square],forward)
            if first_blocker_sq==-1:
                attack_squares|=RAY_ATTACKS[directions][square]
            else:
                attack_squares|=RAY_ATTACKS[directions][square]^RAY_ATTACKS[directions][first_blocker_sq]
        return attack_squares

    def possible_queen_attack_squares(self,square):
        return self.possible_bishop_attack_squares(square)| self.possible_rook_attack_squares(square)

    def possible_knight_attack_squares(self,square):
        return KNIGHT_ATTACKS[square]
    def possible_pawn_attack_squares(self,square,attack_color): 
        attack_squares=0
        square_bb=1<<square
        if attack_color==BLACK:
            if square//8==0:
                return 0
            attack_squares|=((square_bb<<9) & NOT_FILE_A)
            attack_squares|=((square_bb<<7) & NOT_FILE_H)
        else:
            if square//8==7:
                return 0
            attack_squares|=(square_bb>>(7)) & NOT_FILE_A
            attack_squares|=(square_bb>>(9)) & NOT_FILE_H
        return attack_squares
    def get_position_count_hash(self):
        hash=self.zobrist_hash
        if self.turn==BLACK:
            hash^=self.hasher.black_to_move_key
        for char in self.castling_rights:
            hash^=self.hasher.castling_keys[char]
        if self.en_passant_rights:
            hash^=self.hasher.en_passant_keys[self.en_passant_rights%8]
        return hash
    def is_threefold_repetition(self):
        return self.pos_count[self.get_position_count_hash()]>=3
    @property
    def white_pawn_attacks(self):
        ne_attacks=(self.piece_bitboards[WHITE][PAWN]<<9) & NOT_FILE_A
        nw_attacks=(self.piece_bitboards[WHITE][PAWN]<<7) & NOT_FILE_H
        return ne_attacks | nw_attacks
    @property
    def black_pawn_attacks(self):
        se_attacks=(self.piece_bitboards[BLACK][PAWN]>>7) & NOT_FILE_A
        sw_attacks=(self.piece_bitboards[BLACK][PAWN]>>9) & NOT_FILE_H
        return se_attacks | sw_attacks
    @property
    def white_knight_attacks(self):

        nne = (self.piece_bitboards[WHITE][KNIGHT]<<17) & NOT_FILE_A
        nnw = (self.piece_bitboards[WHITE][KNIGHT]<<15) & NOT_FILE_H
        ene = (self.piece_bitboards[WHITE][KNIGHT]<<10) & NOT_FILE_AB
        wnw = (self.piece_bitboards[WHITE][KNIGHT]<<6)  & NOT_FILE_GH

        ese = (self.piece_bitboards[WHITE][KNIGHT]>>6) & NOT_FILE_AB
        wsw = (self.piece_bitboards[WHITE][KNIGHT]>>10)& NOT_FILE_GH
        sse = (self.piece_bitboards[WHITE][KNIGHT]>>15)& NOT_FILE_A
        ssw = (self.piece_bitboards[WHITE][KNIGHT]>>17)& NOT_FILE_H

        return nne | nnw | ene | wnw | ese | wsw | sse | ssw
    @property
    def black_knight_attacks(self):
        nne = (self.piece_bitboards[BLACK][KNIGHT]<<17) & NOT_FILE_A
        nnw = (self.piece_bitboards[BLACK][KNIGHT]<<15) & NOT_FILE_H
        ene = (self.piece_bitboards[BLACK][KNIGHT]<<10) & NOT_FILE_AB
        wnw = (self.piece_bitboards[BLACK][KNIGHT]<<6)  & NOT_FILE_GH

        ese = (self.piece_bitboards[BLACK][KNIGHT]>>6) & NOT_FILE_AB
        wsw = (self.piece_bitboards[BLACK][KNIGHT]>>10)& NOT_FILE_GH
        sse = (self.piece_bitboards[BLACK][KNIGHT]>>15)& NOT_FILE_A
        ssw = (self.piece_bitboards[BLACK][KNIGHT]>>17)& NOT_FILE_H

        return nne | nnw | ene | wnw | ese | wsw | sse | ssw
    @property
    def white_bishop_attacks(self):
        positions=self.get_set_bit_indices_efficient(self.piece_bitboards[WHITE][BISHOP])
        attacks=0
        occupied=self.occupied^self.piece_bitboards[BLACK][KING]
        for square in positions:
            for direction in [0,2,4,6]:
                ray1=RAY_ATTACKS[direction][square]
                blockers_on_ray=ray1 & occupied
                if blockers_on_ray==0:
                    attacks|=ray1
                    continue
                first_blocker_square=self.get_lsb(blockers_on_ray) if 0<=direction<=3 else self.get_msb(blockers_on_ray)
                attacks|=(ray1^RAY_ATTACKS[direction][first_blocker_square])
        return attacks
    @property
    def black_bishop_attacks(self):
        positions=self.get_set_bit_indices_efficient(self.piece_bitboards[BLACK][BISHOP])
        attacks=0
        occupied=self.occupied^self.piece_bitboards[WHITE][KING]
        for square in positions:
            for direction in [0,2,4,6]:
                ray1=RAY_ATTACKS[direction][square]
                blockers_on_ray=ray1 & occupied
                if blockers_on_ray==0:
                    attacks|=ray1
                    continue
                first_blocker_square=self.get_lsb(blockers_on_ray) if 0<=direction<=3 else self.get_msb(blockers_on_ray)
                attacks|=(ray1^RAY_ATTACKS[direction][first_blocker_square])
        return attacks
    @property
    def white_rook_attacks(self):
        positions=self.get_set_bit_indices_efficient(self.piece_bitboards[WHITE][ROOK])
        attacks=0
        occupied=self.occupied^self.piece_bitboards[BLACK][KING]

        for square in positions:
            for direction in [1,3,5,7]:
                ray1=RAY_ATTACKS[direction][square]
                blockers_on_ray=ray1 & occupied
                if blockers_on_ray==0:
                    attacks|=ray1
                    continue
                first_blocker_square=self.get_lsb(blockers_on_ray) if 0<=direction<=3 else self.get_msb(blockers_on_ray)
                attacks|=(ray1^RAY_ATTACKS[direction][first_blocker_square])
        return attacks
    @property
    def black_rook_attacks(self):
        positions=self.get_set_bit_indices_efficient(self.piece_bitboards[BLACK][ROOK])
        attacks=0
        occupied=self.occupied^self.piece_bitboards[WHITE][KING]
        for square in positions:
            for direction in [1,3,5,7]:
                ray1=RAY_ATTACKS[direction][square]
                blockers_on_ray=ray1 & occupied
                if blockers_on_ray==0:
                    attacks|=ray1
                    continue
                first_blocker_square=self.get_lsb(blockers_on_ray) if 0<=direction<=3 else self.get_msb(blockers_on_ray)
                attacks|=(ray1^RAY_ATTACKS[direction][first_blocker_square])
        return attacks
    @property
    def white_queen_attacks(self):
        
        positions=self.get_set_bit_indices_efficient(self.piece_bitboards[WHITE][QUEEN])
        attacks=0
        occupied=self.occupied^self.piece_bitboards[BLACK][KING]
        for square in positions:
            for direction in range(8):
                ray1=RAY_ATTACKS[direction][square]
                blockers_on_ray=ray1 & occupied
                if blockers_on_ray==0:
                    attacks|=ray1
                    continue
                first_blocker_square=self.get_lsb(blockers_on_ray) if 0<=direction<=3 else self.get_msb(blockers_on_ray)
                attacks|=(ray1^RAY_ATTACKS[direction][first_blocker_square])
        return attacks
    @property
    def black_queen_attacks(self):
        positions=self.get_set_bit_indices_efficient(self.piece_bitboards[BLACK][QUEEN])
        attacks=0
        occupied=self.occupied^self.piece_bitboards[WHITE][KING]
        for square in positions:
            for direction in range(8):
                ray1=RAY_ATTACKS[direction][square]
                blockers_on_ray=ray1 & occupied
                if blockers_on_ray==0:
                    attacks|=ray1
                    continue
                first_blocker_square=self.get_lsb(blockers_on_ray) if 0<=direction<=3 else self.get_msb(blockers_on_ray)
                attacks|=(ray1^RAY_ATTACKS[direction][first_blocker_square])
        return attacks
    @property
    def white_king_attacks(self):
        ne=(self.piece_bitboards[WHITE][KING]<<9) & NOT_FILE_A
        n= (self.piece_bitboards[WHITE][KING]<<8)
        nw=(self.piece_bitboards[WHITE][KING]<<7) & NOT_FILE_H
        w=(self.piece_bitboards[WHITE][KING]>>1) & NOT_FILE_H
        sw=(self.piece_bitboards[WHITE][KING]>>9) & NOT_FILE_H
        s=(self.piece_bitboards[WHITE][KING]>>8) 
        se=(self.piece_bitboards[WHITE][KING]>>7) & NOT_FILE_A
        e=(self.piece_bitboards[WHITE][KING]<<1) & NOT_FILE_A
        return ne | n| nw | w | sw | s | se | e
    @property
    def black_king_attacks(self):
        ne=(self.piece_bitboards[BLACK][KING]<<9) & NOT_FILE_A
        n= (self.piece_bitboards[BLACK][KING]<<8)
        nw=(self.piece_bitboards[BLACK][KING]<<7) & NOT_FILE_H
        w=(self.piece_bitboards[BLACK][KING]>>1) & NOT_FILE_H
        sw=(self.piece_bitboards[BLACK][KING]>>9) & NOT_FILE_H
        s=(self.piece_bitboards[BLACK][KING]>>8) 
        se=(self.piece_bitboards[BLACK][KING]>>7) & NOT_FILE_A
        e=(self.piece_bitboards[BLACK][KING]<<1) & NOT_FILE_A
        return ne | n| nw | w | sw | s | se | e
    @property 
    def white_attacks(self):
        return (self.white_pawn_attacks | self.white_knight_attacks | 
                self.white_bishop_attacks | self.white_rook_attacks | 
                self.white_queen_attacks | self.white_king_attacks)
    @property
    def black_attacks(self):
        return (self.black_pawn_attacks | self.black_knight_attacks | 
                self.black_bishop_attacks | self.black_rook_attacks | 
                self.black_queen_attacks | self.black_king_attacks)
