# # # # import pickle
# # # # import pandas as pd
# # # # import ast

# # # # # --- Load your model files ---
# # # # movies = pickle.load(open('model/movie_list.pkl', 'rb'))
# # # # similarity = pickle.load(open('model/similarity.pkl', 'rb'))

# # # # # --- Dummy poster fetcher (stub) ---
# # # # def fetch_poster(movie_id):
# # # #     return f"https://via.placeholder.com/150?text=Movie+ID+{movie_id}"

# # # # # --- Recommendation Functions ---
# # # # def recommend_based_on_preferences(liked_movies, movies, similarity, top_n=8):
# # # #     indices = []
# # # #     for m in liked_movies:
# # # #         result = movies[movies['title'] == m]
# # # #         if not result.empty:
# # # #             indices.append(result.index[0])
# # # #         else:
# # # #             print(f"⚠️ Warning: '{m}' not found in dataset.")

# # # #     if not indices:
# # # #         return [], [], []

# # # #     sim_scores = {}
# # # #     total_weight = len(indices)

# # # #     for idx in indices:
# # # #         weight = (indices.index(idx) + 1) / total_weight
# # # #         for i, score in enumerate(similarity[idx]):
# # # #             if i not in indices:
# # # #                 sim_scores[i] = sim_scores.get(i, 0) + (score * weight)

# # # #     filtered_scores = {i: score for i, score in sim_scores.items() if score > 0.1}
# # # #     if not filtered_scores:
# # # #         filtered_scores = sim_scores

# # # #     sorted_movies = sorted(filtered_scores.items(), key=lambda x: x[1], reverse=True)[:top_n]

# # # #     names = [movies.iloc[i]['title'] for i, _ in sorted_movies]
# # # #     posters = [fetch_poster(movies.iloc[i]['movie_id']) for i, _ in sorted_movies]
# # # #     scores = [score for _, score in sorted_movies]

# # # #     return names, posters, scores

# # # # def get_genre_based_recommendations(liked_movies, movies, n=8):
# # # #     liked_genres = []

# # # #     for movie in liked_movies:
# # # #         movie_data = movies[movies['title'] == movie]
# # # #         if not movie_data.empty:
# # # #             try:
# # # #                 genres = ast.literal_eval(movie_data.iloc[0]['genres'])
# # # #                 liked_genres.extend([g['name'] for g in genres if isinstance(g, dict) and 'name' in g])
# # # #             except:
# # # #                 pass

# # # #     if liked_genres:
# # # #         from collections import Counter
# # # #         genre_counts = Counter(liked_genres)
# # # #         top_genres = [genre for genre, _ in genre_counts.most_common(3)]

# # # #         recommendations = []
# # # #         for _, movie in movies.iterrows():
# # # #             if movie['title'] not in liked_movies:
# # # #                 try:
# # # #                     movie_genres = ast.literal_eval(movie['genres'])
# # # #                     movie_genre_names = [g['name'] for g in movie_genres if isinstance(g, dict) and 'name' in g]
# # # #                     if any(genre in movie_genre_names for genre in top_genres):
# # # #                         recommendations.append(movie)
# # # #                 except:
# # # #                     continue

# # # #         if recommendations:
# # # #             rec_df = pd.DataFrame(recommendations).sample(min(n, len(recommendations)))
# # # #             names = rec_df['title'].tolist()
# # # #             posters = [fetch_poster(mid) for mid in rec_df['movie_id']]
# # # #             return names, posters

# # # #     return [], []

# # # # def get_smart_recommendations(liked_movies, movies, similarity, strategy='mixed'):
# # # #     all_recommendations = {'names': [], 'posters': [], 'sources': []}

# # # #     if strategy == 'mixed' and len(liked_movies) >= 2:
# # # #         content_names, content_posters, _ = recommend_based_on_preferences(liked_movies, movies, similarity, top_n=6)
# # # #         all_recommendations['names'].extend(content_names)
# # # #         all_recommendations['posters'].extend(content_posters)
# # # #         all_recommendations['sources'].extend(['Content-Based'] * len(content_names))

