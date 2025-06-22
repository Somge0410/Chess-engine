PIECE_VALUES = {
    'p': -100, 'n': -320, 'b': -330, 'r': -500, 'q': -900, 'k': -20000,
    'P': 100,  'N': 320,  'B': 330,  'R': 500,  'Q': 900,  'K': 20000
}
# --- Define Penalties and Bonuses ---
# These values can be tuned later to change the engine's style.
DOUBLED_PAWN_PENALTY = -20  # Penalty for each doubled pawn
ISOLATED_PAWN_PENALTY = -25 # Penalty for each isolated pawn

# Bonus for a passed pawn, scaled by how far advanced it is.
# Index corresponds to the pawn's rank (0-7).
WHITE_PASSED_PAWN_BONUS = [0, 10, 20, 35, 50, 75, 100, 0]
BLACK_PASSED_PAWN_BONUS = [0, 100, 75, 50, 35, 20, 10, 0]
PAWN_SHIELD_BONUS=30
OPEN_FILE_PENALTY=-40
SEMI_OPEN_FILE_PENALTY=-20
ATTACKER_WEIGHTS={'P':0, 'N':2,'B':2,'R':3,'Q':5}
white_pawn= [[0,  0,  0,  0,  0,  0,  0,  0],\
             [50, 50, 50, 50, 50, 50, 50, 50],\
             [10, 10, 20, 30, 30, 20, 10, 10],\
             [5,  5, 10, 25, 25, 10,  5,  5],\
             [0,  0,  0, 20, 20,  0,  0,  0],\
             [5, -5,-10,  0,  0,-10, -5,  5],\
             [5, 10, 10,-20,-20, 10, 10,  5],\
             [0,  0,  0,  0,  0,  0,  0,  0]]
white_knight=[[-50,-40,-30,-30,-30,-30,-40,-50],\
              [-40,-20,  0,  0,  0,  0,-20,-40],\
              [-30,  0, 10, 15, 15, 10,  0,-30],\
              [-30,  5, 15, 20, 20, 15,  5,-30],\
              [-30,  0, 15, 20, 20, 15,  0,-30],\
              [-30,  5, 10, 15, 15, 10,  5,-30],\
              [-40,-20,  0,  5,  5,  0,-20,-40],\
              [-50,-40,-30,-30,-30,-30,-40,-50]]
white_bishop=[[-20,-10,-10,-10,-10,-10,-10,-20],\
              [-10,  0,  0,  0,  0,  0,  0,-10],\
              [-10,  0,  5, 10, 10,  5,  0,-10],\
              [-10,  5,  5, 10, 10,  5,  5,-10],\
              [-10,  0, 10, 10, 10, 10,  0,-10],\
              [-10, 10, 10, 10, 10, 10, 10,-10],\
              [-10,  5,  0,  0,  0,  0,  5,-10],\
              [-20,-10,-10,-10,-10,-10,-10,-20]]    
white_rook= [[0,  0,  0,  0,  0,  0,  0,  0],\
             [5, 10, 10, 10, 10, 10, 10,  5],\
             [-5,  0,  0,  0,  0,  0,  0, -5],\
             [-5,  0,  0,  0,  0,  0,  0, -5],\
             [-5,  0,  0,  0,  0,  0,  0, -5],\
             [-5,  0,  0,  0,  0,  0,  0, -5],\
             [-5,  0,  0,  0,  0,  0,  0, -5],\
             [0,  0,  0,  5,  5,  0,  0,  0]]
white_queen=[[-20,-10,-10, -5, -5,-10,-10,-20],\
             [-10,  0,  0,  0,  0,  0,  0,-10],\
             [-10,  0,  5,  5,  5,  5,  0,-10],\
             [-5,  0,  5,  5,  5,  5,  0, -5],\
             [0,  0,  5,  5,  5,  5,  0, -5],\
             [-10,  5,  5,  5,  5,  5,  0,-10],\
             [-10,  0,  5,  0,  0,  0,  0,-10],\
             [-20,-10,-10, -5, -5,-10,-10,-20]]
middle_game_white_king=[[-30,-40,-40,-50,-50,-40,-40,-30],\
                        [-30,-40,-40,-50,-50,-40,-40,-30],\
                        [-30,-40,-40,-50,-50,-40,-40,-30],\
                        [-30,-40,-40,-50,-50,-40,-40,-30],\
                        [-20,-30,-30,-40,-40,-30,-30,-20],\
                        [-10,-20,-20,-20,-20,-20,-20,-10],\
                        [20, 20,  0,  0,  0,  0, 20, 20],\
                        [20, 30, 10,  0,  0, 10, 30, 20]]
