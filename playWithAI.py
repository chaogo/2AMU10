#!/usr/bin/env python3

#  (C) Copyright Wieger Wesselink 2021. Distributed under the GPL-3.0-or-later
#  Software License, (See accompanying file LICENSE or copy at
#  https://www.gnu.org/licenses/gpl-3.0.txt)

import importlib
import multiprocessing
import platform
import re
import time
from pathlib import Path
from subprocess import TimeoutExpired
from competitive_sudoku.execute import solve_sudoku
from competitive_sudoku.sudoku import GameState, SudokuBoard, Move, TabooMove, load_sudoku_from_text
from competitive_sudoku.sudokuai import SudokuAI


def simulate_game(initial_board: SudokuBoard, human_player_number: int, AI_player: SudokuAI, solve_sudoku_path: str, time_for_human: int = 10, time_for_AI: float = 0.5) -> None:
    """
    Simulates a game between two instances of SudokuAI, starting in initial_board. The first move is played by player1.
    @param initial_board: The initial position of the game.
    @param human_player_number: either 1 or 2 corresponding to whether you want to play first or second
    @param AI_player: Your AI opponent which can be "team6_A1", "team6_A2", "team6_A3_extra1", "random_player", and "greedy_player"
    @param solve_sudoku_path: The location of the oracle executable.
    @param time_for_AI: The time limit for AI to calculate the best move
    @param time_for_human: The time limit for human to propose a move
    """
    import copy

    game_state = GameState(initial_board, copy.deepcopy(initial_board), [], [], [0, 0])
    move_number = 0
    number_of_moves = initial_board.squares.count(SudokuBoard.empty)
    print('Initial state')
    print(game_state)

    with multiprocessing.Manager() as manager:
        # use a lock to protect assignments to best_move
        lock = multiprocessing.Lock()
        AI_player.lock = lock

        # use shared variables to store the best move
        AI_player.best_move = manager.list([0, 0, 0])

        while move_number < number_of_moves:
            player_number = len(game_state.moves) % 2 + 1

            i, j, value = 0, 0, 0
            if player_number == human_player_number:
                print(f"-----------------------------\nIt's your turn.")
                print(f"please propose a move in the form of <i j value> within {time_for_human} seconds. NB: Current "
                      f"taboo moves are {[(mv.i, mv.j, mv.value) for mv in game_state.taboo_moves]}")

                import signal
                def alarm_handler(signum, frame):
                    raise TimeoutExpired
                signal.signal(signal.SIGALRM, alarm_handler)
                signal.alarm(time_for_human)  # wait for time_for_human seconds

                try:
                    move = input().split(" ")
                    i, j, value = (int(k) for k in move)
                except:
                    print("this is an illegal input, you have one chance left to try another.")
                    move = input().split(" ")
                    i, j, value = (int(k) for k in move)
                finally:
                    signal.alarm(0)  # cancel alarm

            else:
                print(f'-----------------------------\nYour AI opponent is thinking...')
                AI_player.best_move[0] = 0
                AI_player.best_move[1] = 0
                AI_player.best_move[2] = 0
                try:
                    process = multiprocessing.Process(target=AI_player.compute_best_move, args=(game_state,))
                    process.start()
                    time.sleep(time_for_AI)
                    lock.acquire()
                    process.terminate()
                    lock.release()
                except Exception as err:
                    print('Error: an exception occurred.\n', err)
                i, j, value = AI_player.best_move
            best_move = Move(i, j, value)
            print(f'Best move: {best_move}')

            # after calculating best move
            player_score = 0
            if best_move != Move(0, 0, 0):
                if TabooMove(i, j, value) in game_state.taboo_moves:
                    print(f'Error: {best_move} is a taboo move. Player {3-player_number} wins the game.')
                    return

                board_text = str(game_state.board)
                options = f'--move "{game_state.board.rc2f(i, j)} {value}"'
                output = solve_sudoku(solve_sudoku_path, board_text, options)
                if 'Invalid move' in output:
                    print(f'Error: {best_move} is not a valid move. Player {3-player_number} wins the game.')
                    return
                if 'Illegal move' in output:
                    print(f'Error: {best_move} is not a legal move. Player {3-player_number} wins the game.')
                    return
                if 'has no solution' in output:
                    print(f'The sudoku has no solution after the move {best_move}.')
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
                print(f'No move was supplied. Player {3-player_number} wins the game.')
                return
            game_state.scores[player_number-1] = game_state.scores[player_number-1] + player_score
            print(f'Reward: {player_score}')
            print(game_state)

        # game over
        if game_state.scores[0] == game_state.scores[1]:
            print("the game ends in a draw")
        elif game_state.scores[human_player_number-1] > game_state.scores[2-human_player_number]:
            print("You win!")
        else:
            print("You lose.")

def play_with_AI(board_name: str, play_first: bool, opponent_name: str, time_limit_for_human: int, time_limit_for_AI: int):
    solve_sudoku_path = 'bin\\solve_sudoku.exe' if platform.system() == 'Windows' else 'bin/solve_sudoku'
    human_player_number = 1 if play_first else 2
    AI_player = importlib.import_module(opponent_name + '.sudokuai').SudokuAI()
    board = load_sudoku_from_text(Path(f"boards/{board_name}.txt").read_text())
    simulate_game(board, human_player_number, AI_player, solve_sudoku_path, time_limit_for_human, time_limit_for_AI)

if __name__ == '__main__':
    play_first = False  # You play first or not
    opponent_name = "greedy_player"  # can choose from "team6_A1", "team6_A2", "team6_A3_extra1", "random_player", and "greedy_player"
    time_limit_for_human = 100  # set a time limit
    time_limit_for_AI = 1  # in seconds
    initial_board_name = "random-3x3"  # can choose from "/boards"
    play_with_AI(initial_board_name, play_first, opponent_name, time_limit_for_human, time_limit_for_AI)