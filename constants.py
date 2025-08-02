import pickle
STARTING_FEN="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

with open('ray_attacks.pkl','rb') as f:
    RAY_ATTACKS=pickle.load(f)
with open('knight_attacks.pkl','rb') as f:
    KNIGHT_ATTACKS=pickle.load(f)
with open('king_attacks.pkl','rb') as f:
    KING_ATTACKS=pickle.load(f)
with open('pawn_attacks.pkl','rb') as f:
    PAWN_ATTACKS=pickle.load(f)
with open('king_zone_masks.pkl','rb') as f:
    KING_ZONE_MASKS=pickle.load(f)
with open('king_shield_masks.pkl','rb') as f:
    KING_SHIELD_MASKS=pickle.load(f)
FILES={'a':0,'b':1, 'c':2, 'd':3, 'e':4,'f':5,'g':6, 'h':7}
NOT_FILE_A = 0xfefefefefefefefe
NOT_FILE_H = 0x7f7f7f7f7f7f7f7f
NOT_FILE_AB= 0xfcfcfcfcfcfcfcfc
NOT_FILE_GH= 0x3f3f3f3f3f3f3f3f
BOARD_ALL_SET=0xFFFFFFFFFFFFFFFF
PIECE_MAP={
            'P': 'white_pawns', 'N': 'white_knights', 'B': 'white_bishops', 'R':'white_rooks',
            'Q': 'white_queens', 'K': 'white_king',
            'p': 'black_pawns', 'n': 'black_knights', 'b': 'black_bishops', 'r':'black_rooks',
            'q': 'black_queens', 'k': 'black_king',
        }
COLOR_MAP={
    'w': 'all_white_pieces', 'b': 'all_black_pieces'
}


LSB_LOOKUP_TABLE = {1 << i: i for i in range(64)}