# # # #         genre_names, genre_posters = get_genre_based_recommendations(liked_movies, movies, n=2)
# # # #         all_recommendations['names'].extend(genre_names)
# # # #         all_recommendations['posters'].extend(genre_posters)
# # # #         all_recommendations['sources'].extend(['Genre-Based'] * len(genre_names))
# # # #     else:
# # # #         names, posters, _ = recommend_based_on_preferences(liked_movies, movies, similarity, top_n=8)
# # # #         all_recommendations['names'] = names
# # # #         all_recommendations['posters'] = posters
# # # #         all_recommendations['sources'] = ['Content-Based'] * len(names)

# # # #     return all_recommendations

# # # # # --- Test runner ---
# # # # if __name__ == "__main__":
# # # #     # Example input
# # # #     liked_movies = [
# # # #     "The Matrix", 
# # # #     "Ender's Game", 
# # # #     "Star Trek: The Motion Picture",
# # # #     "Minority Report",
# # # #     "Moon",
# # # #     "Sunshine"]


# # # #     print(f"\n🧪 Testing recommendations for liked movies: {liked_movies}\n")

# # # #     results = get_smart_recommendations(liked_movies, movies, similarity)

# # # #     for i, (name, source) in enumerate(zip(results['names'], results['sources']), 1):
# # # #         print(f"{i}. {name} ({source})")

# # # import pickle
# # # import pandas as pd
# # # from updated import get_smart_recommendations

# # # # Load model files
# # # print("🔄 Loading model files...")
# # # movies = pickle.load(open("model/movie_list.pkl", "rb"))
# # # similarity = pickle.load(open("model/similarity.pkl", "rb"))

# # # # --- USER INPUT: Replace this with any list of movies you've liked ---
# # # liked_movies = [
# # #     "The Matrix",
# # #     "Ender's Game",
# # #     "Star Trek: The Motion Picture",
# # #     "Silent Running"
# # # ]

# # # print(f"\n🎬 Liked Movies: {liked_movies}")
# # # print("🔍 Generating recommendations...\n")

# # # # Run recommendation
# # # results = get_smart_recommendations(liked_movies, movies, similarity, strategy="mixed")

# # # # Print results
# # # for idx, (title, source) in enumerate(zip(results['names'], results['sources']), 1):
# # #     print(f"{idx}. {title} ({source})")

# # # # Optional: Debug info
# # # print("\n🧠 Debug Info:")
# # # print(f"Total recommendations: {len(results['names'])}")
# # # print(f"Sources used: {set(results['sources'])}")


# # import pickle
# # import os

# # MODEL_DIR = "model"
# # MOVIE_PKL = os.path.join(MODEL_DIR, "movie_list.pkl")
# # SIMILARITY_PKL = os.path.join(MODEL_DIR, "similarity.pkl")

# # def fetch_poster(movie_id):
# #     # Placeholder for poster fetching function (replace if needed)
# #     return f"Poster_for_movie_{movie_id}"

# # def recommend_based_on_preferences(liked_movies, movies, similarity, top_n=8, sim_threshold=0.2):
# #     indices = [movies[movies['title'] == m].index[0] for m in liked_movies if not movies[movies['title'] == m].empty]
# #     if not indices:
# #         return [], []

# #     sim_scores = {}
# #     total_weight = len(indices)

# #     for idx in indices:
# #         weight = (indices.index(idx) + 1) / total_weight
# #         for i, score in enumerate(similarity[idx]):
# #             movie_title = movies.iloc[i]['title']
# #             if i not in indices and score > sim_threshold and movie_title not in liked_movies:
# #                 sim_scores[i] = sim_scores.get(i, 0) + (score * weight)

# #     sorted_movies = sorted(sim_scores.items(), key=lambda x: x[1], reverse=True)[:top_n]

# #     names = [movies.iloc[i]['title'] for i, _ in sorted_movies]
# #     posters = [fetch_poster(movies.iloc[i]['movie_id']) for i, _ in sorted_movies]
# #     scores = [score for _, score in sorted_movies]

# #     return names, posters, scores

# # def test_recommendations(liked_movies):
# #     print(f"🎬 Liked Movies: {liked_movies}")
# #     print("🔍 Generating recommendations...")

# #     movies = pickle.load(open(MOVIE_PKL, 'rb'))
# #     similarity = pickle.load(open(SIMILARITY_PKL, 'rb'))

