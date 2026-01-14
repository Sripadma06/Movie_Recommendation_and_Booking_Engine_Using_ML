# check_poster.py -- robust tester (save in your project folder)
from dotenv import load_dotenv
load_dotenv()

import os, requests, sys
print("Python executable:", sys.executable)
print("CWD:", os.getcwd())

# show raw .env file if exists
env_path = os.path.join(os.getcwd(), ".env")
print(".env exists:", os.path.exists(env_path))
if os.path.exists(env_path):
    print("---- .env contents (repr) ----")
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            print(repr(line.rstrip("\n")))
    print("---- end .env ----")

val = os.getenv("TMDB_API_KEY")
print("TMDB_API_KEY present (bool):", bool(val))
print("TMDB_API_KEY repr:", repr(val))

# if there's a value, test TMDB request
if val:
    tmdb_id = 238
    url = f"https://api.themoviedb.org/3/movie/{tmdb_id}?api_key={val}"
    print("Requesting:", url)
    try:
        r = requests.get(url, timeout=8)
        print("Status code:", r.status_code)
        try:
            print("poster_path:", r.json().get("poster_path"))
        except Exception as e:
            print("json parse error:", e)
            print(r.text[:500])
    except Exception as e:
        print("Requests error:", e)
else:
    print("No TMDB_API_KEY set in environment.")
