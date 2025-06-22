from evaluation import evalutate_position
from evaluation import PIECE_VALUES
import time
MATE_SCORE=1000000
class TimeLimitExceededException(Exception):
    pass
class Engine:
    def __init__(self):
        self.transposition_table={}
        self.stats={'tt_hits':0, 'cutoffs':0, 'nodes_searched':0,'q_nodes':0}

    def search(self,position,max_depth,time_limit_seconds=100):
        start_time=time.perf_counter()
        best_move_so_far=None
        best_score_so_far=None

        try: 
             for current_depth in range(1,max_depth+1):
                print(f"Suche mit Tiefe {current_depth}")
                eval_score,move=self.find_best_move(position,current_depth,start_time,time_limit_seconds)
                duration=time.perf_counter()-start_time
            
                if move is not None:
                    best_move_so_far=move
                    best_score_so_far=eval_score
                    print(f"Tiefe {current_depth} beendet. Bester Zug bisher:{best_move_so_far.to_san()}, Bewertung {eval_score:.2f}, Zeit: {duration:.2f}s")
                if abs(best_score_so_far)==MATE_SCORE:
                    print("Mate found, end search.")
                    break
        except TimeLimitExceededException:
            print(f"\n Time limit of {time_limit_seconds} reached! Seach is canceled.")
            print(f"finale Entscheidung:{best_move_so_far.to_san()}")
        return best_move_so_far



       
    
    def find_best_move(self,position, depth,start_time,time_limit):

        best_move_eval=self._minimax(position,depth,-float('inf'),float('inf'),position.turn=='w',start_time,time_limit)
        return best_move_eval
    
    def _minimax(self,position,depth,alpha,beta,is_maximizing_player,start_time,time_limit):
        if time.perf_counter() - start_time > time_limit:
            raise TimeLimitExceededException()
        zobrist_hash = position.zobrist_hash 
        entry = self.transposition_table.get(zobrist_hash)
        original_alpha=alpha
        original_beta=beta
        if entry and entry['depth'] >= depth:
            self.stats['tt_hits'] += 1 
        
            if entry['flag'] == 'EXACT':
                return (entry['score'], entry.get('best_move'))
        
       
            elif entry['flag'] == 'LOWERBOUND':
                alpha = max(alpha, entry['score'])
            elif entry['flag'] == 'UPPERBOUND':
                beta = min(beta, entry['score'])
            if beta <= alpha:
                return (entry['score'], entry.get('best_move'))
        self.stats['nodes_searched']+=1
        if depth ==0:
            return self._quiescence_search(position,alpha,beta,is_maximizing_player,start_time,time_limit)
            #return evalutate_position(position),None
        moves=self._get_sorted_moves(position)
        if moves==[] :
            if position.in_check():
                return (-MATE_SCORE, None) if is_maximizing_player else (+MATE_SCORE, None)
            else:
                return 0,None
        if is_maximizing_player:
            max_eval=-float('inf')
            best_move=None
            for move in moves:
                position.make_move(move)
                try:
                    evaluation, _ = self._minimax(position,depth-1,alpha,beta,False,start_time,time_limit)
                except TimeLimitExceededException:
                    position.undo_move(move)
                    raise TimeLimitExceededException()
                position.undo_move(move)

                if evaluation > max_eval:
                    max_eval=evaluation
                    best_move=move
                alpha=max(alpha,evaluation)
                if beta<=alpha:
                    self.stats['cutoffs'] +=1
                    break
            flag_to_store = ''
            if max_eval >= beta:
                flag_to_store = 'Lowerbound'
            elif max_eval<=original_alpha:
                flag_to_store='Upperbound'
            else:
                flag_to_store = 'EXACT'
            
            entry = {
                'score': max_eval,
                'depth': depth,
                'flag': flag_to_store,
                'best_move': best_move
             }
            
            self.transposition_table[position.zobrist_hash] = entry
            return max_eval, best_move
        else: 
            min_eval=float('inf')
            best_move=None
            for move in moves:
                position.make_move(move)
                try:
                    evaluation,_=self._minimax(position,depth-1,alpha,beta,True,start_time,time_limit)
                except TimeLimitExceededException:
                    position.undo_move(move)
                    raise TimeLimitExceededException()
                position.undo_move(move)

                if evaluation< min_eval:
                    min_eval = evaluation
                    best_move= move
                beta=min(beta,evaluation)
                if beta<= alpha:
                    self.stats['cutoffs']+=1
                    break
            flag_to_store = ''
            if min_eval <= alpha:
                flag_to_store = 'UPPERBOUND'
            elif min_eval>= original_beta:
                flag_to_store='LOWERBOUND'
            else:
                flag_to_store = 'EXACT'
            
            entry = {
                'score': min_eval,
                'depth': depth,
                'flag': flag_to_store,
                'best_move': best_move
             }
            self.transposition_table[position.zobrist_hash] = entry
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
    def _quiescence_search(self,position,alpha,beta,is_maximizing_player,start_time,time_limit):
        if time.perf_counter()-start_time>time_limit:
            raise TimeLimitExceededException()
        self.stats['q_nodes']+=1
        stand_pat_score=evalutate_position(position)

        if is_maximizing_player:
            if stand_pat_score>=beta:
                return stand_pat_score,None
            alpha=max(alpha,stand_pat_score)
        else:
            if stand_pat_score<=alpha:
                return stand_pat_score,None
            beta=min(beta,stand_pat_score)

        captures=[move for move in self._get_sorted_moves(position) if (move.piece_captured is not None) or position.puts_in_check(move)]
        for move in captures:
            position.make_move(move)
            try: 
                score,_ =self._quiescence_search(position,alpha,beta, not is_maximizing_player,start_time,time_limit)
            except TimeLimitExceededException:
                position.undo_move(move)
                raise TimeLimitExceededException()
            position.undo_move(move)
            if is_maximizing_player:
                if score>stand_pat_score:
                    stand_pat_score=score
                if stand_pat_score>= beta:
                    return stand_pat_score, None
                alpha=max(alpha,stand_pat_score)
            else:
                if score<stand_pat_score:
                    stand_pat_score=score
                if stand_pat_score<=alpha:
                    return stand_pat_score,None
                beta=min(beta,stand_pat_score)
        return stand_pat_score, None
            

    def clear_cache(self):
        self.transposition_table.clear()