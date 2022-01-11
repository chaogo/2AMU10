import numpy as np
from collections import defaultdict


class MonteCarloTreeSearchNode:
    def __init__(self, state, parent=None, parent_action=None):
        self.state = state
        self.parent = parent
        self.parent_action = parent_action
        self.children = []
        self._number_of_visits = 0
        self._results = defaultdict(int)
        self._results[1] = 0
        self._results[-1] = 0
        self._untried_actions = None
        self._untried_actions = self.untried_actions()
        return

    def untried_actions(self):
        self._untried_actions = self.state.get_legal_actions()
        return self._untried_actions

    def q(self):
        wins = self._results[1]
        loses = self._results[-1]
        return wins - loses

    def n(self):
        return self._number_of_visits

    # selection and expansion

    def _tree_policy(self):
        current_node = self
        while not current_node.is_terminal_node():

            # print(f"current_node._untried_actions = {[[mv.i, mv.j, mv.value] for mv in current_node._untried_actions]}")
            if not current_node.is_fully_expanded():
                # print("expanding")
                return current_node.expand()  # -> exploration
            else:
                # print("selecting")
                current_node = current_node.best_child()  # -> exploitation
        return current_node  # terminal node

    def is_terminal_node(self):
        return self.state.is_game_over()

    def is_fully_expanded(self):
        return len(self._untried_actions) == 0

    # expansion
    def expand(self):
        action = self._untried_actions.pop()
        next_state = self.state.move(action)
        child_node = MonteCarloTreeSearchNode(
            next_state, parent=self, parent_action=action)

        self.children.append(child_node)
        # print(f"\t action = {[action.i, action.j, action.value]}")
        return child_node

    # selection
    def best_child(self, c_param=0.1):
        choices_weights = [(c.q() / c.n()) + c_param * np.sqrt((2 * np.log(self.n()) / c.n())) for c in self.children]
        return self.children[np.argmax(choices_weights)]


    # simulation
    def rollout(self):
        current_rollout_state = self.state
        possible_moves = current_rollout_state.get_legal_actions()

        while not current_rollout_state.is_game_over() and possible_moves:
            action = self.rollout_policy(possible_moves)
            current_rollout_state = current_rollout_state.move(action)
            possible_moves = current_rollout_state.get_legal_actions()

        return current_rollout_state.game_result()

    def rollout_policy(self, possible_moves):
        return possible_moves[np.random.randint(len(possible_moves))]

    # backpropagation
    def backpropagate(self, result):
        self._number_of_visits += 1.
        self._results[result] += 1.
        if self.parent:
            self.parent.backpropagate(result)
