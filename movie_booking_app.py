# movie_booking_app.py
import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
from datetime import datetime
import requests
import os

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from dotenv import load_dotenv

# ==================== CONFIG ====================
st.set_page_config(
    page_title="CineMatch - Movie Booking",
    layout="wide",
    page_icon="🎬"
)

load_dotenv()
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w500"

# ==================== SESSION AUTH (NO STORAGE) ====================
def init_session():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.user_name = ""
        st.session_state.user_email = ""
        st.session_state.user_password = ""
        st.session_state.selected_movie = None

def login_ui():
    st.subheader("🔐 Login ")

    email = st.text_input("Email", key="login_email")
    password = st.text_input("Password", type="password", key="login_password")

    if st.button("Login"):
        if not email or not password:
            st.error("Please fill all fields")
            return

        if (
            email == st.session_state.user_email
            and password == st.session_state.user_password
        ):
            st.session_state.logged_in = True
            st.success("Login successful")
            st.rerun()
        else:
            st.error("Invalid email or password")

def signup_ui():
    st.subheader("📝 Sign Up ")

    name = st.text_input("Full Name", key="signup_name")
    email = st.text_input("Email", key="signup_email")
    password = st.text_input("Password", type="password", key="signup_password")
    confirm = st.text_input("Confirm Password", type="password", key="signup_confirm")

    if st.button("Create Account"):
        if not name or not email or not password or not confirm:
            st.error("All fields are required")
            return

        if password != confirm:
            st.error("Passwords do not match")
            return

        st.session_state.user_name = name
        st.session_state.user_email = email
        st.session_state.user_password = password
        st.session_state.logged_in = True

        st.success("Signup successful. You are now logged in.")
        st.rerun()

# ==================== DATABASE (BOOKINGS ONLY) ====================
def init_db():
    conn = sqlite3.connect("bookings.db", check_same_thread=False)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_name TEXT,
            user_email TEXT,
            movie_title TEXT,
            theater TEXT,
            showtime TEXT,
            seats TEXT,
            booking_date TEXT,
            total_price REAL
        )
    """)
    conn.commit()
    return conn

# ==================== DATA ====================
@st.cache_data
def load_movie_data():
    df = pd.read_csv("movies_tmdb_clean.csv")

    if "id" in df.columns and "tmdb_id" not in df.columns:
        df = df.rename(columns={"id": "tmdb_id"})

    df["title"] = df.get("title", "").fillna("").astype(str)
    df["overview"] = df.get("overview", "").fillna("").astype(str)
    df["genres"] = df.get("genres", "").fillna("").astype(str)

    if "vote_average" in df.columns and "rating" not in df.columns:
        df = df.rename(columns={"vote_average": "rating"})
    if "rating" not in df.columns:
        df["rating"] = np.nan

    if "release_date" in df.columns:
        df["year"] = df["release_date"].astype(str).str[:4]
    else:
        df["year"] = ""

    df["tmdb_id"] = pd.to_numeric(df.get("tmdb_id", 0), errors="coerce").fillna(0).astype(int)
    return df

# ==================== POSTERS ====================
def fetch_movie_poster(tmdb_id):
    placeholder = "https://via.placeholder.com/500x750?text=Poster+Not+Available"
    if not TMDB_API_KEY or tmdb_id == 0:
        return placeholder
    try:
        r = requests.get(
            f"{TMDB_BASE_URL}/movie/{tmdb_id}",
            params={"api_key": TMDB_API_KEY},
            timeout=5
        )
        if r.status_code == 200:
            poster = r.json().get("poster_path")
            if poster:
                return f"{TMDB_IMAGE_BASE}{poster}"
    except Exception:
        pass
    return placeholder

# ==================== RECOMMENDER ====================
@st.cache_resource
def build_recommender(df):
    df["content"] = df["genres"] + " " + df["overview"]
    tfidf = TfidfVectorizer(stop_words="english")
    matrix = tfidf.fit_transform(df["content"])
    similarity = cosine_similarity(matrix)
    return similarity

def get_recommendations(title, df, similarity, top_n=5):
    idxs = df[df["title"].str.lower() == title.lower()].index
    if len(idxs) == 0:
        return pd.DataFrame()
    idx = idxs[0]
    scores = sorted(
        list(enumerate(similarity[idx])),
        key=lambda x: x[1],
        reverse=True
    )[1:top_n+1]
    indices = [i[0] for i in scores]
    return df.iloc[indices]

# ==================== THEATERS & SEATS ====================
def get_theaters_and_showtimes():
    return {
        "PVR Cinemas": ["10:00 AM", "01:30 PM", "05:00 PM", "08:30 PM"],
        "INOX": ["11:00 AM", "02:00 PM", "06:00 PM", "09:30 PM"],
        "Cinepolis": ["10:30 AM", "01:00 PM", "04:30 PM", "08:00 PM"]
    }

def get_seats():
    return [f"{r}{c}" for r in "ABCDEFGH" for c in range(1, 13)]

# ==================== BOOKINGS ====================
def save_booking(conn, data):
    c = conn.cursor()
    c.execute("""
        INSERT INTO bookings
        (user_name, user_email, movie_title, theater, showtime, seats, booking_date, total_price)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, tuple(data.values()))
    conn.commit()

