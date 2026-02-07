import collections
import itertools

# ==========================================
# 核心逻辑 (保持原算法不变)
# ==========================================

CHAR_TO_RANK = {
    '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9,
    'T': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14, '2': 15,
    'X': 16, 'D': 17
}
RANK_TO_CHAR = {v: k for k, v in CHAR_TO_RANK.items()}

# 常量定义保持不变
TYPE_ROCKET = 'rocket'
TYPE_BOMB = 'bomb'
TYPE_SINGLE = 'single'
TYPE_PAIR = 'pair'
TYPE_TRIPLE = 'triple'
TYPE_TRIPLE_ONE = '3+1'
TYPE_TRIPLE_TWO = '3+2'
TYPE_STRAIGHT = 'straight'
TYPE_PAIR_STRAIGHT = 'pair_seq'
TYPE_PLANE = 'plane'
TYPE_PLANE_WING_S = 'plane_s'
TYPE_PLANE_WING_P = 'plane_p'
TYPE_QUAD_TWO = '4+2s'
TYPE_QUAD_TWO_PAIRS = '4+2p'

class Move:
    def __init__(self, cards, move_type, rank_val, length=0):
        self.cards = sorted(cards)
        self.type = move_type
        self.rank = rank_val
        self.length = length

    def __repr__(self):
        chars = "".join([RANK_TO_CHAR[c] for c in self.cards])
        return chars

    def __eq__(self, other):
        if other is None: return False
        return self.cards == other.cards and self.type == other.type

    def __hash__(self):
        return hash((tuple(self.cards), self.type))

