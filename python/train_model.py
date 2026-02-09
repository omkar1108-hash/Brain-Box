import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.utils.class_weight import compute_class_weight
import numpy as np
import joblib

# ------------------ LOAD DATA ------------------
df = pd.read_csv("../dataset/notes_dataset.csv")

df = df.dropna()
df["text"] = df["text"].astype(str)
df["category"] = df["category"].astype(str)

X = df["text"]
y = df["category"]

# ------------------ CLASS WEIGHTS ------------------
classes = np.unique(y)
weights = compute_class_weight(
    class_weight="balanced",
    classes=classes,
    y=y
)

class_weight_dict = dict(zip(classes, weights))

# ------------------ MODEL PIPELINE ------------------
model = Pipeline([
    ("tfidf", TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2),   # unigrams + bigrams
        min_df=5,
        max_df=0.90
    )),
    ("clf", MultinomialNB())
])

# ------------------ TRAIN ------------------
model.fit(X, y)

# ------------------ SAVE MODEL ------------------
joblib.dump(model, "../model/note_classifier.pkl")

print("Model trained successfully")
print("Categories learned:", classes)
