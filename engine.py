from evaluation import evaluate
from evaluation import PIECE_VALUES
import time
from collections import defaultdict
MATE_SCORE = 1000000
MAX_PLY=50
WHITE, BLACK=0,1
PAWN,KNIGHT,BISHOP,ROOK,QUEEN,KING=0,1,2,3,4,5
PIECE_TYPE_MAP={
    'P': PAWN, 'N': KNIGHT, 'B': BISHOP, 'R':ROOK,'Q':QUEEN, 'K':KING
}
FUTILITY_MARGIN_D1=200
FUTILITY_MARGIN_D2=500
PIECE_CHAR_LIST='PNBRQK'
class TimeLimitExceededException(Exception):
    pass

class Engine:
    def __init__(self):
        self.transposition_table = {}
        self.stats = {'tt_hits': 0, 'cutoffs': 0, 'nodes_searched': 0, 'q_nodes': 0}
        self.killer_moves=[[None,None] for _ in range(MAX_PLY)]
        self.history_scores=[[0]*64 for _ in range(12)]
    def search(self, position, max_depth, time_limit_seconds=100):
        start_time = time.perf_counter()
        best_move_so_far = None
        best_score_so_far = None

        try:
            for current_depth in range(1, max_depth + 1):
                print(f"Suche mit Tiefe {current_depth}")
                eval_score, move,_ = self.find_best_move(position, current_depth, start_time, time_limit_seconds)
                duration = time.perf_counter() - start_time
                if move is not None:
                    best_move_so_far = move
                    best_score_so_far = eval_score
                    print(f"Tiefe {current_depth} beendet. Bester Zug bisher:{position.to_san(best_move_so_far, position.get_legal_moves())}, Bewertung {eval_score:.2f}, Zeit: {duration:.2f}s")
                if best_score_so_far is not None and abs(best_score_so_far) == MATE_SCORE:
                    print("Mate found, end search.")
                    break
        except TimeLimitExceededException:
            print(f"\n Time limit of {time_limit_seconds} reached! Seach is canceled.")
            if best_move_so_far:
                print(f"finale Entscheidung:{position.to_san(best_move_so_far, position.get_legal_moves())}")
        return best_move_so_far

    def find_best_move(self, position, depth, start_time, time_limit):
        best_move_eval = self._negamax(position, depth, -float('inf'), float('inf'), start_time, time_limit)
        return best_move_eval

    def _negamax(self,position,depth,alpha,beta,start_time, time_limit,ply=0):
        if time.perf_counter()-start_time>time_limit:
            raise TimeLimitExceededException()
        if position.is_threefold_repetition():
            return 0, None,True
        

        zobrist_hash=position.zobrist_hash
        original_alpha=alpha
        entry=self.transposition_table.get(zobrist_hash)

        if entry and entry['depth']>=depth:
            self.stats['tt_hits']+=1

            if entry['flag']=='EXACT':
                return entry['score'], entry.get('best_move'),False
            elif entry['flag'] == 'LOWERBOUND':
                alpha = max(alpha, entry['score'])
            elif entry['flag'] == 'UPPERBOUND':
                beta = min(beta, entry['score'])
            if beta <= alpha:
                return entry['score'], entry.get('best_move'),False

        self.stats['nodes_searched']+=1
        if depth==0:
            q_score,_=self._quiescence_search(position,alpha,beta,start_time,time_limit)
            return q_score,None,False
        
                # In your _negamax function

        # --- NULL MOVE PRUNING (NMP) ---
        if beta!=float('inf') and depth >= 3 and not position.is_in_check() and position.has_enough_material_for_nmp():

            # 1. Make the null move and save the original en passant state
            original_ep_square = position.make_null_move()

            # 2. Search with a reduced depth
            try:
                null_move_score, _,from_repeat= self._negamax(position, depth - 3, -beta, -beta + 1, start_time, time_limit, ply + 1)
                null_move_score = -null_move_score
            except TimeLimitExceededException:
                position.undo_null_move(original_ep_square)
                raise TimeLimitExceededException()

            # 3. Undo the null move, passing the saved state back to restore it
            position.undo_null_move(original_ep_square)

            # 4. If the score is still very high, prune
            if null_move_score >= beta:
                return beta, None, from_repeat
            

        #Futility Pruning Prerequesite:
        current_eval=None
        if depth<=2:
            color=1 if position.turn==WHITE else -1
            current_eval=evaluate(position)*color

        moves=self._get_sorted_moves(position,ply=ply)
        if not moves:
            if position.is_in_check():
                return -MATE_SCORE,None,False
            else:
                return 0, None,False
            
        best_score=-float('inf')
        best_move=None
        is_any_from_repeat=False
        is_best_from_repeat=False
        moves_searched=0
        for move in moves:
            is_quiet_move=move.piece_captured is None and move.promotion_piece is None
            if current_eval is not None and is_quiet_move and not position.is_in_check():
                if depth==1 and current_eval+FUTILITY_MARGIN_D1<=alpha:
                    continue
                if depth==2 and current_eval+FUTILITY_MARGIN_D2<=alpha:
                    continue
            moves_searched+=1
            reduction=0
            is_special_move=(move.piece_captured is not None) or \
                      (move.promotion_piece is not None) or \
                      (ply > 0 and move in self.killer_moves[ply])
            if not is_special_move and depth>=3 and moves_searched>3:
                reduction=2

            position.make_move(move)
            try:
                evaluation,_,from_repeat=self._negamax(position,depth-1-reduction,-beta,-alpha,start_time,time_limit,ply+1)
                evaluation=-evaluation
                if reduction>0 and evaluation>alpha:
                    evaluation,_,from_repeat=self._negamax(position,depth-1,-beta,-alpha,start_time,time_limit,ply+1)
                    evaluation=-evaluation
            except TimeLimitExceededException:
                position.undo_move(move)
                raise TimeLimitExceededException()
            position.undo_move(move)

            if evaluation>best_score:
                best_score=evaluation
                best_move=move
                is_any_from_repeat|=from_repeat
                is_best_from_repeat=from_repeat
            alpha=max(alpha,best_score)
            if beta<= alpha:
                self.stats['cutoffs']+=1
                if not move.piece_captured:
                    self.killer_moves[ply][1]=self.killer_moves[ply][0]
                    self.killer_moves[ply][0]=move
                    bonus=depth*depth
                    self.history_scores[move.piece_moved_type][move.to_square]+=bonus
                break
        flag_to_store=''
        if is_any_from_repeat and not is_best_from_repeat:
            if best_score>=beta:
                flag_to_store='LOWERBOUND '
                entry = {
                'score': best_score,
                'depth': depth,
                'flag': flag_to_store,
                'best_move': best_move
                }
                self.transposition_table[position.zobrist_hash] = entry
        elif not is_any_from_repeat:
            if best_score>=beta:
                flag_to_store='LOWERBOUND'
            elif best_score<=original_alpha:
                flag_to_store='UPPERBOUND'
            else:
                flag_to_store='EXACT'
            entry = {
                'score': best_score,
                'depth': depth,
                'flag': flag_to_store,
                'best_move': best_move
            }
            self.transposition_table[position.zobrist_hash] = entry
        
        return best_score, best_move, is_best_from_repeat




    def _get_sorted_moves(self, position,legal_moves=None,ply=-1):
        if legal_moves==None:
            legal_moves = position.get_legal_moves()
        scored_moves = []
        hash_move = None
        tt_entry = self.transposition_table.get(position.zobrist_hash)
        if tt_entry:
            hash_move = tt_entry.get('best_move')

        for move in legal_moves:
            score = 0
            is_capture = move.piece_captured is not None
            is_killer=False
            if ply>=0:
                is_killer= move in self.killer_moves[ply]
            if move == hash_move:
                score = 20000
            elif move.promotion_piece is not None:
                score = 12000 + PIECE_VALUES[move.promotion_piece.upper()]
            elif is_capture:
                difference=PIECE_VALUES[move.piece_captured.upper()] - PIECE_VALUES[move.piece_moved.upper()]
                if difference>=0:
                    score = 10000 + difference
                else:
                    score=-1000+difference
            elif is_killer:
                score =9000
            else:
                score=self.history_scores[move.piece_moved_type][move.to_square]
            
            scored_moves.append((score, move))

        scored_moves.sort(key=lambda item: item[0], reverse=True)
        return [move for score, move in scored_moves]
    def _quiescence_search(self,position,alpha,beta,start_time,time_limit,ply=0):
        DELTA_MARGIN=200
        if ply>=7:
            return evaluate(position),None
        pos_hash = position.zobrist_hash
        entry = self.transposition_table.get(pos_hash)
        if entry:
            if entry['flag'] == 'EXACT':
                return entry['score'], None
            elif entry['flag'] == 'LOWERBOUND':
                alpha = max(alpha, entry['score'])
            elif entry['flag'] == 'UPPERBOUND':
                beta = min(beta, entry['score'])
            if alpha >= beta:
                return entry['score'], None
            
        color = 1 if position.turn == WHITE else -1

        # Static evaluation is always from White's perspective, so we adjust
        stand_pat_score = evaluate(position) * color
        if stand_pat_score >= beta:
            return stand_pat_score, None
        
        original_alpha=alpha
        
        alpha = max(alpha, stand_pat_score)

        captures = position.get_captures()
        captures=self._get_sorted_moves(position,captures)
        best_score=stand_pat_score

        for move in captures:
            if move.piece_captured:
                capture_value=PIECE_VALUES[move.piece_captured.upper()]
                if stand_pat_score+capture_value+DELTA_MARGIN<alpha:
                    continue
            position.make_move(move)
            score,_=self._quiescence_search(position,-beta,-alpha,start_time,time_limit,ply+1)
            score=-score#
            position.undo_move(move)
            best_score=max(best_score,score)
            alpha=max(alpha,best_score)
            if alpha>=beta:
                break
        flag = ''
        if best_score >= beta:
            flag = 'LOWERBOUND'
        elif best_score<=original_alpha:
            flag = 'UPPERBOUND'
        else:
                flag = 'EXACT'
        if not self.transposition_table.get(pos_hash) or self.transposition_table[pos_hash]['depth'] == 0:
            self.transposition_table[pos_hash] = {'score': best_score, 'flag': flag, 'depth': 0}
        return best_score,None

    
    def clear_cache(self):
        self.transposition_table.clear()
    