# #     names, posters, scores = recommend_based_on_preferences(liked_movies, movies, similarity, top_n=6)

# #     if not names:
# #         print("No recommendations found. Try different liked movies.")
# #         return

# #     print()
# #     for i, (name, source, score) in enumerate(zip(names, ['Content-Based']*len(names), scores), 1):
# #         print(f"{i}. {name} ({source}) - Similarity Score: {score:.3f}")

# # if __name__ == "__main__":
# #     liked = ['The Matrix', "Ender's Game", 'Star Trek: The Motion Picture', 'Silent Running']
# #     test_recommendations(liked)
# import requests
# import firebase_admin
# from firebase_admin import credentials, firestore

# # --- Firebase config ---
# FIREBASE_API_KEY = "*****************************"  # Replace this!
# SIGNIN_URL = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}"

# # --- Firebase Admin Init ---
# cred = credentials.Certificate("firebase.json")  # Replace path
# if not firebase_admin._apps:
#     firebase_admin.initialize_app(cred)
# db = firestore.client()

# # --- Sign in user ---
# def sign_in(email, password):
#     payload = {
#         "email": email,
#         "password": password,
#         "returnSecureToken": True
#     }
#     try:
#         response = requests.post(SIGNIN_URL, json=payload)
#         result = response.json()
#         if "error" in result:
#             print(f"❌ Login error: {result['error']['message']}")
#             return None
#         print(f"✅ Logged in as {result['email']}")
#         return result  # contains idToken, localId, etc.
#     except Exception as e:
#         print(f"❌ Exception during login: {e}")
#         return None

# # --- Save likes ---
# def save_likes_to_db(user_id, liked_movies):
#     try:
#         db.collection('users').document(user_id).set({
#             'liked_movies': liked_movies,
#             'preferences_set': bool(liked_movies)
#         }, merge=True)
#         print(f"✅ Saved likes for user: {user_id}")
#     except Exception as e:
#         print(f"❌ Error saving likes: {e}")

# # --- Get likes ---
# def get_likes_from_db(user_id):
#     try:
#         doc = db.collection('users').document(user_id).get()
#         if doc.exists:
#             likes = doc.to_dict().get('liked_movies', [])
#             print(f"✅ Retrieved likes: {likes}")
#             return likes
#         else:
#             print("⚠️ No document found.")
#             return []
#     except Exception as e:
#         print(f"❌ Error fetching likes: {e}")
#         return []

# # --- MAIN ---
# if __name__ == "__main__":
#     email = input("Enter email: ")
#     password = input("Enter password: ")

#     auth_result = sign_in(email, password)
#     if auth_result:
#         user_id = auth_result["localId"]
#         sample_likes = ["Oppenheimer", "Interstellar", "The Batman"]

#         save_likes_to_db(user_id, sample_likes)
#         get_likes_from_db(user_id)
# import streamlit as st

# st.write("Secrets loaded:", st.secrets)
# st.write("Firebase project ID:", st.secrets["firebase"]["service_account"]["project_id"])
# import streamlit as st

# pk = st.secrets["firebase"]["service_account"]["private_key"]
# print("First 20 chars of key:", pk[:20])
# print("Length of key:", len(pk))

# import streamlit as st
# from admin_db import db
# from auth import sign_in
# import os
# import pickle

# st.title("Smart Movie Recommender - Comprehensive Test Suite")

# # --- 1. User Authentication and Info Fetch ---
# st.header("1. User Authentication & Info Fetch")
# email = st.text_input("Enter your email")
# password = st.text_input("Enter your password", type="password")

# if st.button("Fetch User Details"):
#     if not email or not password:
#         st.warning("Please enter both email and password.")
#     else:
#         res = sign_in(email, password)
#         if res and res.get("status") == "success":
#             uid = res.get("uid")
#             st.success(f"Authenticated! UID: {uid}")
#             user_data = db.collection('users').document(uid).get().to_dict() or {}
#             st.subheader("User Details from Firestore:")
#             st.json(user_data)
#             if 'display_name' in user_data:
#                 st.info(f"Display Name: {user_data['display_name']}")
#         else:
#             st.error(f"Authentication failed: {res.get('message', 'Unknown error') if res else 'Unknown error'}")

