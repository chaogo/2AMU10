#  (C) Copyright Wieger Wesselink 2021. Distributed under the GPL-3.0-or-later
#  Software License, (See accompanying file LICENSE or copy at
#  https://www.gnu.org/licenses/gpl-3.0.txt)

import random
import time
from competitive_sudoku.sudoku import GameState, Move, SudokuBoard, TabooMove
import competitive_sudoku.sudokuai


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

        def possible(i, j, value):
            return game_state.board.get(i, j) == SudokuBoard.empty and not TabooMove(i, j,
                                                                                     value) in game_state.taboo_moves

        def legal(possible_moves):

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
                        if game_state.board.get(l, j) == value:
                            legal = False
                            break

                if legal:
                    # Check if value already in block
                    block_position_verti = i // m
                    block_position_hori = j // n

                    for k in range(, )
                    for l in range()

            # If all checks are passed add the move to the list of legal moves
            if legal:
                all_moves_legal.append(move)

    # Generate all moves that are possible
    all_moves = [Move(i, j, value) for i in range(N) for j in range(N) for value in range(1, N + 1) if
                 possible(i, j, value)]

    # Filter out moves that are illegal (do not comply with the game rules)
    legal_moves = legal(all_moves)

    # Propose naive move
    move = random.choice(all_moves)
    self.propose_move(move)


def eval(self, N, n, m, game_state: GameState, i, j, value):
    """"
    The eval function evaluates the score in the game that will be obtained by the proposed move (i,j,value)
    """
    # Add our hypothetical move to the current situation on the board
    game_state.board.put(i, j, value)

    # Create variables for each region that could be completed by a move (row, column, region)
    # Where 1 = filled and 0 = not filled. All initialized to 1.
    row = 1
    column = 1
    block = 1

    # CHECK ROW: loop through all k values in row i
    for k in range(N):
        # Check if we find an empty cell in row i column k
        if game_state.board.get(i, k) == SudokuBoard.empty:
            row = 0
            break

    # CHECK COLUMN: loop through all l values in column j
    for l in range(N):
        # Check if we find an empty cell in column j row l
        if game_state.board.get(l, j) == SudokuBoard.empty:
            column = 0
            break

    # CHECK block: loop through all n*m

    # the total score in the game earned with this move
    score = 0
    regions_filled = row + column + block

    # Calculate the total score in the game for current move and return the score
    if regions_filled == 0:
        score = 0
    elif regions_filled == 1:
        score = 1
    elif regions_filled == 2:
        score = 3
    elif regions_filled == 3:
        score = 7

    return score


def minimax(self, position, depth, maximizing):
    move = ''

    if depth == 0:
        return move

    if maximizing:
        print('maxi')
    else:
        print('mini')

    return move

