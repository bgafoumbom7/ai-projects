"""
Train a sentiment classifier and save it to disk.

Pipeline: TF-IDF (word + bigram features) -> Logistic Regression.

Usage:
  python train.py
"""

import pickle

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.pipeline import Pipeline

from data import REVIEWS

MODEL_PATH = "sentiment_model.pkl"


def build_pipeline() -> Pipeline:
    return Pipeline(
        [
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True)),
            # Weak regularisation (C=10) suits the tiny demo dataset;
            # lower C on larger, noisier data.
            ("clf", LogisticRegression(C=10, max_iter=1000)),
        ]
    )


def main() -> None:
    texts, labels = zip(*REVIEWS)
    X_train, X_test, y_train, y_test = train_test_split(
        texts, labels, test_size=0.25, random_state=42, stratify=labels
    )

    pipe = build_pipeline()

    scores = cross_val_score(pipe, texts, labels, cv=5)
    print(f"5-fold CV accuracy: {scores.mean():.2%} (+/- {scores.std():.2%})")

    pipe.fit(X_train, y_train)
    print(f"Held-out accuracy:  {pipe.score(X_test, y_test):.2%}")

    with open(MODEL_PATH, "wb") as f:
        pickle.dump(pipe, f)
    print(f"Saved model to {MODEL_PATH}")


if __name__ == "__main__":
    main()
