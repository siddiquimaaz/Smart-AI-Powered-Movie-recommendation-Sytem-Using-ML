# # import pickle
# # import pandas as pd
# # import ast

# # # --- Load your model files ---
# # movies = pickle.load(open('model/movie_list.pkl', 'rb'))
# # similarity = pickle.load(open('model/similarity.pkl', 'rb'))

# # # --- Dummy poster fetcher (stub) ---
# # def fetch_poster(movie_id):
# #     return f"https://via.placeholder.com/150?text=Movie+ID+{movie_id}"

# # # --- Recommendation Functions ---
# # def recommend_based_on_preferences(liked_movies, movies, similarity, top_n=8):
# #     indices = []
# #     for m in liked_movies:
# #         result = movies[movies['title'] == m]
# #         if not result.empty:
# #             indices.append(result.index[0])
# #         else:
# #             print(f"⚠️ Warning: '{m}' not found in dataset.")

# #     if not indices:
# #         return [], [], []

# #     sim_scores = {}
# #     total_weight = len(indices)

# #     for idx in indices:
# #         weight = (indices.index(idx) + 1) / total_weight
# #         for i, score in enumerate(similarity[idx]):
# #             if i not in indices:
# #                 sim_scores[i] = sim_scores.get(i, 0) + (score * weight)

# #     filtered_scores = {i: score for i, score in sim_scores.items() if score > 0.1}
# #     if not filtered_scores:
# #         filtered_scores = sim_scores

# #     sorted_movies = sorted(filtered_scores.items(), key=lambda x: x[1], reverse=True)[:top_n]

# #     names = [movies.iloc[i]['title'] for i, _ in sorted_movies]
# #     posters = [fetch_poster(movies.iloc[i]['movie_id']) for i, _ in sorted_movies]
# #     scores = [score for _, score in sorted_movies]

# #     return names, posters, scores

# # def get_genre_based_recommendations(liked_movies, movies, n=8):
# #     liked_genres = []

# #     for movie in liked_movies:
# #         movie_data = movies[movies['title'] == movie]
# #         if not movie_data.empty:
# #             try:
# #                 genres = ast.literal_eval(movie_data.iloc[0]['genres'])
# #                 liked_genres.extend([g['name'] for g in genres if isinstance(g, dict) and 'name' in g])
# #             except:
# #                 pass

# #     if liked_genres:
# #         from collections import Counter
# #         genre_counts = Counter(liked_genres)
# #         top_genres = [genre for genre, _ in genre_counts.most_common(3)]

# #         recommendations = []
# #         for _, movie in movies.iterrows():
# #             if movie['title'] not in liked_movies:
# #                 try:
# #                     movie_genres = ast.literal_eval(movie['genres'])
# #                     movie_genre_names = [g['name'] for g in movie_genres if isinstance(g, dict) and 'name' in g]
# #                     if any(genre in movie_genre_names for genre in top_genres):
# #                         recommendations.append(movie)
# #                 except:
# #                     continue

# #         if recommendations:
# #             rec_df = pd.DataFrame(recommendations).sample(min(n, len(recommendations)))
# #             names = rec_df['title'].tolist()
# #             posters = [fetch_poster(mid) for mid in rec_df['movie_id']]
# #             return names, posters

# #     return [], []

# # def get_smart_recommendations(liked_movies, movies, similarity, strategy='mixed'):
# #     all_recommendations = {'names': [], 'posters': [], 'sources': []}

# #     if strategy == 'mixed' and len(liked_movies) >= 2:
# #         content_names, content_posters, _ = recommend_based_on_preferences(liked_movies, movies, similarity, top_n=6)
# #         all_recommendations['names'].extend(content_names)
# #         all_recommendations['posters'].extend(content_posters)
# #         all_recommendations['sources'].extend(['Content-Based'] * len(content_names))

# #         genre_names, genre_posters = get_genre_based_recommendations(liked_movies, movies, n=2)
# #         all_recommendations['names'].extend(genre_names)
# #         all_recommendations['posters'].extend(genre_posters)
# #         all_recommendations['sources'].extend(['Genre-Based'] * len(genre_names))
# #     else:
# #         names, posters, _ = recommend_based_on_preferences(liked_movies, movies, similarity, top_n=8)
# #         all_recommendations['names'] = names
# #         all_recommendations['posters'] = posters
# #         all_recommendations['sources'] = ['Content-Based'] * len(names)

