#  (C) Copyright Wieger Wesselink 2021. Distributed under the GPL-3.0-or-later
#  Software License, (See accompanying file LICENSE or copy at
#  https://www.gnu.org/licenses/gpl-3.0.txt)

import random
import time
from competitive_sudoku.sudoku import GameState, Move, SudokuBoard, TabooMove
import competitive_sudoku.sudokuai
import copy

class SudokuAI(competitive_sudoku.sudokuai.SudokuAI):
    """
    Sudoku AI that computes a move for a given sudoku configuration.
    """

    def __init__(self):
        super().__init__()

    # N.B. This is a very naive implementation.
    def compute_best_move(self, game_state: GameState) -> None:
        N = game_state.board.N
        n = game_state.board.n
        m = game_state.board.m

        def empty_cells_each_region(board):
            # row
            row_empty_left = [0] * N
            for i in range(N):
                for j in range(N):
                    if board.get(i, j) == 0:
                        row_empty_left[i] += 1

            # column
            col_empty_left = [0] * N
            for j in range(N):
                for i in range(N):
                    if board.get(i, j) == 0:
                        col_empty_left[j] += 1

            # block
            blk_empty_left = [0] * N
            n_block = 0
            for r in range(0, N, m):
                for c in range(0, N, n):
                    # (r, c) is the top-left cell of the block
                    for i in range(r, r+m):
                        for j in range(c, c+n):
                            if board.get(i, j) == 0:
                                blk_empty_left[n_block] += 1
                    n_block += 1

            return [row_empty_left, col_empty_left, blk_empty_left]

        def move_back(board, i, j):
            """"
            The function revocate the move
            """
            board.put(i, j, 0)
            empties[0][i] += 1
            empties[1][j] += 1
            n_block = (i//m)*m + j//n
            empties[2][n_block] += 1

        def calculate_heuristic_score(empty_left):
            if empty_left % 2 == 0:
                return 1/(empty_left+1)
            return -1/empty_left

        def move_and_calculate_score(board, i, j, value, maximizing):
            """"
            The function take the move and evaluates the score
            """
            # Add our hypothetical move to the current situation on the board
            board.put(i, j, value)
            empties[0][i] -= 1
            empties[1][j] -= 1
            n_block = (i//m)*m + j//n
            empties[2][n_block] -= 1

            # heuristic score
            empties_each_region = [empties[0][i], empties[1][j], empties[2][n_block]] # [row_empty_left, col_empty_left, blk_empty_left]
            h_score = (calculate_heuristic_score(empties_each_region[0])+
                       calculate_heuristic_score(empties_each_region[1])+
                       calculate_heuristic_score(empties_each_region[2]))/3

            # points
            region_completed = 0
            for i in empties_each_region:
                region_completed += i == 0

            # total score for this move
            score = h_score + 2*points_rule[region_completed]

            # multiply -1 for minimizer
            if not maximizing:
                score = -1 * score

            return score

        """ Returns all legal moves given a board """
        def get_all_legal_moves(board):

            # Generate all moves that are possible
            possible_moves = [Move(i, j, value) for i in range(N) for j in range(N) for value in range(1, N + 1) if
                              board.get(i, j) == SudokuBoard.empty and not TabooMove(i, j,
                                                                                     value) in game_state.taboo_moves]
            # filter out illegal moves
            all_moves_legal = []

            for move in possible_moves:
                i = move.i
                j = move.j
                value = move.value
                legal = True

                # Check if value already in row
                for k in range(N):
                    if game_state.board.get(i, k) == value:
                        legal = False
                        break

                if legal:
                    # Check if value already in column
                    for l in range(N):
                        if board.get(l, j) == value:
                            legal = False
                            break

                if legal:
                    # Find the coordinates of the upper left corner of the block in which (i,j) is positioned
                    block_position_verti = i // m * m
                    block_position_hori = j // n * n

                    # Loop through rows (l) and columns (k) inside
                    for l in range(block_position_verti, block_position_verti + m):
                        for k in range(block_position_hori, block_position_hori + n):
                            if board.get(l, k) == value:
                                legal = False
                                break

                # If all checks are passed add the move to the list of legal moves
                if legal:
                    all_moves_legal.append(move)

            return all_moves_legal

        def minimax(board, depth, alpha, beta, max_player):
            if depth == 0:
                return 0

            moves = get_all_legal_moves(board)
            if not moves:
                return 0
            # alpha: best already explored option along path to the root for maximizer
            # beta:  best already explored option along path to the root for minimizer
            if max_player:
                max_eval = -float('inf')
                for move in moves:
                    i, j, value = move.i, move.j, move.value
                    # moved when implementing calculate_move_score
                    cur_move_score = move_and_calculate_score(board, i, j, value, True)
                    # aggregate scores
                    eval = cur_move_score + minimax(board, depth - 1, alpha, beta, False)
                    max_eval = max(max_eval, eval)
                    # reset
                    move_back(board, i, j)
                    alpha = max(alpha, max_eval)
                    if beta <= alpha:
                        break
                return max_eval

            else:
                min_eval = float('inf')
                for move in moves:
                    i, j, value = move.i, move.j, move.value
                    cur_move_score = move_and_calculate_score(board, i, j, value, False)
                    eval = cur_move_score + minimax(board, depth-1, alpha, beta, True)
                    min_eval = min(min_eval, eval)
                    move_back(board, i, j)
                    beta = min(beta, min_eval)
                    if beta <= alpha:
                        break
                return min_eval

        points_rule = {0: 0, 1: 1, 2: 3, 3: 7}
        board = game_state.board
        moves = get_all_legal_moves(board)
        best_move = moves[0]
        self.propose_move(best_move)

        empties = empty_cells_each_region(board)

        for depth in range(1, 50):
            # print(depth, '\t')  # usually can search for less than 5 layers
            max_eval = -float('inf')
            for move in moves:
                i, j, value = move.i, move.j, move.value
                cur_move_score = move_and_calculate_score(board, i, j, value, True)
                eval = cur_move_score + minimax(board, depth - 1, -float('inf'), float('inf'), False)
                if eval > max_eval:
                    max_eval = eval
                    best_move = move
                move_back(board, i, j)
            self.propose_move(best_move)