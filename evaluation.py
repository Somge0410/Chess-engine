from constants import KING_ZONE_MASKS,KING_SHIELD_MASKS
import numpy as np
PIECE_VALUES = {
    'p': -100, 'n': -320, 'b': -330, 'r': -500, 'q': -900, 'k': -20000,
    'P': 100,  'N': 320,  'B': 330,  'R': 500,  'Q': 900,  'K': 20000
}
# --- Define Penalties and Bonuses ---
# These values can be tuned later to change the engine's style.
DOUBLED_PAWN_PENALTY = -17  # Penalty for each doubled pawn
ISOLATED_PAWN_PENALTY = -23 # Penalty for each isolated pawn

# Bonus for a passed pawn, scaled by how far advanced it is.
# Index corresponds to the pawn's rank (0-7).
WHITE_PASSED_PAWN_BONUS = [0, 10, 20, 35, 50, 75, 100, 0]
BLACK_PASSED_PAWN_BONUS = [0, 100, 75, 50, 35, 20, 10, 0]
PASSED_PAWN_BONUS=[WHITE_PASSED_PAWN_BONUS,BLACK_PASSED_PAWN_BONUS]
PAWN_SHIELD_BONUS=15
OPEN_FILE_PENALTY=-40
SEMI_OPEN_FILE_PENALTY=-20
ATTACKER_WEIGHTS={'P':0, 'N':10,'B':10,'R':15,'Q':25}
mg_white_pawn = np.flipud([
    [  0,   0,   0,   0,   0,   0,   0,   0],
    [ 98, 134,  61,  95,  68, 126,  34, -11],
    [ -6,   7,  26,  31,  65,  56,  25, -20],
    [-14,  13,   6,  21,  23,  12,  17, -23],
    [-27,  -2,  -5,  12,  17,   6,  10, -25],
    [-26,  -4,  -4, -10,   3,   3,  33, -12],
    [-35,  -1, -20, -23, -15,  24,  38, -22],
    [  0,   0,   0,   0,   0,   0,   0,   0]
]).flatten()

eg_white_pawn =np.flipud([
    [  0,   0,   0,   0,   0,   0,   0,   0],
    [178, 173, 158, 134, 147, 132, 165, 187],
    [ 94, 100,  85,  67,  56,  53,  82,  84],
    [ 32,  24,  13,   5,  -2,   4,  17,  17],
    [ 13,   9,  -3,  -7,  -7,  -8,   3,  -1],
    [  4,   7,  -6,   1,   0,  -5,  -1,  -8],
    [ 13,   8,   8,  10,  13,   0,   2,  -7],
    [  0,   0,   0,   0,   0,   0,   0,   0]
]).flatten()

mg_white_knight = np.flipud([
    [-167, -89, -34, -49,  61, -97, -15, -107],
    [ -73, -41,  72,  36,  23,  62,   7,  -17],
    [ -47,  60,  37,  65,  84, 129,  73,   44],
    [  -9,  17,  19,  53,  37,  69,  18,   22],
    [ -13,   4,  16,  13,  28,  19,  21,   -8],
    [ -23,  -9,  12,  10,  19,  17,  25,  -16],
    [ -29, -53, -12,  -3,  -1,  18, -14,  -19],
    [-105, -21, -58, -33, -17, -28, -19,  -23]
]).flatten()

eg_white_knight = np.flipud([
    [-58, -38, -13, -28, -31, -27, -63, -99],
    [-25,  -8, -25,  -2,  -9, -25, -24, -52],
    [-24, -20,  10,   9,  -1,  -9, -19, -41],
    [-17,   3,  22,  22,  22,  11,   8, -18],
    [-18,  -6,  16,  25,  16,  17,   4, -18],
    [-23,  -3,  -1,  15,  10,  -3, -20, -22],
    [-42, -20, -10,  -5,  -2, -20, -23, -44],
    [-29, -51, -23, -15, -22, -18, -50, -64]
]).flatten()

