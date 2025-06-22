from ChessBoard import ChessBoard
from evaluation import evalutate_position
from engine import Engine
from move import Move
import time
from zobrist import ZobristHasher

def main():
    hasher=ZobristHasher()
    position=ChessBoard(hasher,"5k2/8/8/6Q1/8/8/PPP2P1P/4R1K1 w - - 5 38")
    engine=Engine()
    player=input("Choose a color, w for white, b for black.\n")
    game_running=True

    while game_running:
        position.display()
        legal_moves=position.get_legal_moves()
        if not legal_moves:
            if position.in_check():
                winner = "Black" if position.turn=='w' else 'White'
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

                move_object=position.parse_move(move_str)
                if move_object:
                    position.make_move(move_object)
                    break
                else:
                    print("\n!!! Invalid Move. Please try again. !!!\n")
        else: 
            print("\n Computer is thinking ...")
            best_move=engine.search(position,max_depth=30,time_limit_seconds=9)

            if best_move:
                print(f"Computer plays: {best_move.to_san()}")
                position.make_move(best_move)
            else:
                print("Engine cannot find a move. Game end.")
                game_running=False
        
if __name__ == "__main__":
    main()

