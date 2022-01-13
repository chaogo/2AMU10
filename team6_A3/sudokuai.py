#  (C) Copyright Wieger Wesselink 2021. Distributed under the GPL-3.0-or-later
#  Software License, (See accompanying file LICENSE or copy at
#  https://www.gnu.org/licenses/gpl-3.0.txt)

from competitive_sudoku.sudoku import GameState, Move, TabooMove
import competitive_sudoku.sudokuai
from operator import attrgetter


class SudokuAI(competitive_sudoku.sudokuai.SudokuAI):
    """
    Sudoku AI that computes a move for a given sudoku configuration.
    """

    def __init__(self):
        super().__init__()

    def compute_best_move(self, game_state: GameState) -> None:
        N = game_state.board.N
        n = game_state.board.n
        m = game_state.board.m
        points_rule = {0: 0, 1: 1, 2: 3, 3: 7}  # the relation between the regions completed and the points gotten

        def find_empties_and_missings() -> None:
            """
            calculate the positions of the empties and the missing numbers for each region
            positions_of_empty_cells and numbers_missing_for_xxxx are all global variables
            """
            # row
            for i in range(N):
                numbers = set(num for num in range(1, N + 1))
                for j in range(N):
                    val = board.get(i, j)
                    if val == 0:  # find an empty cell
                        positions_of_empty_cells.add((i, j))
                    else:  # this val is not missing
                        numbers.remove(val)
                numbers_missing_for_rows.append(numbers)

            # column
            for j in range(N):
                numbers = set(num for num in range(1, N + 1))
                for i in range(N):
                    val = board.get(i, j)
                    if val == 0:
                        positions_of_empty_cells.add((i, j))
                    else:
                        numbers.remove(val)
                numbers_missing_for_cols.append(numbers)

            # block
            # the block number is defined from left to right, from top to bottom
            # i.e. 0,1,...,m-1; m,m+1,...,2*m-1; 2*m, 2*m+1,...
            n_block = 0
            for r in range(0, N, m):
                for c in range(0, N, n):
                    # (r, c) is the top-left cell of the block
                    numbers = set(num for num in range(1, N + 1))
                    for i in range(r, r + m):
                        for j in range(c, c + n):
                            val = board.get(i, j)
                            if val == 0:
                                positions_of_empty_cells.add((i, j))
                            else:
                                numbers.remove(val)
                    numbers_missing_for_blks.append(numbers)
                    n_block += 1


        def cancel_move(move: Move) -> None:
            """
            cancel the move of (i, j) and update positions of empties and missing numbers for each region
            """
            i, j, value = move.i, move.j, move.value
            # cancel the move, i.e. take the move of empty value (0)
            board.put(i, j, 0)
            # update
            positions_of_empty_cells.add((i, j))
            numbers_missing_for_rows[i].add(value)
            numbers_missing_for_cols[j].add(value)
            n_block = (i // m) * m + j // n  # calculate the corresponding block number
            numbers_missing_for_blks[n_block].add(value)

        def calculate_heuristic_score(empties_left):
            """
            this is a heuristic score function based on the empty cells after taking a move
            :param empties_left: the empty cells left in the region after taking a move
            :return: the heuristic score
            """
            # even number of empties left is good, 0 is the best because you get points immediately
            if empties_left % 2 == 0:
                return 1 / (empties_left + 1)
            # odd number of empties left is bad, 1 is the worst because opponent would fill that empty and get points
            return -1 / empties_left

        def move_and_calculate_score(move: Move, maximizing: bool, using_heuristics: bool = True):
            """
            take the move and give a score for it
            :param move: the move to be taken and scored
            :param maximizing: for maximizer or minimizer
            :param using_heuristics: using heuristic evaluation function or not
            :return: the score for this move
            """
            i, j, value = move.i, move.j, move.value
            # take the move of (i, j, value)
            board.put(i, j, value)
            # update the positions of empties and the missing numbers for each region
            positions_of_empty_cells.remove((i, j))
            numbers_missing_for_rows[i].remove(value)
            numbers_missing_for_cols[j].remove(value)
            n_block = (i // m) * m + j // n  # calculate the corresponding block number
            numbers_missing_for_blks[n_block].remove(value)

            # calculate how many regions are completed by this move and the points gotten for this move
            empties_each_region = [len(numbers_missing_for_rows[i]), len(numbers_missing_for_cols[j]), len(numbers_missing_for_blks[n_block])]
            region_completed = 0  # how many regions are completed by this move
            for emp in empties_each_region:
                region_completed += emp == 0
            points = points_rule[region_completed]

            # calculate the heuristic score if needed
            h_score = 0
            if using_heuristics:
                h_score = (calculate_heuristic_score(empties_each_region[0]) +
                           calculate_heuristic_score(empties_each_region[1]) +
                           calculate_heuristic_score(empties_each_region[2])) / 3

            # total score for this move
            score = h_score + 2 * points

            # multiply -1 for minimizer
            if not maximizing:
                score = -1 * score

            return score


        def get_all_legal_moves(threshold=1) -> list:
            """
            this function is to get all possible moves for next step
            :return: a list of possible moves
            """
            legal_moves = []
            single_possibility_moves = []
            for (x, y) in positions_of_empty_cells:
                # the corresponding block number of (x, y)
                n_block = (x // m) * m + y // n
                # legal values should be at least the intersection of the missing number of corresponding three regions
                possible_values = numbers_missing_for_rows[x] & numbers_missing_for_cols[y] & numbers_missing_for_blks[n_block]
                # should has not been declared taboo
                possible_moves = [Move(x, y, val) for val in possible_values if not TabooMove(x, y, val) in game_state.taboo_moves]
                legal_moves.extend(possible_moves)
                # only one possible move means "single possibility move" is found
                if len(possible_moves) == 1:
                    single_possibility_moves.append(possible_moves[0])

            # single_possibility_moves as heuristic possible moves is prior to normal moves
            if (len(positions_of_empty_cells)/(game_state.board.N*game_state.board.N) > threshold) and single_possibility_moves:
                return single_possibility_moves
            return legal_moves

        def minimax(depth: int, alpha, beta, maximizer: bool):
            """
            minimax search with alpha-beta pruning
            :param depth: the depth of the minimax tree
            :param alpha: best already explored option along path to the root for maximizer
            :param beta: best already explored option along path to the root for minimizer
            :param maximizer: if it is maximizer
            :return: the aggregated score if choose this move considering possible future moves
            """
            if depth == 0:
                return 0

            moves = get_all_legal_moves()

            if not moves:
                return 0
            if maximizer:
                max_eval = -float('inf')
                #sorted(initial_children, key=lambda c: c[1], reverse=True)
                for move in moves:
                    # take this move and calculate the score for this move
                    cur_move_score = move_and_calculate_score(move, True)
                    # consider the score that future moves will get
                    eval = cur_move_score + minimax(depth - 1, alpha, beta, False)
                    # update the max score among moves
                    max_eval = max(max_eval, eval)
                    # cancel this move on the board before try other moves
                    cancel_move(move)
                    alpha = max(alpha, max_eval)
                    if beta <= alpha:
                        break
                return max_eval

            else:
                min_eval = float('inf')
                for move in moves:
                    cur_move_score = move_and_calculate_score(move, False)
                    eval = cur_move_score + minimax(depth - 1, alpha, beta, True)
                    min_eval = min(min_eval, eval)
                    cancel_move(move)
                    beta = min(beta, min_eval)
                    if beta <= alpha:
                        break
                return min_eval

        def update_ordering(last_moves):
            """
            Orders the move based on the evaluation of the previous iteration.
            """
            _, moves = zip(*sorted(last_moves, key=lambda l: l[0], reverse=True))

            return moves

        board = game_state.board

        # a set consisting of all position (i, j) of empty cells
        positions_of_empty_cells = set()
        # numbers_missing_for_xxx has a length of N, each element is a set representing which numbers is missing in that region
        numbers_missing_for_rows = []
        numbers_missing_for_cols = []
        numbers_missing_for_blks = []
        # the positions of empty cells and the numbers missing are recorded before searching the tree and maintained all the time
        # so that not need to scan the whole board every time trying a move
        find_empties_and_missings()

        candidate_moves = get_all_legal_moves()

        # take the first as the best move before searching to avoid lose immediately when time_limit == 0.1
        best_move = candidate_moves[0]
        self.propose_move(best_move)

        # decide the starting search depth based on the number of empties
        empties = len(positions_of_empty_cells)
        empties_percentage = empties / N**2
        if empties_percentage < 0.30:
            starting_depth = 4
        elif empties_percentage < 0.50:
            starting_depth = 3
        elif empties_percentage < 0.70:
            starting_depth = 2
        else:
            starting_depth = 1

        # Iterative deepening depth-first search
        for depth in range(starting_depth, 50):
            last_moves = []
            max_eval = -float('inf')
            for candidate_move in candidate_moves:
                cur_move_score = move_and_calculate_score(candidate_move, True)
                eval = cur_move_score + minimax(depth - 1, -float('inf'), float('inf'), False)
                if eval > max_eval:
                    max_eval = eval
                    best_move = candidate_move
                last_moves.append([eval, candidate_move])
                cancel_move(candidate_move)
            # a-b pruning heuristic - sort the candidate moves for next iteration
            # based on current evaluation
            candidate_moves = update_ordering(last_moves)
            self.propose_move(best_move)