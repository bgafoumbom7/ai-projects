# Tic-Tac-Toe AI

Play tic-tac-toe against an opponent that cannot lose. Pure Python, no dependencies.

```bash
python game.py
```

## How it works

The AI uses **minimax**: before each move it recursively simulates every possible continuation of the game, assuming you play perfectly too. Each end state is scored (+ for AI win, − for human win, 0 for draw), scores propagate back up the tree — the AI picks the maximum, you're assumed to pick the minimum — and it plays the move with the best guaranteed outcome.

Two small refinements:

- **Depth-aware scoring** — a win in 2 moves scores higher than a win in 4, so the AI finishes games quickly and drags out losing positions (which, in tic-tac-toe, never actually occur).
- **Memoisation** — `functools.lru_cache` stores the score of every board seen, so the full game tree (5,478 reachable positions) is only evaluated once.

## Proof it's unbeatable

```bash
python test_game.py
```

This walks every possible sequence of human moves and confirms the AI never loses.