mg_white_bishop = np.flipud([
    [-29,   4, -82, -37, -25, -42,   7,  -8],
    [-26,  16, -18, -13,  30,  59,  18, -47],
    [-16,  37,  43,  40,  35,  50,  37,  -2],
    [ -4,   5,  19,  50,  37,  37,   7,  -2],
    [ -6,  13,  13,  26,  34,  12,  10,   4],
    [  0,  15,  15,  15,  14,  27,  18,  10],
    [  4,  15,  16,   0,   7,  21,  33,   1],
    [-33,  -3, -14, -21, -13, -12, -39, -21]
]).flatten()

eg_white_bishop = np.flipud([
    [-14, -21, -11,  -8,  -7,  -9, -17, -24],
    [ -8,  -4,   7, -12,  -3, -13,  -4, -14],
    [  2,  -8,   0,  -1,  -2,   6,   0,   4],
    [ -3,   9,  12,   9,  14,  10,   3,   2],
    [ -6,   3,  13,  19,   7,  10,  -3,  -9],
    [-12,  -3,   8,  10,  13,   3,  -7, -15],
    [-14, -18,  -7,  -1,   4,  -9, -15, -27],
    [-23,  -9, -23,  -5,  -9, -16,  -5, -17]
]).flatten()

mg_white_rook = np.flipud([
    [ 32,  42,  32,  51,  63,   9,  31,  43],
    [ 27,  32,  58,  62,  80,  67,  26,  44],
    [ -5,  19,  26,  36,  17,  45,  61,  16],
    [-24, -11,   7,  26,  24,  35,  -8, -20],
    [-36, -26, -12,  -1,   9,  -7,   6, -23],
    [-45, -25, -16, -17,   3,   0,  -5, -33],
    [-44, -16, -20,  -9,  -1,  11,  -6, -71],
    [-19, -13,   1,  17,  16,   7, -37, -26]
]).flatten()

eg_white_rook = np.flipud([
    [13, 10, 18, 15, 12, 12,  8,  5],
    [11, 13, 13, 11, -3,  3,  8,  3],
    [ 7,  7,  7,  5,  4, -3, -5, -3],
    [ 4,  3, 13,  1,  2,  1, -1,  2],
    [ 3,  5,  8,  4, -5, -6, -8,-11],
    [-4,  0, -5, -1, -7,-12, -8,-16],
    [-6, -6,  0,  2, -9, -9,-11, -3],
    [-9,  2,  3, -1, -5,-13,  4,-20]
]).flatten()

mg_white_queen =np.flipud( [
    [-28,   0,  29,  12,  59,  44,  43,  45],
    [-24, -39,  -5,   1, -16,  57,  28,  54],
    [-13, -17,   7,   8,  29,  56,  47,  57],
    [-27, -27, -16, -16,  -1,  17,  -2,   1],
    [ -9, -26,  -9, -10,  -2,  -4,   3,  -3],
    [-14,   2, -11,  -2,  -5,   2,  14,   5],
    [-35,  -8,  11,   2,   8,  15,  -3,   1],
    [ -1, -18,  -9,  10, -15, -25, -31, -50]
]).flatten()

eg_white_queen =np.flipud([
    [ -9,  22,  22,  27,  27,  19,  10,  20],
    [-17,  20,  32,  41,  58,  25,  30,   0],
    [-20,   6,   9,  49,  47,  35,  19,   9],
    [  3,  22,  24,  45,  57,  40,  57,  36],
    [-18,  28,  19,  47,  31,  34,  39,  23],
    [-16, -27,  15,   6,   9,  17,  10,   5],
    [-22, -23, -30, -16, -16, -23, -36, -32],
    [-33, -28, -22, -43,  -5, -32, -20, -41]
]).flatten()

mg_white_king =np.flipud([
    [-65,  23,  16, -15, -56, -34,   2,  13],
    [ 29,  -1, -20,  -7,  -8,  -4, -38, -29],
    [ -9,  24,   2, -16, -20,   6,  22, -22],
    [-17, -20, -12, -27, -30, -25, -14, -36],
    [-49,  -1, -27, -39, -46, -44, -33, -51],
    [-14, -14, -22, -46, -44, -30, -15, -27],
    [  1,   7,  -8, -64, -43, -16,   9,   8],
    [-15,  36,  12, -54,   8, -28,  24,  14]
]).flatten()

