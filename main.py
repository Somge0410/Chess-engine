from BitboardChessBoard import BitboardChessBoard, WHITE, BLACK
from move import Move, parse_move
import time

from zobrist import ZobristHasher
from engine import Engine
from evaluation import evaluate
from evaluation import _calculate_positional_score, _get_game_phase_percentage,RANK_MASKS,FILE_MASKS,ADJACENT_FILES_MASKS,PASSED_PAWN_MASK

def main():
    position=BitboardChessBoard()
    engine=Engine()
    print(position.square_to_PIECE_MAP)
    player=input("Choose a color, w for white, b for black.\n")
    player=WHITE if player=='w' else BLACK
    game_running=True

    while game_running:
        position.display()
        legal_moves=position.get_legal_moves()
        if not legal_moves:
            if position.is_in_check():
                winner = "Black" if position.turn==WHITE else 'White'
                print(f"Checkmate! {winner} wins.")
            else: 
                print("Stalemate! It's a draw.")
            game_running= False
            continue
        if position.turn==player:
            while True:
                move_str=input("Your Move:")
                if move_str.lower()=='exit':
                    game_running=False
                    break

                move_object=parse_move(move_str,position)
                if move_object:
                    position.make_move(move_object)
                    break
                else:
                    print("\n3!!! Invalid Move. Please try again. !!!\n")
        else: 
            print("\n Computer is thinking ...")
            best_move=engine.search(position,max_depth=30,time_limit_seconds=35)

            if best_move:
                print(f"Computer plays: {position.to_san(best_move,position.get_legal_moves())}")
                position.make_move(best_move)
            else:
                print("Engine cannot find a move. Game end.")
                game_running=False
        
if __name__ == "__main__":
    #main()
    pass

position=BitboardChessBoard("1rb1kb1r/2p2ppp/p2qp3/2ppN3/2PPn3/4PN2/PP3PPP/R1BQ1RK1 w k - 2 11")
position.display()
position.display_bitboard(PASSED_PAWN_MASK[1][59])
copy_position=position
legal_moves=position.get_legal_moves()
# print(evaluate(position))

# print(position.zobrist_hash)
engine=Engine()
engine.search(position,7,100000)
for move in legal_moves:
    if move.piece_moved.upper()=='P' and move.piece_captured!=None:    
        position.make_move(move)
        print(move.from_square)
        print(move.to_square)
        position.display()
        
        position.undo_move(move)
        
#rr4k1/2p2p1p/2P3p1/4b3/p2Np3/1P1bP3/P2B1PPP/R1R3K1 w - - 0 23