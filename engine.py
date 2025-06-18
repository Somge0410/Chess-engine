from evaluation import evalutate_position
from evaluation import PIECE_VALUES
import time
MATE_SCORE=1000000
class Engine:
    def __init__(self):
        self.transposition_table={}

    def search(self,position,max_depth,time_limit_seconds=100):
        start_time=time.perf_counter()
        best_move_so_far=None
        for current_depth in range(1,max_depth+1):
            print(f"Suche mit Tiefe {current_depth}")
            eval_score,move=self.find_best_move(position,current_depth)
            duration=time.perf_counter()-start_time
            
            if move is not None:
                best_move_so_far=move
                print(f"Tiefe {current_depth} beendet. Bester Zug bisher:{best_move_so_far.to_san()}, Bewertung {eval_score:.2f}, Zeit: {duration:.2f}s")
            if duration> time_limit_seconds:
                print(f"Zeitliit erreicht! Zeit: {duration} Stoppe die Suche bei Tiefe {current_depth}")
                break
        return best_move_so_far
    
    def find_best_move(self,position, depth):
        best_move_eval=self._minimax(position,depth,-float('inf'),float('inf'),position.turn=='w')
        return best_move_eval
    
    def _minimax(self,position,depth,alpha,beta,is_maximizing_player):
        if depth ==0:
            return (evalutate_position(position),None)
        moves=self._get_sorted_moves(position)
        if moves==[]:
            return (-MATE_SCORE + depth, None) if is_maximizing_player else (+MATE_SCORE - depth, None)
        if is_maximizing_player:
            max_eval=-float('inf')
            best_move=None
            for move in moves:
                position.make_move(move)
                evaluation, _ = self._minimax(position,depth-1,max_eval,beta,False)
                position.undo_move(move)

                if evaluation > max_eval:
                    max_eval=evaluation
                    best_move=move
                alpha=max(alpha,evaluation)
                if beta<=alpha:
                    break
            self.transposition_table[position.zobrist_hash] = {'score': max_eval, 'depth': depth, 'best_move': best_move}
            return max_eval, best_move
        else: 
            min_eval=float('inf')
            best_move=None
            for move in moves:
                position.make_move(move)
                evaluation,_=self._minimax(position,depth-1,alpha,min_eval,True)
                position.undo_move(move)

                if evaluation< min_eval:
                    min_eval = evaluation
                    best_move= move
                beta=min(beta,evaluation)
                if beta<= alpha:
                    break
            self.transposition_table[position.zobrist_hash] = {'score': min_eval, 'depth': depth, 'best_move': best_move}
            return min_eval, best_move
        
    
    def _get_sorted_moves(self,position):
        legal_moves=position.get_legal_moves()
        scored_moves=[]
        hash_move=None
        tt_entry=self.transposition_table.get(position.zobrist_hash)
        if tt_entry:
            hash_move=tt_entry.get('best_move')
        # is_maximizing_player= (position.turn=='w')
        # weight=1 if is_maximizing_player else -1
        # important_pieces=['Q','R','N','B']
        # other_player='b' if is_maximizing_player else 'w'
        for move in legal_moves:
            score=0
            is_capture=move.piece_captured is not None
            if move==hash_move:
                score=20000
            elif is_capture:
                score=1000+PIECE_VALUES[move.piece_captured.upper()]-PIECE_VALUES[move.piece_moved.upper()]
            elif move.promotion_piece is not None:
                score=9000+PIECE_VALUES[move.promotion_piece.upper()]    
            # elif move.piece_moved.upper() in important_pieces and position.is_square_attacked(move.start_row,move.start_col,other_player):
            #     if move.piece_moved.upper()=='Q':
            #         score=95000
            #     if move.piece_moved.upper()=='R':
            #         score=5000
            #     if move.piece_moved.upper()=='N' or move.piece_moved.upper()=='B':
            #         score=3200
            # else:
            #     position.make_move(move)
            #     # if position.in_check():
            #     #     score=400
            #     # else:
            #     score=weight*evalutate_position(position)
            #     position.undo_move(move)
            scored_moves.append((score,move))
        scored_moves.sort(key=lambda item: item[0],reverse=True)
        return [move for score,move in scored_moves]

    def clear_cache(self):
        self.transposition_table.clear()