eg_white_king =np.flipud( [
    [-74, -35, -18, -18, -11,  15,   4, -17],
    [-12,  17,  14,  17,  17,  38,  23,  11],
    [ 10,  17,  23,  15,  20,  45,  44,  13],
    [ -8,  22,  24,  27,  26,  33,  26,   3],
    [-18,  -4,  21,  24,  27,  23,   9, -11],
    [-19,  -3,  11,  21,  23,  16,   7,  -9],
    [-27, -11,   4,  13,  14,   4,  -5, -17],
    [-53, -34, -21, -11, -28, -14, -24, -43]
]).flatten()

mg_black_pawn = np.flipud(np.array(mg_white_pawn)).flatten() * -1
mg_black_knight = np.flipud(np.array(mg_white_knight)).flatten() * -1
mg_black_bishop = np.flipud(np.array(mg_white_bishop)).flatten() * -1
mg_black_rook = np.flipud(np.array(mg_white_rook)).flatten() * -1
mg_black_queen = np.flipud(np.array(mg_white_queen)).flatten() * -1
mg_black_king = np.flipud(np.array(mg_white_king)).flatten() * -1

eg_black_pawn = np.flipud(np.array(eg_white_pawn)).flatten() * -1
eg_black_knight = np.flipud(np.array(eg_white_knight)).flatten() * -1
eg_black_bishop = np.flipud(np.array(eg_white_bishop)).flatten() * -1
eg_black_rook = np.flipud(np.array(eg_white_rook)).flatten() * -1
eg_black_queen = np.flipud(np.array(eg_white_queen)).flatten() * -1
eg_black_king = np.flipud(np.array(eg_white_king)).flatten() * -1
PIECE_PST={
    'P': mg_white_pawn,
    'N': mg_white_knight,
    'B': mg_white_bishop,
    'R': mg_white_rook,
    'Q': mg_white_queen,
    'K': mg_white_king,
    'p': mg_black_pawn,
    'n': mg_black_knight,
    'b': mg_black_bishop,
    'r': mg_black_rook,
    'q': mg_black_queen,
    'k': mg_black_king,
    'P_end': eg_white_pawn,
    'N_end': eg_white_knight,
    'B_end': eg_white_bishop,
    'R_end': eg_white_rook,
    'Q_end': eg_white_queen,
    'K_end': eg_white_king,
    'p_end': eg_black_pawn,
    'n_end': eg_black_knight,
    'b_end': eg_black_bishop,
    'r_end': eg_black_rook,
    'q_end': eg_black_queen,
    'k_end': eg_black_king,
}
WHITE, BLACK=0,1
PAWN,KNIGHT,BISHOP,ROOK,QUEEN,KING=0,1,2,3,4,5
PIECE_TYPE_MAP={
    'P': PAWN, 'N': KNIGHT, 'B': BISHOP, 'R':ROOK,'Q':QUEEN, 'K':KING
}
PIECE_CHAR_LIST='PNBRQK'
FILE_MASKS=[0x0101010101010101<<i for i in range(8)]
RANK_MASKS=[0xff<< 8*i for i in range(8)]
PASSED_PAWN_MASK=[[0]*64,[0]*64]
ADJACENT_FILES_MASKS=[0]*8
for i in range(8):
    if i==0:
        ADJACENT_FILES_MASKS[0]=FILE_MASKS[1]
    elif i==7:
        ADJACENT_FILES_MASKS[7]=FILE_MASKS[6]
    else:
        ADJACENT_FILES_MASKS[i]=FILE_MASKS[i-1]|FILE_MASKS[i+1]
