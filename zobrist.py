import random
from evaluation import get_all_piece_bitboards
MAX_HASH=0xFFFFFFFFFFFFFFFF

class ZobristHasher:
    def __init__(self):
        random.seed(123456789)
        self.time=0
        self.piece_keys={}
        pieces="PNBRQKpnbrqk"
        for piece in pieces:
            for square in range(64):
                self.piece_keys[(piece,square)]=random.randint(0,MAX_HASH)

        self.black_to_move_key=random.randint(0,MAX_HASH)

        self.castling_keys={
            'K': random.randint(0,MAX_HASH),
            'Q': random.randint(0,MAX_HASH),
            'k': random.randint(0,MAX_HASH),
            'q': random.randint(0,MAX_HASH),
        }
        self.en_passant_keys={}
        for col in range(8):
            self.en_passant_keys[col]=random.randint(0,MAX_HASH)

    def calculate_hash(self, position):
        h=0

        
        for piece_char, piece_bb in get_all_piece_bitboards(position).items():
            for square in position.get_set_bit_indices_efficient(piece_bb):
                h^=self.piece_keys[(piece_char,square)]
        if position.turn=='b':
            h^=self.black_to_move_key

        for char in "KQkq":
            if char in position.castling_rights:
                h^=self.castling_keys[char]
        if position.en_passant_rights is not None:
            h^=self.en_passant_keys[position.en_passant_rights%8]    

        return h    


    

