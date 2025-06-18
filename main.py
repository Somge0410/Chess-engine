from ChessBoard import ChessBoard
from evaluation import evalutate_position
from engine import Engine
import time
from zobrist import ZobristHasher

hasher=ZobristHasher()
position=ChessBoard(hasher,)
engine= Engine()
best_move=engine.search(position,5)