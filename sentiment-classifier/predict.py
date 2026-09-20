"""
Classify text with the trained model.

Usage:
  python predict.py "This thing is amazing"
  python predict.py            # interactive mode
"""

import pickle
import sys

from train import MODEL_PATH


def load_model():
    try:
        with open(MODEL_PATH, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        sys.exit("No model found. Run `python train.py` first.")


def classify(model, text: str) -> str:
    prob_pos = model.predict_proba([text])[0][1]
    label = "POSITIVE" if prob_pos >= 0.5 else "NEGATIVE"
    confidence = prob_pos if label == "POSITIVE" else 1 - prob_pos
    return f"{label} ({confidence:.0%} confident)"


def main() -> None:
    model = load_model()

    if len(sys.argv) > 1:
        print(classify(model, " ".join(sys.argv[1:])))
        return

    print("Enter text to classify (Ctrl+C to exit):")
    while True:
        try:
            text = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if text:
            print(classify(model, text))


if __name__ == "__main__":
    main()
