"""
Tic-tac-toe against an unbeatable minimax AI. No dependencies.

Usage:
  python game.py
"""

from __future__ import annotations

from functools import lru_cache

HUMAN, AI, EMPTY = "X", "O", " "
LINES = [
    (0, 1, 2), (3, 4, 5), (6, 7, 8),  # rows
    (0, 3, 6), (1, 4, 7), (2, 5, 8),  # columns
    (0, 4, 8), (2, 4, 6),             # diagonals
]


def winner(board: str) -> str | None:
    for a, b, c in LINES:
        if board[a] != EMPTY and board[a] == board[b] == board[c]:
            return board[a]
    return None


def moves(board: str) -> list[int]:
    return [i for i, cell in enumerate(board) if cell == EMPTY]


def place(board: str, idx: int, player: str) -> str:
    return board[:idx] + player + board[idx + 1 :]


@lru_cache(maxsize=None)
def minimax(board: str, player: str) -> int:
    """Score of `board` from the AI's perspective when it's `player`'s turn.

    +10 - depth for an AI win, -10 + depth for a human win, 0 for a draw.
    Depth is encoded via the number of empty squares so the AI prefers
    faster wins and slower losses.
    """
    w = winner(board)
    depth = 9 - len(moves(board))
    if w == AI:
        return 10 - depth
    if w == HUMAN:
        return depth - 10
    if not moves(board):
        return 0

    scores = [minimax(place(board, m, player), HUMAN if player == AI else AI) for m in moves(board)]
    return max(scores) if player == AI else min(scores)


def best_move(board: str) -> int:
    return max(moves(board), key=lambda m: minimax(place(board, m, AI), HUMAN))


def render(board: str) -> str:
    cells = [c if c != EMPTY else str(i + 1) for i, c in enumerate(board)]
    rows = [" " + " | ".join(cells[i : i + 3]) for i in (0, 3, 6)]
    return "\n---+---+---\n".join(rows)


def main() -> None:
    board = EMPTY * 9
    print("You are X. Enter 1-9 to place a mark.\n")
    print(render(board), "\n")

    while True:
        # Human turn
        try:
            choice = int(input("Your move: ")) - 1
        except (ValueError, EOFError, KeyboardInterrupt):
            print("\nbye!")
            return
        if choice not in moves(board):
            print("That square isn't available.\n")
            continue
        board = place(board, choice, HUMAN)

        if winner(board) == HUMAN:
            print(render(board), "\nYou win?! That shouldn't be possible.")
            return
        if not moves(board):
            print(render(board), "\nDraw.")
            return

        # AI turn
        board = place(board, best_move(board), AI)
        print("\n" + render(board), "\n")

        if winner(board) == AI:
            print("AI wins.")
            return
        if not moves(board):
            print("Draw.")
            return


if __name__ == "__main__":
    main()
