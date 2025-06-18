import random
import time
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

    def calculate_hash(self, board_obj):
        start=time.perf_counter()
        h=0

        for r in range(8):
            for c in range(8):
                piece=board_obj.board[r][c]
                if piece !='.':
                    square_index= r*8+c
                    h^= self.piece_keys[(piece,square_index)]
        if board_obj.turn =='b':
            h^=self.black_to_move_key
        
        for char in "KQkq":
            if char in board_obj.castling_rights:
                h^=self.castling_keys[char]
        if board_obj.en_passant is not None:
            h^=self.en_passant_keys[board_obj.en_passant[0]]    
        self.time+=time.perf_counter()-start    
        return h    