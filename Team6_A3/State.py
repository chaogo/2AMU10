from competitive_sudoku.sudoku import Move, SudokuBoard
import copy

points_rule = {0: 0, 1: 1, 2: 3, 3: 7}


class State:
    def __init__(self, board: SudokuBoard, scores: list, legal_moves: list, player: int, init_player: int):  # GameState.board作为state
        self.board = board
        self.scores = scores
        self.legal_moves = legal_moves
        self.player = player
        self.init_player = init_player
        self.empties = False

    def get_legal_actions(self):
        # return self.legal_moves
        return copy.copy(self.legal_moves)

    def is_game_over(self) -> bool:
        '''
        It is the game over condition
        and depends on your game. Returns
        true or false
        '''
        # game over if there is no solution
        if len(self.legal_moves) == 0:
            return True

        # game over if there is no empties
        over = True
        board = self.board
        N = board.N
        for i in range(N):
            for j in range(N):
                if board.get(i, j) == 0:
                    over = False
                    self.empties = True
                    break
        return over

    def game_result(self):
        '''
        Returns 1 or 0 or -1 depending
        on your state corresponding to win,
        tie or a loss.
        '''
        if self.empties:
            return 0  # no solution is counted as draw
        # win/lose/tie is always for the init_player
        if self.scores[0] == self.scores[1]:
            return 0
        if self.scores[self.init_player-1] > self.scores[2-self.init_player]:
            return 1
        return -1

    def get_score(self, move: Move):

        x, y, value = move.i, move.j, move.value
        board = self.board
        m, n, N = board.m, board.n, board.N
        board.put(x, y, value)

        row_completed = True
        for j in range(N):
            if board.get(x, j) == 0:
                row_completed = False
                break

        col_completed = True
        for i in range(N):
            if board.get(i, y) == 0:
                row_completed = False
                break

        blk_completed = True
        i0 = x // m * m
        j0 = y // n * n
        for i in range(i0, i0+m):
            for j in range(j0, j0+n):
                if board.get(i, j) == 0:
                    blk_completed = False
                    break
            if not blk_completed:
                break

        board.put(x, y, 0)
        regions_completed = row_completed + col_completed + blk_completed
        return points_rule[regions_completed]

    def move(self, move: Move):
        '''
        Changes the state of your
        board with a new value.
        Returns the new state after making a move.
        '''

        i, j, value = move.i, move.j, move.value
        m, n, N = self.board.m, self.board.n, self.board.N
        # take the move of (i, j, value) and get next board
        next_board = copy.deepcopy(self.board)
        next_board.put(i, j, value)

        # update scores
        score = self.get_score(move)
        next_scores = copy.copy(self.scores)
        next_scores[self.player-1] += score

        # update legal moves for next state
        next_legal_moves = []
        for mv in self.legal_moves:
            if mv.i == i and mv.j == j: continue
            if mv.value == value and (mv.i == i or mv.j == j or (mv.i//m*m <= i < mv.i//m*m+m and mv.j//n*n <= j < mv.j//n*n+n)): continue
            next_legal_moves.append(mv)

        # update player_number
        next_player = 3 - self.player

        # get next game state
        next_state = State(next_board, next_scores, next_legal_moves, next_player, self.init_player)

        return next_state