end_game_white_king=[[-50,-40,-30,-20,-20,-30,-40,-50],\
                     [-30,-20,-10,  0,  0,-10,-20,-30],\
                     [-30,-10, 20, 30, 30, 20,-10,-30],\
                     [-30,-10, 30, 40, 40, 30,-10,-30],\
                     [-30,-10, 30, 40, 40, 30,-10,-30],\
                     [-30,-10, 20, 30, 30, 20,-10,-30],\
                     [-30,-30,  0,  0,  0,  0,-30,-30],\
                     [-50,-30,-30,-30,-30,-30,-30,-50]]
def reverse_pst(table):
    return table[::-1]
black_pawn=reverse_pst(white_pawn)
black_knight=reverse_pst(white_knight)
black_bishop=reverse_pst(white_bishop)
black_rook=reverse_pst(white_rook)
black_queen=reverse_pst(white_queen)
middle_game_black_king=reverse_pst(middle_game_white_king)
end_game_black_king=reverse_pst(end_game_white_king)

PIECE_PST={
    'P': white_pawn,
    'N': white_knight,
    'B': white_bishop,
    'R': white_rook,
    'Q': white_queen,
    'K_mid': middle_game_white_king,
    'K_end': end_game_white_king,
    'p': black_pawn,
    'n': black_knight,
    'b': black_bishop,
    'r': black_rook,
    'q': black_queen,
    'k_mid': middle_game_black_king,
    'k_end': end_game_black_king
}
def evalutate_position(position):
    phase=get_game_phase_percentage(position)
    material_score=0
    positional_score=0
    pawn_structure_score=evaluate_pawn_structure(position)
    king_safety_score=evaluate_king_safety(position,phase)
    for r in range(8):
        for c in range(8):
            piece=position.board[r][c]
            if piece=='.':
                continue
            material_score+=PIECE_VALUES[piece]
            positional_score+=get_positional_score(piece,r,c,phase)

    final_score=material_score+positional_score+pawn_structure_score+king_safety_score
    return final_score

    

def get_positional_score(piece,r,c,phase):
    piece_type=piece.upper()
    if piece_type!='K':
        return PIECE_PST[piece][r][c] if piece.isupper() else -PIECE_PST[piece][r][c]
    else:
        mid_game_pst=PIECE_PST[piece+'_mid'][r][c]
        end_game_pst=PIECE_PST[piece+'_end'][r][c]
        score= (mid_game_pst*phase)+(end_game_pst)*(1-phase)
        score=score if piece.isupper() else -score
        return score

def get_game_phase_percentage(position):
    phase=0
    initial_value=24
    for r in range(8):
        for c in range(8):
            piece=position.board[r][c]
            if piece in '.KkPp':
                continue
            if piece == 'N' or piece == 'n': phase += 1
            if piece == 'B' or piece == 'b': phase += 1
            if piece == 'R' or piece == 'r': phase += 2
            if piece == 'Q' or piece == 'q': phase += 4
    return phase/initial_value


    



def evaluate_pawn_structure(board):
    """
    Analyzes the pawn structure for both sides and returns a score.
    + score is good for White, - score is good for Black.
    """
    score = 0
    
    # 1. First, map out all pawn locations by file for efficient access
    white_pawns_on_file = {i: [] for i in range(8)}
    black_pawns_on_file = {i: [] for i in range(8)}

    for r in range(8):
        for c in range(8):
            piece = board.board[r][c]
            if piece == 'P':
                white_pawns_on_file[c].append(r)
            elif piece == 'p':
                black_pawns_on_file[c].append(r)

    # 2. Now, iterate through the files and evaluate the structure
    for c in range(8):
        # --- Evaluate White's Pawns on this file ---
        if white_pawns_on_file[c]:
            # a) Check for doubled pawns
            if len(white_pawns_on_file[c]) > 1:
                score += DOUBLED_PAWN_PENALTY * (len(white_pawns_on_file[c]) - 1)

            # b) Check for isolated and passed pawns for each pawn on the file
            for r in white_pawns_on_file[c]:
                is_isolated = True
                # Check left adjacent file (if it exists)
                if c > 0 and white_pawns_on_file[c-1]:
                    is_isolated = False
                # Check right adjacent file (if it exists)
                if c < 7 and white_pawns_on_file[c+1]:
                    is_isolated = False
                
                if is_isolated:
                    score += ISOLATED_PAWN_PENALTY

                # c) Check for passed pawns
                if is_white_pawn_passed(r, c, black_pawns_on_file):
                    score += WHITE_PASSED_PAWN_BONUS[r]

        # --- Evaluate Black's Pawns on this file (symmetrical logic) ---
        if black_pawns_on_file[c]:
            # a) Check for doubled pawns
            if len(black_pawns_on_file[c]) > 1:
                score -= DOUBLED_PAWN_PENALTY * (len(black_pawns_on_file[c]) - 1)

            # b) Check for isolated and passed pawns
            for r in black_pawns_on_file[c]:
                is_isolated = True
                if c > 0 and black_pawns_on_file[c-1]:
                    is_isolated = False
                if c < 7 and black_pawns_on_file[c+1]:
                    is_isolated = False

                if is_isolated:
                    score -= ISOLATED_PAWN_PENALTY
                
                # c) Check for passed pawns
                if is_black_pawn_passed(r, c, white_pawns_on_file):
                    score -= BLACK_PASSED_PAWN_BONUS[r]
                    
    return score