# # --- 2. Model File Loading and Structure ---
# st.header("2. Model File Loading & Structure")
# MOVIE_PKL = os.path.join("model", "movie_list.pkl")
# SIMILARITY_PKL = os.path.join("model", "similarity.pkl")

# try:
#     movies = pickle.load(open(MOVIE_PKL, 'rb'))
#     st.success(f"Loaded movies DataFrame: {type(movies)}, shape: {movies.shape}")
#     st.write(movies.head(2))
# except Exception as e:
#     st.error(f"Failed to load movies: {e}")
#     movies = None

# try:
#     similarity = pickle.load(open(SIMILARITY_PKL, 'rb'))
#     st.success(f"Loaded similarity matrix: {type(similarity)}, shape: {getattr(similarity, 'shape', 'N/A')}")
# except Exception as e:
#     st.error(f"Failed to load similarity: {e}")
#     similarity = None

# # --- 3. Genre and Movie Field Integrity ---
# st.header("3. Genre & Movie Field Integrity")
# if movies is not None:
#     required_columns = ['movie_id', 'title', 'genres']
#     missing = [col for col in required_columns if col not in movies.columns]
#     if missing:
#         st.error(f"Missing columns: {missing}")
#     else:
#         st.success("All required columns present.")
#     st.write("Sample genres field:", movies.iloc[0]['genres'])

# # --- 4. Poster Fetching Test ---
# st.header("4. Poster Fetching Test")
# def fetch_poster(movie_id, size='w500'):
#     import requests
#     api_key = st.secrets.get("tmdb_api_key", "")
#     placeholder_base = "https://via.placeholder.com/500x750"
#     if not api_key:
#         return f"{placeholder_base}?text=No+API+Key"
#     try:
#         url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}&language=en-US"
#         response = requests.get(url, timeout=5)
#         if response.status_code != 200:
#             return f"{placeholder_base}?text=TMDB+Error+{response.status_code}"
#         data = response.json()
#         poster_path = data.get('poster_path')
#         if not poster_path:
#             return f"{placeholder_base}?text=No+Poster"
#         return f"https://image.tmdb.org/t/p/{size}/{poster_path}"
#     except Exception as e:
#         return f"{placeholder_base}?text=Error"

# if movies is not None:
#     sample_movie = movies.iloc[0]
#     poster_url = fetch_poster(sample_movie['movie_id'])
#     st.image(poster_url, caption=f"Poster for {sample_movie['title']}")

# # --- 5. Recommendation Output Test ---
# st.header("5. Recommendation Output Test")
# if movies is not None and similarity is not None:
#     # Simulate a user with a few liked movies
#     liked_movies = movies['title'].sample(3).tolist()
#     disliked_movies = movies['title'].sample(2).tolist()
#     st.write(f"Liked movies: {liked_movies}")
#     st.write(f"Disliked movies: {disliked_movies}")
#     # Import the recommendation function from updated.py
#     from updated import get_ultimate_recommendations
#     names, posters, sources = get_ultimate_recommendations(liked_movies, disliked_movies, movies, similarity, top_n=5)
#     st.write("Recommendations:", names)
#     for name, poster, src in zip(names, posters, sources):
#         st.image(poster, caption=f"{name} ({src})")

# # --- 6. Edge Cases ---
# st.header("6. Edge Cases")
# if movies is not None and similarity is not None:
#     st.subheader("Empty likes/dislikes")
#     names, posters, sources = get_ultimate_recommendations([], [], movies, similarity, top_n=3)
#     st.write("Result:", names)

#     st.subheader("Invalid movie names")
#     names, posters, sources = get_ultimate_recommendations(["NotARealMovie123"], [], movies, similarity, top_n=3)
#     st.write("Result:", names)

#     st.subheader("All disliked")
#     all_disliked = movies['title'].sample(5).tolist()
#     names, posters, sources = get_ultimate_recommendations([], all_disliked, movies, similarity, top_n=3)
#     st.write("Result:", names)

#     st.subheader("Large feedback (20 likes, 20 dislikes)")
#     many_likes = movies['title'].sample(20).tolist()
#     many_dislikes = movies['title'].sample(20).tolist()
#     names, posters, sources = get_ultimate_recommendations(many_likes, many_dislikes, movies, similarity, top_n=3)
#     st.write("Result:", names)

# st.success("All tests completed.")


