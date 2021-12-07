import importlib
import multiprocessing
from pathlib import Path
import re
import time
import platform
from competitive_sudoku.sudoku import GameState, SudokuBoard, Move, TabooMove, load_sudoku_from_text
from competitive_sudoku.execute import solve_sudoku
from competitive_sudoku.sudokuai import SudokuAI

def simulate_game(initial_board: SudokuBoard, player1: SudokuAI, player2: SudokuAI, solve_sudoku_path: str, calculation_time: float = 0.5) -> int:
    """
    Simulates a game between two instances of SudokuAI, starting in initial_board. The first move is played by player1.
    @param initial_board: The initial position of the game.
    @param player1: The AI of the first player.
    @param player2: The AI of the second player.
    @param solve_sudoku_path: The location of the oracle executable.
    @param calculation_time: The amount of time in seconds for computing the best move.
    retrun 1 if player1 wins, 0 if draws, -1 if lose
    """
    import copy
    N = initial_board.N

    game_state = GameState(initial_board, copy.deepcopy(initial_board), [], [], [0, 0])
    move_number = 0
    number_of_moves = initial_board.squares.count(SudokuBoard.empty)
    # print('Initial state')
    # print(game_state)

    with multiprocessing.Manager() as manager:
        # use a lock to protect assignments to best_move
        lock = multiprocessing.Lock()
        player1.lock = lock
        player2.lock = lock

        # use shared variables to store the best move
        player1.best_move = manager.list([0, 0, 0])
        player2.best_move = manager.list([0, 0, 0])

        while move_number < number_of_moves:
            player, player_number = (player1, 1) if len(game_state.moves) % 2 == 0 else (player2, 2)
            # print(f'-----------------------------\nCalculate a move for player {player_number}')
            player.best_move[0] = 0
            player.best_move[1] = 0
            player.best_move[2] = 0
            try:
                process = multiprocessing.Process(target=player.compute_best_move, args=(game_state,))
                process.start()
                time.sleep(calculation_time)
                lock.acquire()
                process.terminate()
                lock.release()
            except Exception as err:
                print('Error: an exception occurred.\n', err)
            i, j, value = player.best_move
            best_move = Move(i, j, value)
            # print(f'Best move: {best_move}')
            player_score = 0
            if best_move != Move(0, 0, 0):
                if TabooMove(i, j, value) in game_state.taboo_moves:
                    # print(f'Error: {best_move} is a taboo move. Player {2-player_number} wins the game.')
                    return 1 if 2-player_number == 1 else -1
                board_text = str(game_state.board)
                options = f'--move "{game_state.board.rc2f(i, j)} {value}"'
                output = solve_sudoku(solve_sudoku_path, board_text, options)
                if 'Invalid move' in output:
                    # print(f'Error: {best_move} is not a valid move. Player {3-player_number} wins the game.')
                    return 1 if 3-player_number == 1 else -1
                if 'Illegal move' in output:
                    # print(f'Error: {best_move} is not a legal move. Player {3-player_number} wins the game.')
                    return 1 if 3-player_number == 1 else -1
                if 'has no solution' in output:
                    # print(f'The sudoku has no solution after the move {best_move}.')
                    player_score = 0
                    game_state.moves.append(TabooMove(i, j, value))
                    game_state.taboo_moves.append(TabooMove(i, j, value))
                if 'The score is' in output:
                    match = re.search(r'The score is ([-\d]+)', output)
                    if match:
                        player_score = int(match.group(1))
                        game_state.board.put(i, j, value)
                        game_state.moves.append(best_move)
                        move_number = move_number + 1
                    else:
                        raise RuntimeError(f'Unexpected output of sudoku solver: "{output}".')
            else:
                # print(f'No move was supplied. Player {3-player_number} wins the game.')
                return 1 if 3-player_number == 1 else -1
            game_state.scores[player_number-1] = game_state.scores[player_number-1] + player_score
            # print(f'Reward: {player_score}')
            # print(game_state)
        if game_state.scores[0] > game_state.scores[1]:
            # print('Player 1 wins the game.')
            return 1
        elif game_state.scores[0] == game_state.scores[1]:
            # print('The game ends in a draw.')
            return 0
        elif game_state.scores[0] < game_state.scores[1]:
            # print('Player 2 wins the game.')
            return -1

def test():


    # game conditions
    agents = ['Team6_A1', 'random_player', 'greedy_player']
    boards = ["easy-2x2", "easy-3x3", "empty-2x2", "empty-2x2", "empty-2x3", "empty-3x3", "empty-3x4", "empty-4x4",
              "hard-3x3", "random-2x3", "random-3x3", "random-3x4", "random-4x4"]
    time_candidates = [0.1, 0.5, 1, 5]
    n_games = 10
    solve_sudoku_path = 'bin\\solve_sudoku.exe' if platform.system() == 'Windows' else 'bin/solve_sudoku'
    P1 = 'Team6_A1'  # team6_A1 plays the first move
    player1 = importlib.import_module(P1 + '.sudokuai').SudokuAI()

    for P2 in agents[1:]:
        player2 = importlib.import_module(P2 + '.sudokuai').SudokuAI()
        print(f"{P1} vs. {P2}")
        for time in time_candidates:
            print(f"\t time_limit = {time}")
            for B in boards:
                board = load_sudoku_from_text(Path(f"boards/{B}.txt").read_text())
                result = [0, 0, 0]  # [draw, win, lose]
                for _ in range(n_games):
                    r = simulate_game(board, player1, player2, solve_sudoku_path, time)
                    result[r] += 1
                print(f"\t\t{B}: \twin({result[1]/n_games}) \tdraw({result[0]/n_games}) \tlose({result[-1]/n_games})")
        print("========================================================================\n")


if __name__ == '__main__':
    test()