class DoudizhuSolver:
    def __init__(self):
        self.memo = {} 
        self.nodes_searched = 0

    def _get_combinations(self, source_list, n):
        return list(itertools.combinations(source_list, n))

    def get_all_moves(self, hand_cards):
        # ... (此处保留原代码 get_all_moves 的完整逻辑) ...
        # 为节省篇幅，假设此处是原 get_all_moves 函数体
        # 在实际复制时，请确保包含原文件中该函数的全部内容
        moves = []
        counts = collections.Counter(hand_cards)
        unique_ranks = sorted(counts.keys())
        
        # 1. 火箭
        if 16 in hand_cards and 17 in hand_cards:
            moves.append(Move([16, 17], TYPE_ROCKET, 20))
        # 2. 炸弹
        for r in unique_ranks:
            if counts[r] == 4:
                moves.append(Move([r]*4, TYPE_BOMB, r))
        # 3. 基础
        for r in unique_ranks:
            moves.append(Move([r], TYPE_SINGLE, r))
            if counts[r] >= 2: moves.append(Move([r, r], TYPE_PAIR, r))
            if counts[r] >= 3:
                base = [r, r, r]
                moves.append(Move(base, TYPE_TRIPLE, r))
                remaining = list(hand_cards)
                for _ in range(3): remaining.remove(r)
                unique_rem = sorted(list(set(remaining)))
                for kicker in unique_rem:
                    moves.append(Move(base + [kicker], TYPE_TRIPLE_ONE, r))
                possible_pairs = [k for k in unique_ranks if k != r and counts[k] >= 2]
                for p_rank in possible_pairs:
                    moves.append(Move(base + [p_rank, p_rank], TYPE_TRIPLE_TWO, r))
        # 4. 四带
        for r in unique_ranks:
            if counts[r] == 4:
                base = [r]*4
                remaining = list(hand_cards)
                for _ in range(4): remaining.remove(r)
                if len(remaining) >= 2:
                    combs = set(itertools.combinations(remaining, 2))
                    for c1, c2 in combs:
                        moves.append(Move(base + [c1, c2], TYPE_QUAD_TWO, r))
                pairs = [k for k in unique_ranks if k != r and counts[k] >= 2]
                if len(pairs) >= 2:
                    for p1, p2 in itertools.combinations(pairs, 2):
                        moves.append(Move(base + [p1, p1, p2, p2], TYPE_QUAD_TWO_PAIRS, r))
        # 5. 顺子/连对
        valid_seq = [r for r in unique_ranks if r < 15]
        for length in range(5, 13):
            for i in range(len(valid_seq) - length + 1):
                seq = valid_seq[i : i+length]
                if seq[-1] - seq[0] == length - 1:
                    if all(counts[x] >= 1 for x in seq):
                        moves.append(Move(seq, TYPE_STRAIGHT, seq[0], length))
        for length in range(3, 11):
            for i in range(len(valid_seq) - length + 1):
                seq = valid_seq[i : i+length]
                if seq[-1] - seq[0] == length - 1:
                    if all(counts[x] >= 2 for x in seq):
                        cards = []
                        for x in seq: cards.extend([x, x])
                        moves.append(Move(cards, TYPE_PAIR_STRAIGHT, seq[0], length))
        # 6. 飞机
        triples = [r for r in valid_seq if counts[r] >= 3]
        if len(triples) >= 2:
            for length in range(2, 7):
                for i in range(len(triples) - length + 1):
                    seq = triples[i : i+length]
                    if seq[-1] - seq[0] == length - 1:
                        plane_body = []
                        for x in seq: plane_body.extend([x]*3)
                        moves.append(Move(plane_body, TYPE_PLANE, seq[0], length))
                        remaining = list(hand_cards)
                        for c in plane_body: remaining.remove(c)
                        if len(remaining) >= length:
                            wing_combs = set(itertools.combinations(remaining, length))
                            for wings in wing_combs:
                                moves.append(Move(plane_body + list(wings), TYPE_PLANE_WING_S, seq[0], length))
                        rem_counts = collections.Counter(remaining)
                        avail_pairs = [k for k in rem_counts if rem_counts[k] >= 2]
                        if len(avail_pairs) >= length:
                            pair_combs = itertools.combinations(avail_pairs, length)
                            for p_ranks in pair_combs:
                                wings = []
                                for p in p_ranks: wings.extend([p, p])
                                moves.append(Move(plane_body + wings, TYPE_PLANE_WING_P, seq[0], length))
        return moves

    def get_legal_moves(self, hand_cards, last_move=None):
        all_moves = self.get_all_moves(hand_cards)
        if last_move is None: return all_moves
        valid_moves = []
        if last_move.type == TYPE_ROCKET: return []
        for move in all_moves:
            if move.type == TYPE_ROCKET:
                valid_moves.append(move)
                continue
            if move.type == TYPE_BOMB:
                if last_move.type == TYPE_BOMB:
                    if move.rank > last_move.rank: valid_moves.append(move)
                else:
                    valid_moves.append(move)
                continue
            if move.type == last_move.type:
                if move.length == last_move.length:
                    if move.rank > last_move.rank:
                        valid_moves.append(move)
        return valid_moves

    def alpha_beta_search(self, my_hand, op_hand, turn, last_move, alpha, beta):
        # 保持原逻辑
        state_key = (tuple(sorted(my_hand)), tuple(sorted(op_hand)), turn, tuple(last_move.cards) if last_move else None)
        if state_key in self.memo: return self.memo[state_key]
        if not my_hand: return 100
        if not op_hand: return 0

        current_hand = my_hand if turn == 'landlord' else op_hand
        can_pass = (last_move is not None)
        legal_moves = self.get_legal_moves(current_hand, last_move)
        legal_moves.sort(key=lambda m: (m.type == TYPE_ROCKET, m.type == TYPE_BOMB, m.rank), reverse=True)

        if turn == 'landlord':
            v = 0
            for move in legal_moves:
                new_hand = list(current_hand)
                for c in move.cards: new_hand.remove(c)
                val = self.alpha_beta_search(new_hand, op_hand, 'peasant', move, alpha, beta)
                if val == 100:
                    v = 100; break
                v = max(v, val)
                alpha = max(alpha, v)
                if beta <= alpha: break
            if v != 100 and can_pass:
                val = self.alpha_beta_search(my_hand, op_hand, 'peasant', None, alpha, beta)
                v = max(v, val) if val != 100 else 100
                alpha = max(alpha, v)
            self.memo[state_key] = v
            return v
        else:
            v = 100
            for move in legal_moves:
                new_hand = list(current_hand)
                for c in move.cards: new_hand.remove(c)
                val = self.alpha_beta_search(my_hand, new_hand, 'landlord', move, alpha, beta)
                if val == 0:
                    v = 0; break
                v = min(v, val)
                beta = min(beta, v)
                if beta <= alpha: break
            if v != 0 and can_pass:
                val = self.alpha_beta_search(my_hand, op_hand, 'landlord', None, alpha, beta)
                v = min(v, val) if val == 0 else v
                beta = min(beta, v)
            self.memo[state_key] = v
            return v

    def get_best_strategy(self, landlord_hand, peasant_hand, last_move_by_peasant):
        self.memo = {} 
        self.nodes_searched = 0
        moves = self.get_legal_moves(landlord_hand, last_move_by_peasant)
        can_pass = (last_move_by_peasant is not None)
        best_move = None
        best_val = -1
        
        for move in moves:
            new_hand = list(landlord_hand)
            for c in move.cards: new_hand.remove(c)
            val = self.alpha_beta_search(new_hand, peasant_hand, 'peasant', move, -1, 101)
            if val == 100: return move, 100
            if val > best_val:
                best_val = val
                best_move = move
        
        if can_pass:
            pass_val = self.alpha_beta_search(landlord_hand, peasant_hand, 'peasant', None, -1, 101)
            if pass_val == 100: return None, 100
            if pass_val >= best_val:
                best_val = pass_val
                best_move = None
        
        return best_move, best_val