def is_white_pawn_passed(r, c, black_pawns_on_file):
    """Checks if a white pawn at (r, c) is a passed pawn."""
    # Check current file in front of the pawn
    if any(br < r for br in black_pawns_on_file[c]):
        return False
    # Check left adjacent file
    if c > 0 and any(br < r for br in black_pawns_on_file[c-1]):
        return False
    # Check right adjacent file
    if c < 7 and any(br < r for br in black_pawns_on_file[c+1]):
        return False
    return True

def is_black_pawn_passed(r, c, white_pawns_on_file):
    """Checks if a black pawn at (r, c) is a passed pawn."""
    # Check current file in front of the pawn
    if any(wr > r for wr in white_pawns_on_file[c]):
        return False
    # Check left adjacent file
    if c > 0 and any(wr > r for wr in white_pawns_on_file[c-1]):
        return False
    # Check right adjacent file
    if c < 7 and any(wr > r for wr in white_pawns_on_file[c+1]):
        return False
    return True

def evaluate_king_safety(position,phase):
    white_king_pos,black_king_pos=position.white_king_pos, position.black_king_pos
    white_safety=_calculate_safety_for_king(white_king_pos,position,'w')
    black_safety=_calculate_safety_for_king(black_king_pos,position,'b')
    safety_difference=white_safety-black_safety
    return int(safety_difference*phase)

def _calculate_safety_for_king(king_pos,position,color):
    if king_pos is None:
        return 0
    kr, kc=king_pos
    board=position.board
    safety_score=0

    for c_offset in range(-1,2):
        file=kc+c_offset
        if 0<= file <=7:
           # Find the first piece on this file in front of the king
            found_friendly_pawn = False
            found_enemy_pawn = False
            
            # Determine direction based on color
            search_range = range(kr - 1, -1, -1) if color == 'w' else range(kr + 1, 8)
            
            for r in search_range:
                piece = board[r][file]
                if piece == ('P' if color == 'w' else 'p'):
                    found_friendly_pawn = True
                    # Bonus for a pawn directly in front or one step away
                    if abs(r - kr) <= 2:
                        safety_score += PAWN_SHIELD_BONUS
                    break # Stop searching on this file
                elif piece == ('p' if color == 'w' else 'P'):
                    found_enemy_pawn = True
                    break # Stop searching on this file

            if not found_friendly_pawn:
                if not found_enemy_pawn:
                    safety_score += OPEN_FILE_PENALTY # Open file
                else:
                    safety_score += SEMI_OPEN_FILE_PENALTY # Semi-open file 

    # --- 2. Evaluate Attacker Proximity ("King's Zone") ---
    attack_score = 0
    # Define a 5x5 square "zone" around the king
    for r_offset in range(-2, 3):
        for c_offset in range(-2, 3):
            r, c = kr + r_offset, kc + c_offset
            if 0 <= r < 8 and 0 <= c < 8:
                piece = board[r][c]
                # If the piece is an enemy piece
                if piece != '.' and piece.islower() != (color == 'b'):
                    piece_type = piece.upper()
                    if piece_type in ATTACKER_WEIGHTS:
                        attack_score += ATTACKER_WEIGHTS[piece_type]

    safety_score -= (attack_score * 10) # Apply the attacker penalty

    return safety_score