def get_user_bookings(conn, email):
    return pd.read_sql(
        "SELECT * FROM bookings WHERE user_email=? ORDER BY booking_date DESC",
        conn,
        params=(email,)
    )

# ==================== MAIN ====================
def main():
    init_session()

    login_tab, signup_tab, app_tab = st.tabs(
        ["🔐 Login", "📝 Sign Up", "🎬 CineMatch"]
    )

    # LOGIN TAB
    with login_tab:
        if st.session_state.logged_in:
            st.success(f"Logged in as {st.session_state.user_name}")
        else:
            login_ui()

    # SIGNUP TAB
    with signup_tab:
        if st.session_state.logged_in:
            st.info("You are already logged in.")
        else:
            signup_ui()

    # APP TAB
    with app_tab:
        if not st.session_state.logged_in:
            st.warning("Please login or sign up to continue.")
            return

        conn = init_db()
        df = load_movie_data()
        similarity = build_recommender(df)

        st.sidebar.title("🎬 CineMatch")
        st.sidebar.write(f"👤 {st.session_state.user_name}")
        st.sidebar.write(st.session_state.user_email)

        if st.sidebar.button("🚪 Logout"):
            st.session_state.clear()
            st.rerun()

        page = st.sidebar.radio(
            "Navigate",
            ["🏠 Home", "🎯 Recommendations", "🎟️ Book Tickets", "📋 My Bookings"]
        )

        if page == "🏠 Home":
            st.title("🎬 CineMatch")
            st.subheader("AI-Powered Movie Recommendation & Booking System")

        elif page == "🎯 Recommendations":
            movie = st.selectbox("Select a movie:", df["title"])
            if st.button("Get Recommendations"):
                recs = get_recommendations(movie, df, similarity)
                for _, m in recs.iterrows():
                    col1, col2 = st.columns([1, 4])
                    with col1:
                        st.image(fetch_movie_poster(m["tmdb_id"]), width=120)
                    with col2:
                        st.subheader(m["title"])
                        if st.button(f"Book {m['title']}", key=m["title"]):
                            st.session_state.selected_movie = m["title"]
                            st.rerun()

        elif page == "🎟️ Book Tickets":
            movie = st.session_state.selected_movie or st.selectbox("Movie:", df["title"])
            m = df[df["title"] == movie].iloc[0]

            st.image(fetch_movie_poster(m["tmdb_id"]), width=200)
            st.subheader(m["title"])
            st.write(m["overview"])

            theater = st.selectbox("Theater", list(get_theaters_and_showtimes()))
            showtime = st.selectbox("Showtime", get_theaters_and_showtimes()[theater])
            seats = st.multiselect("Seats", get_seats(), max_selections=10)

            total = len(seats) * 250
            st.write(f"Total: ₹{total}")

            if st.button("Confirm Booking", disabled=not seats):
                save_booking(conn, {
                    "user_name": st.session_state.user_name,
                    "user_email": st.session_state.user_email,
                    "movie_title": movie,
                    "theater": theater,
                    "showtime": showtime,
                    "seats": ", ".join(seats),
                    "booking_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "total_price": total
                })
                st.success("Booking Confirmed 🎉")

        elif page == "📋 My Bookings":
            bookings = get_user_bookings(conn, st.session_state.user_email)
            if bookings.empty:
                st.info("No bookings found")
            else:
                for _, b in bookings.iterrows():
                    with st.expander(f"{b['movie_title']}"):
                        st.write(f"Theater: {b['theater']}")
                        st.write(f"Showtime: {b['showtime']}")
                        st.write(f"Seats: {b['seats']}")
                        st.write(f"Amount: ₹{b['total_price']}")

if __name__ == "__main__":
    main()
