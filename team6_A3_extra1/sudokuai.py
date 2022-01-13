#  (C) Copyright Wieger Wesselink 2021. Distributed under the GPL-3.0-or-later
#  Software License, (See accompanying file LICENSE or copy at
#  https://www.gnu.org/licenses/gpl-3.0.txt)

from team6_A3_extra1.MonteCarlo import MonteCarloTreeSearchNode
from team6_A3_extra1.State import State
from competitive_sudoku.sudoku import GameState, Move, SudokuBoard, TabooMove
import competitive_sudoku.sudokuai
import time
import numpy as np


class SudokuAI(competitive_sudoku.sudokuai.SudokuAI):
    """
    Sudoku AI that computes a move for a given sudoku configuration.
    """
    def __init__(self):
        super().__init__()

    def get_initial_legal_moves(self, game_state: GameState) -> list:
        '''
        :return: legal moves for initial boards
        '''
        board = game_state.board
        m, n, N = board.m, board.n, board.N

        # a set consisting of all position (i, j) of empty cells
        positions_of_empty_cells = set()
        # numbers_missing_for_xxx has a length of N, each element is a set representing which numbers is missing in that region
        numbers_missing_for_rows = []
        numbers_missing_for_cols = []
        numbers_missing_for_blks = []

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

        legal_moves = []
        for (x, y) in positions_of_empty_cells:
            # the corresponding block number of (x, y)
            n_block = (x // m) * m + y // n
            # legal values should be at least the intersection of the missing number of corresponding three regions
            possible_values = numbers_missing_for_rows[x] & numbers_missing_for_cols[y] & numbers_missing_for_blks[
                n_block]
            # should has not been declared taboo
            possible_moves = [Move(x, y, val) for val in possible_values if not TabooMove(x, y, val) in game_state.taboo_moves]
            legal_moves.extend(possible_moves)

        return legal_moves

    def compute_best_move(self, game_state: GameState) -> None:
        root = self.load()
        can_find_target_node = 0
        if root:
            # find target node corresponding to current game_state
            for move in game_state.moves[-2:]:
                if not isinstance(move, TabooMove): # 必须找到node,没有的话就只能新扩展
                    for child in root.children:
                        if child.parent_action == move:
                            root = child  # 有可能还没扩展开，找不到
                            can_find_target_node += 1
                            break

            # already found
            if can_find_target_node == 2:
                # update legal moves
                new_legal_moves = []
                for move in root.state.legal_moves:
                    if move in game_state.taboo_moves:
                        continue
                    new_legal_moves.append(move)
                root.state.legal_moves = new_legal_moves
                root.untried_actions()  # need call this function to assign new_legal_moves to MC node!
                # update root.children
                new_children = []
                for child in root.children:
                    if child.parent_action in game_state.taboo_moves:
                        continue
                    new_children.append(child)
                root.children = new_children
                # propose a move at the start
                self.propose_move(root.state.legal_moves[0])

        # initialize a root node if cannot find the target node from previous tree
        if can_find_target_node != 2:
            init_board = game_state.board
            init_scores = game_state.scores
            init_legal_moves = self.get_initial_legal_moves(game_state)
            init_player = 1 if len(game_state.moves) % 2 == 0 else 2

            initial_state = State(init_board, init_scores, init_legal_moves, init_player, init_player)
            root = MonteCarloTreeSearchNode(state=initial_state)

            self.propose_move(init_legal_moves[0])

        simulation_no = 100000
        for i in range(simulation_no):
            v = root._tree_policy()
            # reward = v.rollout()
            # v.backpropagate(reward)
            #backpropagate score reward instead of wins
            player, reward = v.rollout()
            v.backpropagate(player,reward)

            if i % 10 == 0:  # propose a move and save the current node status every 10 simulations
                selected_node = root.best_child(c_param=0.)
                self.propose_move(selected_node.parent_action)
                self.save(root)  # only keep the latest saved node
