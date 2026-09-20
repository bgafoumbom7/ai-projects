# Sentiment Classifier

A classic machine-learning text classifier: it reads a review and predicts whether it's positive or negative.

No neural networks, no GPU — just TF-IDF features and logistic regression from scikit-learn. It trains in under a second and is a good reference for how "traditional" NLP works.

## Run it

```bash
pip install scikit-learn
python train.py
python predict.py "The battery life is incredible"
```

Or run `python predict.py` with no arguments for an interactive prompt.

## How it works

1. **TF-IDF** turns each sentence into a sparse vector of word and word-pair (bigram) weights, so "not good" is treated differently from "good".
2. **Logistic regression** learns a weight for each feature; positive weights push toward the positive class.
3. `train.py` reports 5-fold cross-validation accuracy plus a held-out test score, then pickles the fitted pipeline.

## Notes

The bundled dataset (`data.py`) is tiny — 60 hand-written examples — so it exists to demonstrate the pipeline, not to be accurate on arbitrary text. Swap in a real dataset (e.g. IMDB reviews) for meaningful results; the code doesn't need to change.
