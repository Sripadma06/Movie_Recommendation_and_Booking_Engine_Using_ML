"""
data_prep.py

Usage:
    python data_prep.py

Outputs (in working directory):
    - movies_tmdb_clean.csv
    - tfidf_vectorizer.pkl
    - tfidf_matrix.npz
    - nn_model.pkl

Set your TMDB API key in the environment if you plan to fetch posters:
    export TMDB_API_KEY="your_key_here"
    (Windows PowerShell): $env:TMDB_API_KEY="your_key_here"
"""
import os
import ast
import pickle
import pandas as pd
import requests
from scipy import sparse
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors

# ---------- Config ----------
TMDB_MOVIES_CSV = "tmdb_5000_movies.csv"
TMDB_CREDITS_CSV = "tmdb_5000_credits.csv"
OUT_CLEAN_CSV = "movies_tmdb_clean.csv"
OUT_VECT = "tfidf_vectorizer.pkl"
OUT_MATRIX = "tfidf_matrix.npz"
OUT_NN = "nn_model.pkl"
TMDB_API_KEY = os.getenv("TMDB_API_KEY", "")  # set this if you want poster URLs
N_NEIGHBORS = 12  # neighbors to build for nearest-neighbors model (includes itself)
# ----------------------------

def _parse_list_column(s):
    """Safely parse stringified list-of-dicts columns from TMDB CSVs."""
    if pd.isna(s):
        return []
    try:
        # use literal_eval for safety
        return ast.literal_eval(s)
    except Exception:
        # fallback: try replacing common issues then eval
        try:
            return ast.literal_eval(s.replace("None", "null"))
        except Exception:
            return []

def _join_names(list_of_dicts, top_n=None, key='name'):
    """Extract names from list-of-dicts and join with comma."""
    if not isinstance(list_of_dicts, (list, tuple)):
        return ""
    names = [d.get(key, "") for d in list_of_dicts if isinstance(d, dict) and d.get(key)]
    if top_n:
        names = names[:top_n]
    return ", ".join(names)

def load_tmdb5000_data(movies_csv=TMDB_MOVIES_CSV, credits_csv=TMDB_CREDITS_CSV,
                       save_clean=False, out_csv=OUT_CLEAN_CSV):
    """
    Loads tmdb_5000_movies.csv and tmdb_5000_credits.csv, merges and returns cleaned DataFrame.
    """
    if not os.path.exists(movies_csv):
        raise FileNotFoundError(f"{movies_csv} not found. Put it in the same folder as this script.")
    if not os.path.exists(credits_csv):
        raise FileNotFoundError(f"{credits_csv} not found. Put it in the same folder as this script.")

    print("Reading CSV files...")
    movies = pd.read_csv(movies_csv)
    credits = pd.read_csv(credits_csv)

    # normalize id column names and types
    if 'movie_id' in credits.columns and 'id' not in credits.columns:
        credits = credits.rename(columns={'movie_id': 'id'})

    # ensure integer ids where possible
    if 'id' in movies.columns:
        try:
            movies['id'] = movies['id'].astype(int)
        except Exception:
            movies['id'] = pd.to_numeric(movies['id'], errors='coerce').fillna(0).astype(int)
    if 'id' in credits.columns:
        try:
            credits['id'] = credits['id'].astype(int)
        except Exception:
            credits['id'] = pd.to_numeric(credits['id'], errors='coerce').fillna(0).astype(int)

    # merge credits (keep cast, crew)
    print("Merging movies and credits...")
    credits_small = credits[['id', 'cast', 'crew']] if set(['id','cast','crew']).issubset(credits.columns) else credits
    df = pd.merge(movies, credits_small, on='id', how='left')

    # Parse genres -> list and join into string
    print("Parsing genres, cast, crew...")
    df['genres_parsed'] = df['genres'].apply(_parse_list_column)
    df['genres_list'] = df['genres_parsed'].apply(lambda x: [g.get('name','') for g in x if isinstance(g, dict)])
    df['genres'] = df['genres_list'].apply(lambda lst: ", ".join([s for s in lst if s]))

    # Parse cast -> take top 3 cast names
    df['cast_parsed'] = df['cast'].apply(_parse_list_column)
    df['top_cast'] = df['cast_parsed'].apply(lambda x: _join_names(x, top_n=3))

    # Parse crew -> find director
    df['crew_parsed'] = df['crew'].apply(_parse_list_column)
    def find_director(crew_list):
        if not isinstance(crew_list, (list, tuple)):
            return ""
        for c in crew_list:
            if isinstance(c, dict) and (c.get('job') == 'Director' or c.get('department') == 'Directing'):
                return c.get('name', "")
        return ""
    df['director'] = df['crew_parsed'].apply(find_director)

    # Fill missing critical columns
    df['overview'] = df.get('overview', pd.Series([""] * len(df))).fillna("").astype(str)
    df['title'] = df.get('title', pd.Series([""] * len(df))).fillna("").astype(str)
    df['tmdb_id'] = df['id']  # explicit name

    # rename vote_average to rating if present
    if 'vote_average' in df.columns:
        df = df.rename(columns={'vote_average': 'rating'})

    # choose useful columns to keep
    keep_cols = ['tmdb_id', 'title', 'overview', 'genres', 'top_cast', 'director', 'release_date', 'rating']
    existing_keep = [c for c in keep_cols if c in df.columns]
    df_clean = df[existing_keep].copy()

    # remove duplicates by tmdb_id (keep first)
    df_clean = df_clean.drop_duplicates(subset=['tmdb_id'])

    # optionally save
    if save_clean:
        df_clean.to_csv(out_csv, index=False)
        print(f"Saved cleaned csv to {out_csv}")

    print("Data preprocessing complete.")
    return df_clean

