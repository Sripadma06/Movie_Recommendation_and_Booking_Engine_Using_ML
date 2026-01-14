# build_recommender.py
# Run this from the same folder as movies_tmdb_clean.csv

import os, pickle, time, traceback
import pandas as pd
from pathlib import Path
from scipy import sparse
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors

BASE = Path(__file__).resolve().parent
CLEAN_CSV = BASE / "movies_tmdb_clean.csv"
OUT_VECT = BASE / "tfidf_vectorizer.pkl"
OUT_MATRIX = BASE / "tfidf_matrix.npz"
OUT_NN = BASE / "nn_model.pkl"

def log(msg):
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}", flush=True)

def build():
    log(f"Checking file: {CLEAN_CSV.exists()} -> {CLEAN_CSV}")
    if not CLEAN_CSV.exists():
        raise FileNotFoundError(f"{CLEAN_CSV} not found. Run data_prep.py first.")
    log("Loading cleaned CSV...")
    df = pd.read_csv(CLEAN_CSV)
    log(f"Loaded {len(df)} rows.")

    # ensure overview column exists
    if 'overview' not in df.columns:
        df['overview'] = ""

    docs = df['overview'].fillna("").astype(str).values
    log("Building TF-IDF (this may take a few seconds)...")
    try:
        vectorizer = TfidfVectorizer(stop_words='english', max_df=0.85, min_df=2)
        tfidf = vectorizer.fit_transform(docs)
        log(f"TF-IDF matrix shape: {tfidf.shape}")
    except Exception as e:
        log("ERROR during TF-IDF build:")
        traceback.print_exc()
        raise

    # save vectorizer and matrix
    log(f"Saving vectorizer to {OUT_VECT} ...")
    with open(OUT_VECT, "wb") as f:
        pickle.dump(vectorizer, f)
    log(f"Saving sparse matrix to {OUT_MATRIX} ...")
    sparse.save_npz(OUT_MATRIX, tfidf)

    # build nearest neighbors
    log("Training NearestNeighbors (cosine)...")
    try:
        nn = NearestNeighbors(metric='cosine', algorithm='brute', n_neighbors=12)
        nn.fit(tfidf)
    except Exception as e:
        log("ERROR during NN training:")
        traceback.print_exc()
        raise

    log(f"Saving NN model to {OUT_NN} ...")
    with open(OUT_NN, "wb") as f:
        pickle.dump(nn, f)

    log("All artifacts saved successfully.")
    log("Files and sizes:")
    for p in [OUT_VECT, OUT_MATRIX, OUT_NN]:
        if p.exists():
            log(f" - {p.name}: {p.stat().st_size} bytes")
        else:
            log(f" - {p.name}: NOT FOUND")

if __name__ == "__main__":
    try:
        build()
    except Exception as e:
        log("Build failed with exception:")
        traceback.print_exc()
        raise
