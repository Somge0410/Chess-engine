DIRECTIONS=[7,8,9,1,-7,-8,-9,-1]
RAY_ATTACKS={}
for i in range(8):
    RAY_ATTACKS[i]=[0]*64
LINE_BETWEEN=[[0]*64 for _ in range(64)]
KNIGHT_DIRECTION=[6,15,17,10,-6,-17,-15,-10]
KNIGHT_ATTACKS=[0]*64
KING_ATTACKS=[0]*64
WHITE=0
BLACK=1
PAWN_ATTACKS={WHITE: [0]*64, BLACK:[0]*64}
KING_SHIELD_MASKS={WHITE: [0]*64, BLACK:[0]*64}
KING_ZONE_MASKS=[0]*64
for square in range(64):
    for direction_anz, direction in enumerate(DIRECTIONS):
        ray_bb=0
        target_square=square+direction

        while 0<=target_square<64:
            if abs((target_square % 8)-((target_square-direction) % 8))>1:
                break
            ray_bb|=  (1<< target_square)
            target_square+=direction
        RAY_ATTACKS[direction_anz][square]=ray_bb


for from_sq in range(64):
    for to_sq in range(64):
        r1,f1=from_sq//8, from_sq % 8
        r2,f2=to_sq//8, to_sq %8
        step=0
        line_bb=0
        if r1==r2 or f1==f2 or abs(r1-r2)==abs(f1-f2):
            rank_step=(r2>r1)-(r2<r1)
            file_step=(f2>f1) -(f2<f1)
            step=rank_step*8+file_step
            current_sq=from_sq
            while current_sq!= to_sq:
                line_bb|=(1<< current_sq)
                current_sq+= step
            line_bb|=(1<< to_sq)
        LINE_BETWEEN[from_sq][to_sq]=line_bb
RAY_ATTACKS['line']=LINE_BETWEEN


for square in range(64):
    attack=0
    for direction in KNIGHT_DIRECTION:
        target_square=square+direction
        if abs(target_square %8 - square %8)>2:
            continue
        if 0<=target_square<64:
            attack|=(1<<target_square)
    KNIGHT_ATTACKS[square]=attack

for square in range(64):
    ray_bb=0
    for direction in DIRECTIONS:
        if abs((square % 8)-((square+direction) % 8))>1:
            continue
        if 0<= square+direction<64:
            ray_bb|=  (1<< (square+direction))
    KING_ATTACKS[square]=ray_bb
for square in range(64):
    if square%8==0:
        PAWN_ATTACKS[WHITE][square]=(1<< square+9) if square+9 <64 else 0
        PAWN_ATTACKS[BLACK][square]=(1<< (square-7)) if square-7>=0 else 0
    elif square%8 ==7:
        PAWN_ATTACKS[WHITE][square]=(1<< square+7) if square+7<64 else 0
        PAWN_ATTACKS[BLACK][square]=(1<< (square-9)) if square-9>=0 else 0
    else:
        PAWN_ATTACKS[WHITE][square]=(1<<square+9)|(1<<square+7) if square+9<64 else 0
        PAWN_ATTACKS[BLACK][square]=(1<<square-9) |(1<< square-7) if square-9>=0 else 0
for square in range(64):
    r,f=square //8,square%8

    schield_bb=0
    if f==0:
        if r<7:
            KING_SHIELD_MASKS[WHITE][square]=(1<<square+8)|(1<< square+9)
        if r>0:
            KING_SHIELD_MASKS[BLACK][square]=((1<<square-8))|(1<< square-7)
    elif f==7:
        if r<7:
            KING_SHIELD_MASKS[WHITE][square]=(1<<square+8)|(1<< square+7)
        if r>0:
            KING_SHIELD_MASKS[BLACK][square]=((1<<square-8))|(1<< square-9)
    else:
        if r<7:
            KING_SHIELD_MASKS[WHITE][square]=(1<<square+8)|(1<< square+9)|(1<<square+7)
        if r>0:
            KING_SHIELD_MASKS[BLACK][square]=((1<<square-8))|(1<< square-7)|(1<<square-9)

for square in range(64):
    direction=[-18,-17,-16,-15,-14,-10,-9,-8,-7,-6,-5,-2,-1,1,2,6,7,8,9,10,14,15,16,17,18]
    bb=0
    for d in direction:
            if 0<=square +d<64:
                if abs(square %8 -(square+d) % 8)>2:
                    continue
                else:
                    bb|=(1<< square+d)
    KING_ZONE_MASKS[square]=bb


import pickle
with open('ray_attacks.pkl','wb') as f:
    pickle.dump(RAY_ATTACKS,f)
with open('knight_attacks.pkl','wb') as f:
    pickle.dump(KNIGHT_ATTACKS,f)
with open('king_attacks.pkl','wb') as f:
    pickle.dump(KING_ATTACKS,f)
with open('pawn_attacks.pkl','wb') as f:
    pickle.dump(PAWN_ATTACKS,f)
with open('king_zone_masks.pkl','wb') as f:
    pickle.dump(KING_ZONE_MASKS,f)
with open('king_shield_masks.pkl','wb') as f:
    pickle.dump(KING_SHIELD_MASKS,f)