# ---------- Poster helper ----------
def fetch_movie_poster(tmdb_id):
    """Return poster URL for a tmdb movie id or None if unavailable. Requires TMDB_API_KEY env var."""
    if not TMDB_API_KEY:
        return None
    try:
        url = f"https://api.themoviedb.org/3/movie/{tmdb_id}?api_key={TMDB_API_KEY}"
        resp = requests.get(url, timeout=6)
        resp.raise_for_status()
        data = resp.json()
        poster_path = data.get('poster_path')
        if poster_path:
            return f"https://image.tmdb.org/t/p/w500{poster_path}"
    except Exception:
        return None

# ---------- TF-IDF + NearestNeighbors builder ----------
def build_and_save_tfidf_nn(df, overview_col="overview", n_neighbors=N_NEIGHBORS,
                            out_vec=OUT_VECT, out_matrix=OUT_MATRIX, out_nn=OUT_NN):
    """
    Build TF-IDF on df[overview_col], save vectorizer and sparse matrix and a NearestNeighbors model.
    n_neighbors includes the movie itself (so choose k+1 to get k recommendations).
    """
    print("Building TF-IDF matrix...")
    documents = df[overview_col].fillna("").astype(str).values
    vectorizer = TfidfVectorizer(stop_words='english', max_df=0.85, min_df=2)
    tfidf_matrix = vectorizer.fit_transform(documents)  # sparse matrix

    print("Saving vectorizer and matrix...")
    with open(out_vec, "wb") as f:
        pickle.dump(vectorizer, f)
    sparse.save_npz(out_matrix, tfidf_matrix)

    print("Training NearestNeighbors (cosine)...")
    nn = NearestNeighbors(metric='cosine', algorithm='brute', n_neighbors=n_neighbors)
    nn.fit(tfidf_matrix)
    with open(out_nn, "wb") as f:
        pickle.dump(nn, f)

    print(f"Saved: {out_vec}, {out_matrix}, {out_nn}")
    return vectorizer, tfidf_matrix, nn

# ---------- CLI behavior ----------
if __name__ == "__main__":
    print("Starting data_prep.py")
    try:
        df_clean = load_tmdb5000_data(save_clean=True, out_csv=OUT_CLEAN_CSV)
        print("Cleaned rows:", len(df_clean))
    except Exception as e:
        print("Error during cleaning:", e)
        raise

    # build TF-IDF and NearestNeighb