# #     return all_recommendations

# # # --- Test runner ---
# # if __name__ == "__main__":
# #     # Example input
# #     liked_movies = [
# #     "The Matrix", 
# #     "Ender's Game", 
# #     "Star Trek: The Motion Picture",
# #     "Minority Report",
# #     "Moon",
# #     "Sunshine"]


# #     print(f"\n🧪 Testing recommendations for liked movies: {liked_movies}\n")

# #     results = get_smart_recommendations(liked_movies, movies, similarity)

# #     for i, (name, source) in enumerate(zip(results['names'], results['sources']), 1):
# #         print(f"{i}. {name} ({source})")

# import pickle
# import pandas as pd
# from updated import get_smart_recommendations

# # Load model files
# print("🔄 Loading model files...")
# movies = pickle.load(open("model/movie_list.pkl", "rb"))
# similarity = pickle.load(open("model/similarity.pkl", "rb"))

# # --- USER INPUT: Replace this with any list of movies you've liked ---
# liked_movies = [
#     "The Matrix",
#     "Ender's Game",
#     "Star Trek: The Motion Picture",
#     "Silent Running"
# ]

# print(f"\n🎬 Liked Movies: {liked_movies}")
# print("🔍 Generating recommendations...\n")

# # Run recommendation
# results = get_smart_recommendations(liked_movies, movies, similarity, strategy="mixed")

# # Print results
# for idx, (title, source) in enumerate(zip(results['names'], results['sources']), 1):
#     print(f"{idx}. {title} ({source})")

# # Optional: Debug info
# print("\n🧠 Debug Info:")
# print(f"Total recommendations: {len(results['names'])}")
# print(f"Sources used: {set(results['sources'])}")


import pickle
import os

MODEL_DIR = "model"
MOVIE_PKL = os.path.join(MODEL_DIR, "movie_list.pkl")
SIMILARITY_PKL = os.path.join(MODEL_DIR, "similarity.pkl")

def fetch_poster(movie_id):
    # Placeholder for poster fetching function (replace if needed)
    return f"Poster_for_movie_{movie_id}"

def recommend_based_on_preferences(liked_movies, movies, similarity, top_n=8, sim_threshold=0.2):
    indices = [movies[movies['title'] == m].index[0] for m in liked_movies if not movies[movies['title'] == m].empty]
    if not indices:
        return [], []

    sim_scores = {}
    total_weight = len(indices)

    for idx in indices:
        weight = (indices.index(idx) + 1) / total_weight
        for i, score in enumerate(similarity[idx]):
            movie_title = movies.iloc[i]['title']
            if i not in indices and score > sim_threshold and movie_title not in liked_movies:
                sim_scores[i] = sim_scores.get(i, 0) + (score * weight)

    sorted_movies = sorted(sim_scores.items(), key=lambda x: x[1], reverse=True)[:top_n]

    names = [movies.iloc[i]['title'] for i, _ in sorted_movies]
    posters = [fetch_poster(movies.iloc[i]['movie_id']) for i, _ in sorted_movies]
    scores = [score for _, score in sorted_movies]

    return names, posters, scores

def test_recommendations(liked_movies):
    print(f"🎬 Liked Movies: {liked_movies}")
    print("🔍 Generating recommendations...")

    movies = pickle.load(open(MOVIE_PKL, 'rb'))
    similarity = pickle.load(open(SIMILARITY_PKL, 'rb'))

    names, posters, scores = recommend_based_on_preferences(liked_movies, movies, similarity, top_n=6)

    if not names:
        print("No recommendations found. Try different liked movies.")
        return

    print()
    for i, (name, source, score) in enumerate(zip(names, ['Content-Based']*len(names), scores), 1):
        print(f"{i}. {name} ({source}) - Similarity Score: {score:.3f}")

if __name__ == "__main__":
    liked = ['The Matrix', "Ender's Game", 'Star Trek: The Motion Picture', 'Silent Running']
    test_recommendations(liked)