for square in range(64):
    files=ADJACENT_FILES_MASKS[square%8]|FILE_MASKS[square%8]
    forward_ranks=0
    backward_ranks=0
    for row in range(square//8+1,8):
        forward_ranks|=RANK_MASKS[row]
    for row in range(square//8):
        backward_ranks|=RANK_MASKS[row]
    PASSED_PAWN_MASK[WHITE][square]=forward_ranks&files
    PASSED_PAWN_MASK[BLACK][square]=backward_ranks&files
    
def evaluate(position,new=True):
    game_phase=_get_game_phase_percentage(position)
    material_score=_calculate_material_score(position,new)
    positional_score=_calculate_positional_score(position,game_phase,new)
    pawn_structure_score=_calculate_pawn_structure_score(position)
    try:
        king_safety_score=_calculate_king_safety_score(position,game_phase)
    except KeyError:
        position.display_bitboard(position.piece_bitboards[WHITE][QUEEN])
        raise AttributeError
    final_score=material_score+positional_score+pawn_structure_score+king_safety_score
    return final_score

def _calculate_material_score(position,new):
    if not new:
        score=0
        score += bin(position.piece_bitboards[WHITE][PAWN]).count('1')   * PIECE_VALUES['P']
        score += bin(position.piece_bitboards[WHITE][KNIGHT]).count('1') * PIECE_VALUES['N']
        score += bin(position.piece_bitboards[WHITE][BISHOP]).count('1') * PIECE_VALUES['B']
        score += bin(position.piece_bitboards[WHITE][ROOK]).count('1')   * PIECE_VALUES['R']
        score += bin(position.piece_bitboards[WHITE][QUEEN]).count('1')  * PIECE_VALUES['Q']
        
        score += bin(position.piece_bitboards[BLACK][PAWN]).count('1')   * PIECE_VALUES['p']
        score += bin(position.piece_bitboards[BLACK][KNIGHT]).count('1') * PIECE_VALUES['n']
        score += bin(position.piece_bitboards[BLACK][BISHOP]).count('1') * PIECE_VALUES['b']
        score += bin(position.piece_bitboards[BLACK][ROOK]).count('1')   * PIECE_VALUES['r']
        score += bin(position.piece_bitboards[BLACK][QUEEN]).count('1')  * PIECE_VALUES['q']
    else:
        score=position.material_score
    return score

def _calculate_positional_score(position,game_phase,new=False):
    if not new:
        score=0
        for piece_char, piece_bb in get_all_piece_bitboards(position).items():
            pst_mg=PIECE_PST[piece_char]
            pst_eg=PIECE_PST[piece_char+'_end']
            for square in position.get_set_bit_indices_efficient(piece_bb):
                score+=pst_mg[square]*game_phase+pst_eg[square]*(1-game_phase)
    else:
        score=position.positional_score
    return score

def _calculate_pawn_structure_score(position):
    score=0
    #checks for doubled pawns
    for file_mask in FILE_MASKS:
        white_doubled=(position.piece_bitboards[WHITE][PAWN] & file_mask).bit_count()
        if white_doubled>1:
            score+=DOUBLED_PAWN_PENALTY*(white_doubled-1)
        black_doubled=(position.piece_bitboards[BLACK][PAWN]& file_mask).bit_count()
        if black_doubled>1:
            score-=DOUBLED_PAWN_PENALTY*(black_doubled-1)
    #checks for Isolated and passed pawns
    #for white:
    _calculate_isolated_passed_pawns_score(position,score,WHITE)
    #for black:
    _calculate_isolated_passed_pawns_score(position,score,BLACK)
    return score


def _calculate_isolated_passed_pawns_score(position,score,color):
    bb=position.piece_bitboards[color][PAWN]
    other_color=BLACK if color ==WHITE else WHITE
    weight=-1 if color==BLACK else 1
    while bb>0:
        pawn_square=position.get_lsb(bb)
        file_index=pawn_square %8
        if (position.piece_bitboards[color][PAWN] & ADJACENT_FILES_MASKS[file_index])==0:
            score+=ISOLATED_PAWN_PENALTY*weight
        if (position.piece_bitboards[other_color][PAWN] &PASSED_PAWN_MASK[color][pawn_square])==0:
            score+=PASSED_PAWN_BONUS[color][pawn_square//8]*weight
        bb &=(bb-1)

def _calculate_king_safety_score(position,game_phase):
    white_king_sq=position.get_lsb(position.piece_bitboards[WHITE][KING])
    black_king_sq=position.get_lsb(position.piece_bitboards[BLACK][KING])

    white_safety=_calculate_king_safety_for_side(position,white_king_sq,WHITE)
    black_safety=_calculate_king_safety_for_side(position,black_king_sq,BLACK)

    return (white_safety-black_safety)*game_phase

def _calculate_king_safety_for_side(position,king_sq,color):
    if king_sq==-1: return 0

    safety_score=0
    friendly_pawns=position.piece_bitboards[color][PAWN] 
    shield_mask=KING_SHIELD_MASKS[color][king_sq]
    shield_pawns=bin(friendly_pawns & shield_mask).count('1')
    safety_score+= shield_pawns*PAWN_SHIELD_BONUS

    zone_mask=KING_ZONE_MASKS[king_sq]
    enemy_pieces=position.color_bitboards[BLACK] if color==WHITE else position.color_bitboards[WHITE]
    attackers_in_zone=zone_mask & enemy_pieces

    attacker_weight_score=0
    
    for attacker_sq in position.get_set_bit_indices_efficient(attackers_in_zone):
        try:
            piece_char=position.square_to_PIECE_MAP[attacker_sq].upper()
        except:
            print(attacker_sq)
            # position.display_bitboard(position.piece_bitboards[WHITE][QUEEN])
            
            # position.display_bitboard(position.color_bitboards[0])
            # position.display_bitboard(position.piece_bitboards[WHITE][BISHOP])
            # position.display_bitboard(position.piece_bitboards[WHITE][ROOK])
            # position.display_bitboard(position.piece_bitboards[WHITE][KNIGHT])
            # position.display_bitboard(position.piece_bitboards[WHITE][PAWN])
            
            # position.display_bitboard(position.piece_bitboards[BLACK][PAWN])
            # position.display_bitboard(position.piece_bitboards[WHITE][QUEEN])
            # position.display_bitboard(enemy_pieces)
            
            
            raise KeyError()
        if piece_char in ATTACKER_WEIGHTS:
            attacker_weight_score+=ATTACKER_WEIGHTS[piece_char]*(6-abs(attacker_sq %8-king_sq%8)-abs(attacker_sq//8 -king_sq//8))/4
    safety_score-=attacker_weight_score

    return safety_score

    


def get_all_piece_bitboards(position):
    return {
        'P': position.piece_bitboards[WHITE][PAWN], 'N': position.piece_bitboards[WHITE][KNIGHT], 'B': position.piece_bitboards[WHITE][BISHOP],
        'R': position.piece_bitboards[WHITE][ROOK], 'Q': position.piece_bitboards[WHITE][QUEEN], 'K': position.piece_bitboards[WHITE][KING],
        'p': position.piece_bitboards[BLACK][PAWN], 'n': position.piece_bitboards[BLACK][KNIGHT], 'b': position.piece_bitboards[BLACK][BISHOP],
        'r': position.piece_bitboards[BLACK][ROOK], 'q': position.piece_bitboards[BLACK][QUEEN], 'k': position.piece_bitboards[BLACK][KING],
    }

def _get_game_phase_percentage(position):
    INITIAL_PHASE_VALUE=24

    knight_phase=bin(position.piece_bitboards[WHITE][KNIGHT]| position.piece_bitboards[BLACK][KNIGHT]).count('1')*1
    bishop_phase=bin(position.piece_bitboards[WHITE][BISHOP]|position.piece_bitboards[BLACK][BISHOP]).count('1')*1
    rook_phase=bin(position.piece_bitboards[WHITE][ROOK]|position.piece_bitboards[BLACK][ROOK]).count('1')*2
    queen_phase=bin(position.piece_bitboards[WHITE][QUEEN]| position.piece_bitboards[BLACK][QUEEN]).count('1')*4
    current_phase=knight_phase+bishop_phase+rook_phase+queen_phase

    return min(current_phase,INITIAL_PHASE_VALUE)/ INITIAL_PHASE_VALUE



