"""Exhaustively verify the AI never loses. Run with: python test_game.py"""

from game import AI, EMPTY, HUMAN, best_move, moves, place, winner


def ai_never_loses(board: str) -> bool:
    """Human plays every possible move; AI replies optimally. Return False on any AI loss."""
    for m in moves(board):
        b = place(board, m, HUMAN)
        if winner(b) == HUMAN:
            return False
        if not moves(b):
            continue
        b = place(b, best_move(b), AI)
        if winner(b) == AI or not moves(b):
            continue
        if not ai_never_loses(b):
            return False
    return True


if __name__ == "__main__":
    assert ai_never_loses(EMPTY * 9), "AI lost a game!"
    print("OK: AI is unbeatable across all human strategies.")
