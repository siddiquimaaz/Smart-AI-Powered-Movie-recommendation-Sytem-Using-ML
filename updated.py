import os
import pickle
import pandas as pd
import streamlit as st
import requests
import ast
from collections import Counter, defaultdict
import traceback
import random
import difflib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from auth import sign_in, sign_up, get_name
import firebase_admin
from firebase_admin import credentials, firestore
from admin_db import db,get_likes_from_db,save_likes_to_db
import time
from css import load_css  # Import custom CSS for styling
import numpy as np

# Add at the top of the file
DEBUG = False  # Set to True for developer debugging, False for users

# Firebase Init

# Paths
DATA_DIR = "/Dataset"
MOVIES_PATH = os.path.join(DATA_DIR, "tmdb_5000_movies.csv")
CREDITS_PATH = os.path.join(DATA_DIR, "tmdb_5000_credits.csv")
MODEL_DIR = "model"
MOVIE_PKL = os.path.join(MODEL_DIR, "movie_list.pkl")
SIMILARITY_PKL = os.path.join(MODEL_DIR, "similarity.pkl")

# --- Helper Functions ---
def fetch_poster(movie_id, size='w500'):
    """Fetches poster URL from TMDB using movie_id with fallback and timeout handling."""
    api_key = st.secrets.get("tmdb_api_key", "")
    placeholder_base = "https://via.placeholder.com/500x750"

    if not api_key:
        return f"{placeholder_base}?text=No+API+Key"

    try:
        url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}&language=en-US"
        response = requests.get(url, timeout=5)
        
        if response.status_code != 200:
            return f"{placeholder_base}?text=TMDB+Error+{response.status_code}"

        data = response.json()
        poster_path = data.get('poster_path')
        
        if not poster_path:
            return f"{placeholder_base}?text=No+Poster"

        return f"https://image.tmdb.org/t/p/{size}/{poster_path}"
    
    except requests.exceptions.Timeout:
        return f"{placeholder_base}?text=Timeout"

    except requests.exceptions.RequestException as e:
        # Optional: log the error for debugging
        if DEBUG:
            print(f"[Poster Fetch Error] movie_id={movie_id}: {e}")
        return f"{placeholder_base}?text=Fetch+Error"

    except Exception as e:
        if DEBUG:
            print(f"[Unexpected Error] movie_id={movie_id}: {e}")
        return f"{placeholder_base}?text=Unknown+Error"


def get_popular_movies(movies, n=8):
    """Get popular movies based on available columns"""
    possible_columns = ['vote_average', 'popularity', 'vote_count', 'revenue', 'budget']
    
    for col in possible_columns:
        if col in movies.columns:
            try:
                if col in ['vote_average', 'popularity']:
                    return movies.nlargest(n, col)
                elif col in ['vote_count', 'revenue', 'budget']:
                    return movies.nlargest(n, col)
            except Exception as e:
                continue
    
    return movies.sample(n)

def handle_like_toggle(movie_name, key_suffix=""):
    if movie_name in st.session_state.liked_movies:
        st.session_state.liked_movies.remove(movie_name)
        st.success(f"❤️ Removed '{movie_name}' from your likes!")
    else:
        st.session_state.liked_movies.append(movie_name)
        st.success(f"💖 Added '{movie_name}' to your likes!")

    st.write("🔄 Attempting to update Firebase...")
    st.write("Current liked movies:", st.session_state.liked_movies)
    st.write("User:", st.session_state.username)

    try:
        if DEBUG:
            print(f"[DEBUG] Writing likes for user {st.session_state.uid}: {st.session_state.liked_movies}")
        result = db.collection('users').document(st.session_state.uid).set({
            'liked_movies': st.session_state.liked_movies,
            'preferences_set': bool(st.session_state.liked_movies),
            'email': st.session_state.username  # Store email as a field
        }, merge=True)
        if DEBUG:
            print("[DEBUG] Firestore write result:", result)
        st.success("✅ Firebase updated successfully!")
    except Exception as e:
        st.error(f"❌ Failed to save to database.")
        st.exception(e)
        traceback.print_exc()

# Cache recommendations for better performance
@st.cache_data(ttl=1800)  # Cache for 30 minutes
def get_ultimate_recommendations(liked_movies, disliked_movies, movies, similarity, top_n=10, genre_boost=0.25):
    """
    Enhanced Hybrid Movie Recommendation System:
    - Content-Based Filtering (movie features similarity)
    - Genre-Based Collaborative Filtering (genre preferences)
    - Mood-Based Filtering (genre mood analysis)
    - Popularity-Aware Scoring (quality + popularity balance)
    - User Feedback Integration (likes/dislikes with weights)
    - Diversity Control (prevent similar recommendations)
    - Recency Bias (favor newer movies slightly)
    """

    # === Sanity Checks ===
    if not liked_movies:
        if DEBUG:
            print("⚠️ No liked movies provided.")
        return [], [], []
    if similarity is None:
        if DEBUG:
            print("⚠️ Similarity matrix is None.")
        return [], [], []
    if movies is None or movies.empty:
        if DEBUG:
            print("⚠️ Movies dataframe is empty or None.")
        return [], [], []
    if 'genres' not in movies.columns:
        if DEBUG:
            print("⚠️ 'genres' column not found in movies dataframe.")
        return [], [], []

    # === Helper: Safe movie title to index ===
    def safe_index_lookup(title):
        match = movies[movies['title'] == title]
        return match.index[0] if not match.empty else None

    liked_indices = list(filter(lambda x: x is not None, [safe_index_lookup(title) for title in liked_movies]))
    disliked_indices = list(filter(lambda x: x is not None, [safe_index_lookup(title) for title in disliked_movies]))

    if not liked_indices:
        if DEBUG:
            print("⚠️ No valid liked movie indices found.")
        return [], [], []

    try:
        similarity_matrix = np.array(similarity)
        content_scores = {}

        # === PHASE 1: Enhanced Content-Based Similarity ===
        for i, idx in enumerate(liked_indices):
            # Weight by recency (more recent likes get higher weight)
            recency_weight = (len(liked_indices) - i) / len(liked_indices)
            if i == 0:  # Most recent like gets extra weight
                recency_weight *= 1.5
            
            scores = similarity_matrix[idx]
            for j, score in enumerate(scores):
                if j in liked_indices or j in disliked_indices:
                    continue
                content_scores[j] = content_scores.get(j, 0) + score * recency_weight

        # === PHASE 2: Genre and Mood Analysis ===
        def extract_genres(title_list):
            genres = []
            for title in title_list:
                match = movies[movies['title'] == title]
                if not match.empty:
                    raw = match.iloc[0]['genres']
                    try:
                        parsed = ast.literal_eval(raw) if isinstance(raw, str) else raw
                        genres.extend([g['name'] for g in parsed if isinstance(g, dict) and 'name' in g])
                    except:
                        continue
            return genres

        liked_genres = extract_genres(liked_movies)
        disliked_genres = set(extract_genres(disliked_movies))

        # Genre preferences
        genre_counter = Counter(liked_genres)
        top_genres = set([g for g, _ in genre_counter.most_common(5)])
        
        # Mood-based genre grouping
        mood_genres = {
            'action': ['Action', 'Adventure', 'War', 'Thriller'],
            'comedy': ['Comedy', 'Romance', 'Family'],
            'drama': ['Drama', 'History', 'Biography'],
            'scifi': ['Science Fiction', 'Fantasy', 'Animation'],
            'horror': ['Horror', 'Mystery', 'Crime']
        }
        
        # Find user's preferred moods
        user_moods = set()
        for genre in liked_genres:
            for mood, mood_genres_list in mood_genres.items():
                if genre in mood_genres_list:
                    user_moods.add(mood)

        # === PHASE 3: Enhanced Scoring ===
        final_scores = {}
        recommendation_sources = {}
        
        for idx, base_score in content_scores.items():
            try:
                raw = movies.iloc[idx]['genres']
                parsed = ast.literal_eval(raw) if isinstance(raw, str) else raw
                genre_list = [g['name'] for g in parsed if isinstance(g, dict) and 'name' in g]
            except:
                genre_list = []

            # Skip disliked movies and genres
            if movies.iloc[idx]['title'] in disliked_movies or any(g in disliked_genres for g in genre_list):
                continue

            score = base_score
            source_parts = []

            # Genre boosting
            genre_matches = sum(1 for g in genre_list if g in top_genres)
            if genre_matches > 0:
                score *= (1 + genre_boost * (2 ** (genre_matches - 1)))
                if genre_matches >= 2:
                    source_parts.append(f"Multi-genre match ({genre_matches})")
                else:
                    source_parts.append("Genre preference")

            # Mood matching
            movie_moods = set()
            for genre in genre_list:
                for mood, mood_genres_list in mood_genres.items():
                    if genre in mood_genres_list:
                        movie_moods.add(mood)
            
            mood_overlap = len(user_moods & movie_moods)
            if mood_overlap > 0:
                score *= (1 + 0.15 * mood_overlap)
                source_parts.append("Mood match")

            # Quality boost
            if 'vote_average' in movies.columns and 'vote_count' in movies.columns:
                try:
                    vote_avg = movies.iloc[idx]['vote_average']
                    vote_count = movies.iloc[idx]['vote_count']
                    if vote_avg > 7.0 and vote_count > 100:
                        score *= 1.1
                        source_parts.append("High quality")
                    elif vote_count > 1000:
                        score *= 1.05
                        source_parts.append("Popular choice")
                except:
                    pass

            # Recency boost
            if 'release_date' in movies.columns:
                try:
                    release_date = movies.iloc[idx]['release_date']
                    if pd.notna(release_date):
                        year = pd.to_datetime(release_date).year
                        if year >= 2010:
                            score *= 1.05
                        elif year >= 2000:
                            score *= 1.02
                except:
                    pass

            final_scores[idx] = score
            recommendation_sources[idx] = " + ".join(source_parts) if source_parts else "Similar content"

        if not final_scores:
            if DEBUG:
                print("⚠️ No final recommendations could be computed.")
            return [], [], []

        # === PHASE 4: Diversity-Aware Selection ===
        ranked = sorted(final_scores.items(), key=lambda x: x[1], reverse=True)
        selected_indices = []
        
        for idx, score in ranked:
            if len(selected_indices) >= top_n:
                break
            
            # Check for diversity
            too_similar = False
            for selected_idx in selected_indices:
                if similarity_matrix[idx][selected_idx] > 0.85:
                    too_similar = True
                    break
            
            if not too_similar:
                selected_indices.append(idx)
        
        # Fill remaining slots
        if len(selected_indices) < top_n:
            remaining = [idx for idx, _ in ranked if idx not in selected_indices]
            selected_indices.extend(remaining[:top_n - len(selected_indices)])
        
        # Prepare results
        names = [movies.iloc[i]['title'] for i in selected_indices]
        posters = [fetch_poster(movies.iloc[i]['movie_id']) for i in selected_indices]
        sources = [f"🎯 {recommendation_sources.get(i, 'AI Recommendation')} (Score: {final_scores[i]:.2f})" 
                  for i in selected_indices]
        
        return names, posters, sources
        
    except Exception as e:
        if DEBUG:
            print(f"⚠️ Error in recommendation calculation: {str(e)}")
        return [], [], []

def display_movies_grid(names, posters, movies, key_prefix="", allow_like=True, columns=4, sources=None, show_explanation=False, show_ratings=True):
    """Enhanced movie grid display with card-based UI and ratings badge in top right"""
    # Input validation
    if not names or not posters:
        return
    if len(names) != len(posters):
        if DEBUG:
            st.warning("Mismatch between movie names and posters")
        return
    if movies is None:
        if DEBUG:
            st.warning("Movie data not available")
        return
    num_movies = len(names)
    cols = st.columns(min(columns, num_movies))
    for idx, (name, poster) in enumerate(zip(names, posters)):
        with cols[idx % columns]:
            try:
                # Validate movie name
                if not name or pd.isna(name):
                    continue
                # Get movie genres for this card (fix: use list of strings)
                genres = []
                if movies is not None:
                    try:
                        movie_data = movies[movies['title'] == name]
                        if not movie_data.empty and 'genres' in movie_data.columns:
                            genres_val = movie_data.iloc[0]['genres']
                            if isinstance(genres_val, list):
                                genres = genres_val
                            else:
                                genres = []
                    except Exception as e:
                        genres = []
                        if DEBUG:
                            print(f"[DEBUG] Error extracting genres for {name}: {e}")
                # Create a card-like container with relative positioning
                with st.container():
                    st.markdown(
                        """
                        <div style='position: relative; width: 100%;'>
                        """,
                        unsafe_allow_html=True
                    )
                    # Movie poster with error handling and alt text
                    try:
                        alt_text = f"Poster for {name}" if name else "Movie poster"
                        # Ensure movie_id is int and not NaN before fetching poster
                        movie_data = movies[movies['title'] == name]
                        movie_id = None
                        if not movie_data.empty and 'movie_id' in movie_data.columns:
                            mid_val = movie_data.iloc[0]['movie_id']
                            if not pd.isna(mid_val):
                                try:
                                    movie_id = int(mid_val)
                                except Exception as e:
                                    if DEBUG:
                                        print(f"[DEBUG] Invalid movie_id for {name}: {mid_val}")
                        if movie_id is not None:
                            poster_url = fetch_poster(movie_id)
                        else:
                            poster_url = "https://via.placeholder.com/500x750?text=No+Image"
                        if poster_url and poster_url != "https://via.placeholder.com/500x750?text=No+Image":
                            st.image(poster_url, use_container_width=True, caption="", output_format="auto", channels="RGB", clamp=False, width=None)
                        else:
                            st.image("https://via.placeholder.com/500x750?text=No+Image", 
                                    use_container_width=True, caption="")
                    except Exception as e:
                        st.image("https://via.placeholder.com/500x750?text=Image+Error", 
                                use_container_width=True, caption="")
                        if DEBUG:
                            print(f"[DEBUG] Error displaying poster for {name}: {e}")
                    # Movie rating badge (top right)
                    if show_ratings and movies is not None:
                        try:
                            movie_data = movies[movies['title'] == name]
                            if not movie_data.empty:
                                rating = movie_data.iloc[0].get('vote_average')
                                if pd.notna(rating) and rating > 0:
                                    st.markdown(f"""
                                    <div style='position: absolute; top: 10px; right: 10px; background: #FFD700; color: #222; padding: 0.35em 0.8em; border-radius: 1em; font-weight: bold; font-size: 1.05em; box-shadow: 0 2px 8px rgba(0,0,0,0.12); z-index: 2;'>
                                        ⭐ {rating:.1f}
                                    </div>
                                    """, unsafe_allow_html=True)
                        except Exception as e:
                            if DEBUG:
                                print(f"[DEBUG] Error displaying rating for {name}: {e}")
                            pass
                    # Movie title with better styling
                    try:
                        st.markdown(f"""
                        <div style="text-align: center; margin: 0.5rem 0;">
                            <h6 style="color: white; margin: 0; font-size: 0.9rem; line-height: 1.2;">
                                {str(name)[:50]}{'...' if len(str(name)) > 50 else ''}
                            </h6>
                        </div>
                        """, unsafe_allow_html=True)
                    except Exception as e:
                        st.write(f"**{str(name)[:30]}...**")
                        if DEBUG:
                            print(f"[DEBUG] Error displaying title for {name}: {e}")
                    # Show genres as chips/badges
                    if genres:
                        st.markdown(
                            '<div style="display: flex; flex-wrap: wrap; justify-content: center; gap: 0.3em; margin-bottom: 0.5em;">' +
                            ''.join([
                                f'<span style="background: #222; color: #FFD700; border-radius: 0.7em; padding: 0.2em 0.8em; font-size: 0.8em; margin: 0 0.1em;">{g}</span>'
                                for g in genres
                            ]) +
                            '</div>',
                            unsafe_allow_html=True
                        )
                    # Show recommendation explanation
                    if show_explanation and sources and idx < len(sources):
                        try:
                            source = sources[idx]
                            st.caption(f"💡 Why this movie? {source}")
                        except Exception as e:
                            if DEBUG:
                                print(f"[DEBUG] Error displaying explanation for {name}: {e}")
                            pass
                    # Feedback buttons with better UX and alt text
                    if allow_like:
                        try:
                            display_movie_feedback_buttons(name, idx, key_prefix, genres)
                        except Exception as e:
                            if DEBUG:
                                print(f"[DEBUG] Error displaying feedback buttons for {name}: {e}")
                            pass
            except Exception as e:
                st.error(f"Error displaying movie: {str(name)[:20]}... Exception: {e}")
                if DEBUG:
                    print(f"[DEBUG] Error displaying movie: {name}, Exception: {e}")
                continue

def display_movie_feedback_buttons(movie_name, idx, key_prefix, genres=None):
    """Separate function for movie feedback buttons with better UX and accessibility alt text"""
    unique_key = f"{key_prefix}_{hash(movie_name)}_{idx}"
    is_liked = movie_name in st.session_state.liked_movies
    is_disliked = movie_name in st.session_state.disliked_movies
    col_like, col_dislike = st.columns(2)
    with col_like:
        button_text = "❤️ Liked" if is_liked else "🤍 Like"
        alt_text = f"Like {movie_name} ({', '.join(genres)})" if genres else f"Like {movie_name}"
        if st.button(button_text, key=f"like_{unique_key}", use_container_width=True, help=alt_text):
            if handle_movie_feedback(movie_name, 'like'):
                st.success("👍 Added to your likes!")
                time.sleep(0.5)
                st.rerun()
    with col_dislike:
        button_text = "👎 Disliked" if is_disliked else "👎 Dislike"
        alt_text = f"Dislike {movie_name} ({', '.join(genres)})" if genres else f"Dislike {movie_name}"
        if st.button(button_text, key=f"dislike_{unique_key}", use_container_width=True, help=alt_text):
            if handle_movie_feedback(movie_name, 'dislike'):
                st.info("👎 We'll avoid similar movies!")
                time.sleep(0.5)
                st.rerun()

# Cache movie suggestions for better performance
@st.cache_data(ttl=3600)
def get_movie_suggestions(query, movies, limit=10):
    """Get comprehensive movie suggestions for autocomplete with improved algorithm"""
    if not query or len(query) < 2:
        return []
    
    # Create lowercase title column for faster searching
    if 'title_lower' not in movies.columns:
        movies['title_lower'] = movies['title'].str.lower()
    
    query_lower = query.lower()
    suggestions = []
    
    # 1. Exact matches (highest priority)
    exact_matches = movies[movies['title_lower'] == query_lower]['title'].tolist()
    suggestions.extend(exact_matches)
    
    # 2. Starts with matches (high priority)
    starts_with = movies[movies['title_lower'].str.startswith(query_lower)]['title'].tolist()
    suggestions.extend([m for m in starts_with if m not in suggestions])
    
    # 3. Contains matches (medium priority)
    contains = movies[movies['title_lower'].str.contains(query_lower, na=False)]['title'].tolist()
    suggestions.extend([m for m in contains if m not in suggestions])
    
    # 4. Fuzzy matches for better suggestions (lower priority)
    if len(suggestions) < limit:
        from difflib import get_close_matches
        all_titles = movies['title'].tolist()
        fuzzy_matches = get_close_matches(query_lower, [t.lower() for t in all_titles], n=5, cutoff=0.6)
        fuzzy_matches = [movies[movies['title_lower'] == m]['title'].iloc[0] for m in fuzzy_matches if m]
        suggestions.extend([m for m in fuzzy_matches if m not in suggestions])
    
    return suggestions[:limit]

def search_movies_improved(query, movies, filters=None):
    """Enhanced movie search with filters and better matching"""
    if not query or len(query.strip()) < 2:
        return pd.DataFrame()
    
    query = query.strip()
    
    # Create lowercase title column if it doesn't exist
    if 'title_lower' not in movies.columns:
        movies['title_lower'] = movies['title'].str.lower()
    
    # Apply search filters
    filtered_movies = movies.copy()
    if filters:
        filtered_movies = apply_search_filters(filtered_movies, filters)
    
    # 1. Exact matches (highest relevance)
    exact_matches = filtered_movies[filtered_movies['title_lower'] == query.lower()]
    
    # 2. Starts with matches (high relevance)
    starts_with = filtered_movies[filtered_movies['title_lower'].str.startswith(query.lower())]
    starts_with = starts_with[~starts_with['title'].isin(exact_matches['title'])]
    
    # 3. Contains matches (medium relevance)
    contains = filtered_movies[filtered_movies['title_lower'].str.contains(query.lower(), na=False)]
    contains = contains[~contains['title'].isin(pd.concat([exact_matches, starts_with])['title'])]
    
    # 4. Fuzzy matches if we have few results
    if len(exact_matches) + len(starts_with) + len(contains) < 10:
        from difflib import get_close_matches
        all_titles = filtered_movies['title'].tolist()
        fuzzy_matches = get_close_matches(query.lower(), [t.lower() for t in all_titles], n=10, cutoff=0.6)
        fuzzy_matches = filtered_movies[filtered_movies['title_lower'].isin(fuzzy_matches)]
        fuzzy_matches = fuzzy_matches[~fuzzy_matches['title'].isin(pd.concat([exact_matches, starts_with, contains])['title'])]
        
        # Combine all results
        final_results = pd.concat([exact_matches, starts_with, contains, fuzzy_matches], ignore_index=True)
    else:
        final_results = pd.concat([exact_matches, starts_with, contains], ignore_index=True)
    
    # Remove duplicates and limit results
    if not final_results.empty:
        final_results = final_results.drop_duplicates(subset=['title']).head(20)
    
    return final_results

def apply_search_filters(movies, filters):
    """Apply search filters to movies dataframe"""
    filtered = movies.copy()
    
    # Genre filter
    if filters.get('genre') and filters['genre'] != 'All':
        genre_filter = filtered['genres'].str.contains(filters['genre'], case=False, na=False)
        filtered = filtered[genre_filter]
    
    # Year filter
    if filters.get('year_from') and filters.get('year_to'):
        try:
            # Extract year from release_date if available
            if 'release_date' in filtered.columns:
                filtered['year'] = pd.to_datetime(filtered['release_date'], errors='coerce').dt.year
                year_filter = (filtered['year'] >= filters['year_from']) & (filtered['year'] <= filters['year_to'])
                filtered = filtered[year_filter]
        except:
            pass
    
    # Rating filter
    if filters.get('min_rating'):
        try:
            rating_filter = filtered['vote_average'] >= filters['min_rating']
            filtered = filtered[rating_filter]
        except:
            pass
    
    return filtered

def get_search_filters():
    """Get search filter options"""
    return {
        'genres': ['All', 'Action', 'Adventure', 'Animation', 'Comedy', 'Crime', 'Documentary', 
                  'Drama', 'Family', 'Fantasy', 'History', 'Horror', 'Music', 'Mystery', 
                  'Romance', 'Science Fiction', 'TV Movie', 'Thriller', 'War', 'Western'],
        'years': list(range(1900, 2025, 5)),
        'ratings': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    }

def debug_dataframe_columns(df, name="DataFrame"):
    """Debug helper to show dataframe columns"""
    st.expander(f"🔍 Debug: {name} Columns", expanded=False).write({
        "Columns": list(df.columns),
        "Shape": df.shape,
        "Sample Data": df.head(2).to_dict() if not df.empty else "No data"
    })

def handle_movie_feedback(movie_name, feedback_type):
    """Handle movie feedback (like/dislike) and update Firebase with better error handling"""
    try:
        # Validate inputs
        if not movie_name or not feedback_type:
            st.error("Invalid feedback data")
            return False
        
        if feedback_type not in ['like', 'dislike']:
            st.error("Invalid feedback type")
            return False
        
        # Update session state
        if feedback_type == 'like':
            if movie_name in st.session_state.disliked_movies:
                st.session_state.disliked_movies.remove(movie_name)
            if movie_name not in st.session_state.liked_movies:
                st.session_state.liked_movies.append(movie_name)
        else:  # dislike
            if movie_name in st.session_state.liked_movies:
                st.session_state.liked_movies.remove(movie_name)
            if movie_name not in st.session_state.disliked_movies:
                st.session_state.disliked_movies.append(movie_name)
        
        # Update feedback in session state
        st.session_state.movie_feedback[movie_name] = {
            'type': feedback_type,
            'timestamp': time.time()
        }
        
        # Update Firebase with retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                db.collection('users').document(st.session_state.uid).set({
                    'liked_movies': st.session_state.liked_movies,
                    'disliked_movies': st.session_state.disliked_movies,
                    'movie_feedback': st.session_state.movie_feedback,
                    'preferences_set': bool(st.session_state.liked_movies or st.session_state.disliked_movies),
                    'last_updated': time.time()
                }, merge=True)
                return True
            except Exception as e:
                if attempt == max_retries - 1:  # Last attempt
                    st.error(f"Failed to save feedback after {max_retries} attempts: {e}")
                    return False
                time.sleep(0.5)  # Wait before retry
        
        return True
    except Exception as e:
        st.error(f"Failed to save feedback: {e}")
        return False

def analyze_user_preferences(liked_movies, disliked_movies, movies):
    """Analyze user preferences and provide insights"""
    if not liked_movies and not disliked_movies:
        return None
    analysis = {
        'total_feedback': len(liked_movies) + len(disliked_movies),
        'liked_count': len(liked_movies),
        'disliked_count': len(disliked_movies),
        'preference_ratio': len(liked_movies) / max(1, len(liked_movies) + len(disliked_movies)),
        'genres': {},
        'years': [],
        'ratings': [],
        'insights': []
    }
    # Analyze liked movies
    for movie_title in liked_movies:
        movie_data = movies[movies['title'] == movie_title]
        if not movie_data.empty:
            movie = movie_data.iloc[0]
            # Genre analysis (now as list of strings)
            try:
                if isinstance(movie['genres'], list):
                    for genre_name in movie['genres']:
                        analysis['genres'][genre_name] = analysis['genres'].get(genre_name, 0) + 1
            except:
                pass
            # Year analysis
            if 'release_date' in movie and pd.notna(movie['release_date']):
                try:
                    year = pd.to_datetime(movie['release_date']).year
                    analysis['years'].append(year)
                except:
                    pass
            # Rating analysis
            if 'vote_average' in movie and pd.notna(movie['vote_average']):
                analysis['ratings'].append(movie['vote_average'])
    # Generate insights
    if analysis['genres']:
        top_genres = sorted(analysis['genres'].items(), key=lambda x: x[1], reverse=True)[:3]
        analysis['insights'].append(f"🎭 Your top genres: {', '.join([g[0] for g in top_genres])}")
    if analysis['years']:
        avg_year = sum(analysis['years']) / len(analysis['years'])
        analysis['insights'].append(f"📅 You prefer movies from around {int(avg_year)}")
    if analysis['ratings']:
        avg_rating = sum(analysis['ratings']) / len(analysis['ratings'])
        analysis['insights'].append(f"⭐ You tend to like movies rated {avg_rating:.1f}/10")
    if analysis['preference_ratio'] > 0.7:
        analysis['insights'].append("😊 You're quite selective with your likes!")
    elif analysis['preference_ratio'] < 0.3:
        analysis['insights'].append("🤔 You're very critical - that's good for quality recommendations!")
    return analysis

def get_user_recommendation_insights(liked_movies, disliked_movies, movies):
    """Get insights about recommendation quality and user behavior"""
    insights = []
    if not liked_movies:
        insights.append("🎯 **Getting Started**: Like a few movies to get personalized recommendations!")
        return insights
    # Feedback quantity insights
    total_feedback = len(liked_movies) + len(disliked_movies)
    if total_feedback < 5:
        insights.append("📈 **Learning Phase**: More feedback = better recommendations!")
    elif total_feedback < 10:
        insights.append("🎯 **Good Progress**: Your recommendations are getting smarter!")
    else:
        insights.append("🧠 **Expert Level**: The AI has learned your preferences well!")
    # Genre diversity insights
    if liked_movies:
        genres = set()
        for movie_title in liked_movies:
            movie_data = movies[movies['title'] == movie_title]
            if not movie_data.empty:
                try:
                    if isinstance(movie_data.iloc[0]['genres'], list):
                        genres.update(movie_data.iloc[0]['genres'])
                except:
                    pass
        if len(genres) < 3:
            insights.append("🎭 **Genre Explorer**: Try different genres for more diverse recommendations!")
        elif len(genres) < 6:
            insights.append("🎬 **Genre Enthusiast**: You enjoy a good variety of movies!")
        else:
            insights.append("🌟 **Genre Master**: You're open to all types of cinema!")
    # Recent activity insights
    if 'movie_feedback' in st.session_state:
        recent_feedback = st.session_state.movie_feedback
        if recent_feedback:
            recent_count = len([f for f in recent_feedback.values() 
                              if time.time() - f.get('timestamp', 0) < 3600])  # Last hour
            if recent_count > 5:
                insights.append("🔥 **Active User**: You're really exploring today!")
    return insights

def display_user_analytics(movies):
    """Display user analytics and insights in the sidebar"""
    liked = st.session_state.get('liked_movies', [])
    disliked = st.session_state.get('disliked_movies', [])
    
    if not liked and not disliked:
        return
    
    with st.sidebar.expander("📊 Your Movie Analytics", expanded=False):
        # Basic stats
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Liked", len(liked))
        with col2:
            st.metric("Disliked", len(disliked))
        
        # Preference analysis
        if movies is not None:
            analysis = analyze_user_preferences(liked, disliked, movies)
            if analysis:
                st.markdown("### 🎯 Your Preferences")
                
                # Genre breakdown
                if analysis['genres']:
                    st.markdown("**Top Genres:**")
                    top_genres = sorted(analysis['genres'].items(), key=lambda x: x[1], reverse=True)[:5]
                    for genre, count in top_genres:
                        st.write(f"• {genre}: {count} movies")
                
                # Insights
                if analysis['insights']:
                    st.markdown("### 💡 Insights")
                    for insight in analysis['insights']:
                        st.info(insight)
        
        # Recommendation insights
        insights = get_user_recommendation_insights(liked, disliked, movies)
        if insights:
            st.markdown("### 🧠 AI Insights")
            for insight in insights:
                st.success(insight)

def safe_load_data():
    """Safely load data with comprehensive error handling"""
    errors = []
    
    # Check file existence
    if not os.path.exists(MOVIE_PKL):
        errors.append(f"Movie data file not found: {MOVIE_PKL}")
    if not os.path.exists(SIMILARITY_PKL):
        errors.append(f"Similarity data file not found: {SIMILARITY_PKL}")
    
    if errors:
        return None, None, errors
    
    # Load movies
    try:
        movies = pickle.load(open(MOVIE_PKL, 'rb'))
        if not isinstance(movies, pd.DataFrame):
            errors.append("Invalid movie data format")
            movies = None
        elif movies.empty:
            errors.append("Movie data is empty")
            movies = None
    except Exception as e:
        errors.append(f"Error loading movie data: {e}")
        movies = None
    
    # Load similarity
    try:
        similarity = pickle.load(open(SIMILARITY_PKL, 'rb'))
        if similarity is None:
            errors.append("Similarity data is None")
    except Exception as e:
        errors.append(f"Error loading similarity data: {e}")
        similarity = None
    
    return movies, similarity, errors

def show_loading_state(message="Loading...", progress_bar=None):
    """Show loading state with progress bar"""
    if progress_bar is None:
        progress_bar = st.progress(0)
    
    status_text = st.empty()
    status_text.text(message)
    return progress_bar, status_text

def hide_loading_state(progress_bar, status_text):
    """Hide loading state"""
    if progress_bar:
        progress_bar.empty()
    if status_text:
        status_text.empty()

def validate_movie_data(movies):
    """Validate movie data structure and content"""
    if movies is None or movies.empty:
        return False, "Movie data is empty or None"
    
    required_columns = ['movie_id', 'title', 'genres']
    missing_columns = [col for col in required_columns if col not in movies.columns]
    
    if missing_columns:
        return False, f"Missing required columns: {', '.join(missing_columns)}"
    
    # Check for data quality issues
    if movies['title'].isna().sum() > len(movies) * 0.1:  # More than 10% missing titles
        return False, "Too many missing movie titles"
    
    if movies['movie_id'].isna().sum() > 0:
        return False, "Missing movie IDs found"
    
    return True, "Data validation passed"

def get_movie_details(movie_title, movies):
    """Get detailed information about a movie"""
    if movies is None or movies.empty:
        return None
    
    movie_data = movies[movies['title'] == movie_title]
    if movie_data.empty:
        return None
    
    movie = movie_data.iloc[0]
    details = {
        'title': movie['title'],
        'movie_id': movie['movie_id'],
        'genres': [],
        'release_date': None,
        'vote_average': None,
        'vote_count': None,
        'overview': None
    }
    
    # Parse genres
    try:
        if 'genres' in movie and pd.notna(movie['genres']):
            genres = ast.literal_eval(movie['genres']) if isinstance(movie['genres'], str) else movie['genres']
            details['genres'] = [g['name'] for g in genres if isinstance(g, dict) and 'name' in g]
    except:
        pass
    
    # Add other details
    for field in ['release_date', 'vote_average', 'vote_count', 'overview']:
        if field in movie and pd.notna(movie[field]):
            details[field] = movie[field]
    
    return details

def display_movie_details(movie_title, movies):
    """Display detailed movie information in an expander"""
    details = get_movie_details(movie_title, movies)
    if not details:
        return
    
    with st.expander(f"📖 Details: {movie_title}", expanded=False):
        col1, col2 = st.columns([2, 1])
        
        with col1:
            if details['overview']:
                st.write("**Overview:**")
                st.write(details['overview'])
            
            if details['genres']:
                st.write("**Genres:**")
                st.write(", ".join(details['genres']))
        
        with col2:
            if details['release_date']:
                st.write("**Release Date:**")
                st.write(details['release_date'])
            
            if details['vote_average']:
                st.write("**Rating:**")
                st.write(f"⭐ {details['vote_average']:.1f}/10")
            
            if details['vote_count']:
                st.write("**Votes:**")
                st.write(f"{details['vote_count']:,}")

def get_genre_matching_movies(search_movie, movies, limit=8):
    """Get movies with similar genres to the searched movie"""
    if movies is None or movies.empty or not search_movie:
        return pd.DataFrame()
    
    # Get genres of the searched movie
    search_movie_data = movies[movies['title'] == search_movie]
    if search_movie_data.empty:
        return pd.DataFrame()
    
    try:
        search_genres = ast.literal_eval(search_movie_data.iloc[0]['genres']) if isinstance(search_movie_data.iloc[0]['genres'], str) else search_movie_data.iloc[0]['genres']
        search_genre_names = [g['name'] for g in search_genres if isinstance(g, dict) and 'name' in g]
    except:
        return pd.DataFrame()
    
    if not search_genre_names:
        return pd.DataFrame()
    
    # Find movies with similar genres
    matching_movies = []
    for _, movie in movies.iterrows():
        if movie['title'] == search_movie:
            continue
            
        try:
            movie_genres = ast.literal_eval(movie['genres']) if isinstance(movie['genres'], str) else movie['genres']
            movie_genre_names = [g['name'] for g in movie_genres if isinstance(g, dict) and 'name' in g]
            
            # Calculate genre overlap
            overlap = len(set(search_genre_names) & set(movie_genre_names))
            if overlap > 0:
                matching_movies.append({
                    'title': movie['title'],
                    'movie_id': movie['movie_id'],
                    'genres': movie_genre_names,
                    'overlap': overlap,
                    'vote_average': movie.get('vote_average', 0),
                    'vote_count': movie.get('vote_count', 0)
                })
        except:
            continue
    
    # Sort by genre overlap and rating
    matching_movies.sort(key=lambda x: (x['overlap'], x['vote_average']), reverse=True)
    
    # Convert to DataFrame
    if matching_movies:
        result_df = pd.DataFrame(matching_movies[:limit])
        return result_df
    
    return pd.DataFrame()

def explain_hybrid_recommendation_model():
    """Explain the hybrid recommendation model to users"""
    st.markdown("""
    ## 🧠 How Our Hybrid AI Works
    
    Our recommendation system combines multiple AI techniques to find your perfect movies:
    
    ### 🎯 **Content-Based Filtering**
    - Analyzes movie features: plot, genres, cast, director, keywords
    - Finds movies similar to what you've liked before
    - Uses advanced text analysis and similarity algorithms
    
    ### 🎭 **Genre-Based Collaborative Filtering**
    - Learns your genre preferences from your likes/dislikes
    - Boosts movies with genres you enjoy
    - Considers genre combinations and mood matching
    
    ### 😊 **Mood-Based Analysis**
    - Groups genres by mood (Action, Comedy, Drama, Sci-Fi, Horror)
    - Matches your preferred movie moods
    - Suggests movies that fit your emotional preferences
    
    ### ⭐ **Quality & Popularity Balance**
    - Considers both ratings and popularity
    - Balances critically acclaimed movies with crowd favorites
    - Ensures recommendations are both good and accessible
    
    ### 🕒 **Recency & Diversity**
    - Slightly favors newer movies (2010+)
    - Prevents too-similar recommendations
    - Ensures variety in your suggestions
    
    ### 💡 **Smart Learning**
    - Weights recent feedback more heavily
    - Learns from both likes AND dislikes
    - Continuously improves as you rate more movies
    """)

def get_recommendation_breakdown(liked_movies, disliked_movies, movies):
    """Show users a breakdown of what the AI learned about their preferences"""
    if not liked_movies:
        return None
    breakdown = {
        'total_feedback': len(liked_movies) + len(disliked_movies),
        'liked_count': len(liked_movies),
        'disliked_count': len(disliked_movies),
        'top_genres': [],
        'mood_preferences': [],
        'quality_preference': 'Unknown',
        'recency_preference': 'Unknown'
    }
    # Analyze liked movies
    all_genres = []
    all_years = []
    all_ratings = []
    for movie_title in liked_movies:
        movie_data = movies[movies['title'] == movie_title]
        if not movie_data.empty:
            movie = movie_data.iloc[0]
            # Genres (now as list of strings)
            try:
                if isinstance(movie['genres'], list):
                    all_genres.extend(movie['genres'])
            except:
                pass
            # Years
            if 'release_date' in movie and pd.notna(movie['release_date']):
                try:
                    year = pd.to_datetime(movie['release_date']).year
                    all_years.append(year)
                except:
                    pass
            # Ratings
            if 'vote_average' in movie and pd.notna(movie['vote_average']):
                all_ratings.append(movie['vote_average'])
    # Calculate preferences
    if all_genres:
        genre_counter = Counter(all_genres)
        breakdown['top_genres'] = [g for g, _ in genre_counter.most_common(3)]
    if all_years:
        avg_year = sum(all_years) / len(all_years)
        if avg_year >= 2010:
            breakdown['recency_preference'] = 'Recent (2010+)'
        elif avg_year >= 2000:
            breakdown['recency_preference'] = 'Modern (2000-2009)'
        else:
            breakdown['recency_preference'] = 'Classic (Pre-2000)'
    if all_ratings:
        avg_rating = sum(all_ratings) / len(all_ratings)
        if avg_rating >= 7.5:
            breakdown['quality_preference'] = 'High Quality (7.5+)'
        elif avg_rating >= 6.5:
            breakdown['quality_preference'] = 'Good Quality (6.5-7.4)'
        else:
            breakdown['quality_preference'] = 'Mixed Quality'
    # Mood analysis
    mood_genres = {
        'Action': ['Action', 'Adventure', 'War', 'Thriller'],
        'Comedy': ['Comedy', 'Romance', 'Family'],
        'Drama': ['Drama', 'History', 'Biography'],
        'Sci-Fi': ['Science Fiction', 'Fantasy', 'Animation'],
        'Horror': ['Horror', 'Mystery', 'Crime']
    }
    user_moods = set()
    for genre in all_genres:
        for mood, mood_genres_list in mood_genres.items():
            if genre in mood_genres_list:
                user_moods.add(mood)
    breakdown['mood_preferences'] = list(user_moods)
    return breakdown

def display_ai_insights(breakdown):
    """Display AI insights about user preferences"""
    if not breakdown:
        return
    
    st.markdown("### 🤖 AI Insights About Your Taste")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Total Movies Rated", breakdown['total_feedback'])
        st.metric("Liked Movies", breakdown['liked_count'])
        
        if breakdown['top_genres']:
            st.write("**🎭 Top Genres:**")
            for genre in breakdown['top_genres']:
                st.write(f"• {genre}")
    
    with col2:
        st.metric("Quality Preference", breakdown['quality_preference'])
        st.metric("Era Preference", breakdown['recency_preference'])
        
        if breakdown['mood_preferences']:
            st.write("**😊 Mood Preferences:**")
            for mood in breakdown['mood_preferences']:
                st.write(f"• {mood}")
    
    # Confidence level
    if breakdown['total_feedback'] >= 10:
        st.success("🎯 **High Confidence**: The AI has learned your preferences well!")
    elif breakdown['total_feedback'] >= 5:
        st.info("🙂 **Good Confidence**: Keep rating to improve recommendations!")
    else:
        st.warning("📈 **Learning Phase**: Rate more movies for better suggestions!")

def main():
    st.set_page_config(
        page_title="🎬 Smart Movie Recommender", 
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Initialize session state - IMPORTANT: Initialize all keys at once (MOVE TO TOP)
    if 'logged_in' not in st.session_state:
        st.session_state.update({
            'logged_in': False,
            'username': '',
            'user_name': '',  # Add user's actual name
            'uid': '',
            'liked_movies': [],
            'disliked_movies': [],  # Add disliked movies tracking
            'movie_feedback': {},   # Add detailed feedback tracking
            'preferences_set': False,
            'current_tab': 'Recommendations',  # Set default tab
            'first_login': True,
            'random_movies': pd.DataFrame(),
            'search_query': '',
            'search_results': pd.DataFrame(),
            'show_suggestions': False,
            'selected_suggestion': '',
            'login_attempted': False,
            'signup_attempted': False
        })
    
    debug_info = {}
    # Load custom CSS
    load_css()
    
    if DEBUG:
        if st.sidebar.button("🔍 Debug Info"):
          st.sidebar.write("Session State Debug:")
          debug_info = {
            'logged_in': st.session_state.get('logged_in', 'Not set'),
            'username': st.session_state.get('username', 'Not set'),
            'user_name': st.session_state.get('user_name', 'Not set'),
            'login_attempted': st.session_state.get('login_attempted', 'Not set'),
            'signup_attempted': st.session_state.get('signup_attempted', 'Not set'),
            'models_loaded': st.session_state.get('models_loaded', 'Not set'),
        }
        st.sidebar.json(debug_info)
          
        if st.sidebar.button("🔄 Reset Session"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    # Check if Firebase is initialized
    # if not firebase_admin._apps:
    #     st.error("🚨 Firebase not initialized. Please check your configuration.")
    #     return

    # Authentication Section
    if not st.session_state.logged_in:
        st.markdown("""
        <div class="movie-header">
            <h1>🎬 Smart Movie Recommender</h1>
            <p>Discover your next favorite movie with AI-powered recommendations</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            login_tab, signup_tab = st.tabs(["🔐 Login", "✨ Sign Up"])

            with login_tab:
                with st.container():
                    st.markdown("### Welcome Back!")
                    
                    # Use a form without clear_on_submit to maintain values
                    with st.form("login_form", clear_on_submit=False):
                        email = st.text_input("📧 Email", placeholder="Enter your email", key="login_email")
                        password = st.text_input("🔒 Password", type="password", placeholder="Enter your password", key="login_password")
                        
                        col_a, col_b, col_c = st.columns([1, 2, 1])
                        with col_b:
                            login_btn = st.form_submit_button("🚀 Login", use_container_width=True)
                        
                        # Handle login outside of form but inside the tab
                        if login_btn and email and password:
                            if not st.session_state.get('login_attempted', False):
                                st.session_state.login_attempted = True
                                
                                # Show progress
                                progress_bar = st.progress(0)
                                status_text = st.empty()
                                
                                try:
                                    status_text.text("🔐 Authenticating...")
                                    progress_bar.progress(25)
                                    
                                    res = sign_in(email, password)
                                    progress_bar.progress(50)
                                    
                                    if res and res.get('status') == 'success':
                                        status_text.text("✅ Login successful! Loading your profile...")
                                        progress_bar.progress(75)
                                        
                                        # Set session state
                                        st.session_state.logged_in = True
                                        st.session_state.username = email
                                        st.session_state.uid = res.get('uid')  # Store UID
                                        
                                        # Load user data using UID
                                        try:
                                            user_data = db.collection('users').document(st.session_state.uid).get().to_dict() or {}
                                            st.session_state.liked_movies = user_data.get('liked_movies', [])
                                            st.session_state.disliked_movies = user_data.get('disliked_movies', [])
                                            st.session_state.movie_feedback = user_data.get('movie_feedback', {})
                                            st.session_state.user_name = user_data.get('display_name', '')  # Load actual name
                                            st.session_state.preferences_set = bool(st.session_state.liked_movies or st.session_state.disliked_movies)
                                            st.session_state.first_login = False
                                        except Exception as e:
                                            st.warning("Could not load user preferences")
                                        
                                        progress_bar.progress(100)
                                        status_text.text("🎉 Welcome back! Redirecting...")
                                        
                                        # Clear the attempt flag and rerun
                                        st.session_state.login_attempted = False
                                        time.sleep(1)
                                        st.rerun()
                                        
                                    else:
                                        progress_bar.empty()
                                        status_text.empty()
                                        st.session_state.login_attempted = False
                                        st.error(f"❌ {res.get('message', 'Login failed') if res else 'Login failed'}")
                                        
                                except Exception as e:
                                    progress_bar.empty()
                                    status_text.empty()
                                    st.session_state.login_attempted = False
                                    st.error(f"❌ Login error: {str(e)}")
                        
                        elif login_btn:
                            st.warning("Please fill in all fields")

            with signup_tab:
                with st.container():
                    st.markdown("### Join the Community!")
                    
                    with st.form("signup_form", clear_on_submit=False):
                        name = st.text_input("👤 Full Name", placeholder="Enter your full name", key="signup_name")
                        email = st.text_input("📧 Email", placeholder="Enter your email", key="signup_email")
                        password = st.text_input("🔒 Password", type="password", placeholder="Create a password", key="signup_password")
                        
                        col_a, col_b, col_c = st.columns([1, 2, 1])
                        with col_b:
                            signup_btn = st.form_submit_button("🎬 Join Now", use_container_width=True)
                        
                        # Handle signup outside of form but inside the tab
                        if signup_btn and name and email and password:
                            if not st.session_state.get('signup_attempted', False):
                                st.session_state.signup_attempted = True
                                
                                # Show progress
                                progress_bar = st.progress(0)
                                status_text = st.empty()
                                
                                try:
                                    status_text.text("🎬 Creating your account...")
                                    progress_bar.progress(25)
                                    
                                    res = sign_up("", email, password, name)
                                    progress_bar.progress(50)
                                    
                                    if res and res.get('status') == 'success':
                                        status_text.text("✅ Account created! Setting up your profile...")
                                        progress_bar.progress(75)
                                        
                                        # Set session state
                                        st.session_state.logged_in = True
                                        st.session_state.username = email
                                        st.session_state.user_name = name  # Store actual name
                                        st.session_state.uid = res.get('uid')  # Store UID
                                        st.session_state.liked_movies = []
                                        st.session_state.disliked_movies = []
                                        st.session_state.movie_feedback = {}
                                        st.session_state.preferences_set = False
                                        st.session_state.first_login = True
                                        
                                        # Save user data to Firestore including display name
                                        try:
                                            db.collection('users').document(st.session_state.uid).set({
                                                'email': email,
                                                'display_name': name,
                                                'liked_movies': [],
                                                'disliked_movies': [],
                                                'movie_feedback': {},
                                                'preferences_set': False,
                                                'created_at': time.time()
                                            }, merge=True)
                                        except Exception as e:
                                            if DEBUG:
                                                print(f"[DEBUG] Error saving user data to Firestore: {e}")
                                        
                                        progress_bar.progress(100)
                                        status_text.text("🎉 Welcome to the community! Redirecting...")
                                        
                                        # Clear the attempt flag and rerun
                                        st.session_state.signup_attempted = False
                                        time.sleep(1)
                                        st.rerun()
                                        
                                    else:
                                        progress_bar.empty()
                                        status_text.empty()
                                        st.session_state.signup_attempted = False
                                        st.error(f"❌ {res.get('message', 'Signup failed') if res else 'Signup failed'}")
                                        
                                except Exception as e:
                                    progress_bar.empty()
                                    status_text.empty()
                                    st.session_state.signup_attempted = False
                                    st.error(f"❌ Signup error: {str(e)}")
                        
                        elif signup_btn:
                            st.warning("Please fill in all fields")
        
        # Stop execution here if not logged in
        return

    # Initialize model loading state
    if 'models_loaded' not in st.session_state:
        st.session_state.models_loaded = False
        st.session_state.movies = None
        st.session_state.similarity = None

    # Load model files with caching
    @st.cache_data(ttl=3600)  # Cache for 1 hour
    def load_movies():
        """Load and validate movie data"""
        try:
            if not os.path.exists(MOVIE_PKL):
                st.error(f"❌ Movie data file not found at {MOVIE_PKL}")
                return None
                
            movies = pickle.load(open(MOVIE_PKL, 'rb'))
            
            # Validate that we got a DataFrame
            if not isinstance(movies, pd.DataFrame):
                st.error("❌ Invalid movie data format. Expected DataFrame.")
                return None
                
            # Ensure required columns exist
            required_columns = ['movie_id', 'title', 'genres']
            missing_columns = [col for col in required_columns if col not in movies.columns]
            
            if missing_columns:
                st.error(f"❌ Missing required columns in movie data: {', '.join(missing_columns)}")
                return None
                
            # Validate data types
            if not pd.api.types.is_numeric_dtype(movies['movie_id']):
                st.error("❌ 'movie_id' column must be numeric")
                return None
                
            # Convert genres to string if it's not already
            if 'genres' in movies.columns:
                movies['genres'] = movies['genres'].apply(lambda x: str(x) if not isinstance(x, str) else x)
            
            # Add title_lower column for searching
            movies['title_lower'] = movies['title'].str.lower()
            
            return movies
            
        except Exception as e:
            st.error(f"❌ Error loading movie data: {str(e)}")
            return None

    @st.cache_data(ttl=3600)  # Cache for 1 hour
    def load_similarity():
        try:
            return pickle.load(open(SIMILARITY_PKL, 'rb'))
        except Exception as e:
            st.error(f"Error loading similarity data: {e}")
            return None

    # Check if model files exist
    if not os.path.exists(MOVIE_PKL) or not os.path.exists(SIMILARITY_PKL):
        st.error("🚨 Model files not found. Please build the recommendation model first.")
        return

    # Load models only when needed
    try:
        if not st.session_state.models_loaded:
            with st.spinner("🚀 Loading movie database... This may take a moment."):
                movies = load_movies()
                similarity = load_similarity()
                
                # Validate loaded data
                if movies is None or similarity is None:
                    st.error("❌ Failed to load required data. Please check if the model files exist and are valid.")
                    return
                
                st.session_state.movies = movies
                st.session_state.similarity = similarity
                st.session_state.models_loaded = True
        else:
            movies = st.session_state.movies
            similarity = st.session_state.similarity
            
            # Validate session state data
            if movies is None or similarity is None:
                st.error("❌ Session data is invalid. Please refresh the page.")
                # Reset session state
                st.session_state.models_loaded = False
                st.session_state.movies = None
                st.session_state.similarity = None
                st.rerun()
                return
            
        with st.sidebar:
            if DEBUG and st.checkbox("🔧 Debug Mode"):
                debug_dataframe_columns(movies, "Movies")
                
    except Exception as e:
        st.error(f"Error loading model files: {e}")
        return

    # Main App Header
    st.markdown(f"""
    <div class="movie-header">
        <h1>🎬 Welcome back, {st.session_state.user_name if st.session_state.user_name else st.session_state.username.split('@')[0].title() if st.session_state.username and '@' in st.session_state.username else 'User'}!</h1>
        <p>You've liked {len(st.session_state.liked_movies)} movies so far</p>
    </div>
    """, unsafe_allow_html=True)

    # Logout button in sidebar
    with st.sidebar:
        st.markdown("### Account")
        if st.button("🚪 Logout", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
        
        st.markdown("### Quick Stats")
        st.metric("Liked Movies", len(st.session_state.liked_movies))
        st.metric("Disliked Movies", len(st.session_state.disliked_movies))
        if movies is not None:  # Add check before accessing movies
            st.metric("Available Movies", len(movies))
        
        # Display user analytics
        display_user_analytics(movies)

    # Main Tabs
    tab_names = ["🔍 Discover", "🎯 Recommendations", "❤️ My Movies"]
    tabs = st.tabs(tab_names)
    
    # Store the current tab in session state
    if 'current_tab' not in st.session_state:
        st.session_state.current_tab = 1  # Default to Recommendations tab

    # Discover Tab
    with tabs[0]:
        st.session_state.current_tab = 0
        st.markdown("### 🔍 Discover Amazing Movies")
        
        # Enhanced Search Section
        search_container = st.container()
        with search_container:
            # Search header with better styling
            st.markdown("""
            <div style="background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); 
                        padding: 1rem; border-radius: 10px; margin-bottom: 1rem;">
                <h4 style="color: white; margin: 0;">🎬 Find Your Next Favorite Movie</h4>
                <p style="color: rgba(255,255,255,0.8); margin: 0.5rem 0 0 0;">Search by title or explore popular movies</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Auto-matching searchable dropdown
            col1, col2 = st.columns([4, 1])
            with col1:
                # Get all movie titles for dropdown
                all_movies = movies['title'].tolist() if movies is not None else []
                
                # Create searchable dropdown
                selected_movie = st.selectbox(
                    "🔎 Search and select a movie...",
                    options=[""] + all_movies,
                    index=0,
                    help="Type to search through all movies",
                    key="movie_search_dropdown"
                )
                
                # Update search query when movie is selected
                if selected_movie and selected_movie != st.session_state.get('search_query', ''):
                    st.session_state.search_query = selected_movie
                    st.session_state.search_results = search_movies_improved(selected_movie, movies)
                    st.rerun()
            
            with col2:
                # Aligned clear button
                if st.button("🗑️ Clear", use_container_width=True, help="Clear search results"):
                    st.session_state.search_query = ""
                    st.session_state.search_results = pd.DataFrame()
                    st.session_state.show_suggestions = False
                    st.rerun()

            # Process search query
            search_query = st.session_state.get('search_query', '')
            if search_query and search_query.strip():
                search_results = st.session_state.get('search_results', pd.DataFrame())
            else:
                search_results = pd.DataFrame()
                st.session_state.search_query = ""
                st.session_state.search_results = pd.DataFrame()

            # Always use grid, even for one result
            if not search_results.empty:
                result_count = len(search_results)
                st.markdown(f"""
                <div style="background: rgba(0,255,0,0.1); padding: 1rem; border-radius: 8px; margin: 1rem 0;">
                    <h5 style="color: white; margin: 0;">🎯 Found {result_count} movie{'s' if result_count != 1 else ''} matching '{search_query}'</h5>
                </div>
                """, unsafe_allow_html=True)

                posters = [fetch_poster(mid) for mid in search_results['movie_id']]
                # Always use columns=4 for grid, even if 1 result
                display_movies_grid(
                    search_results['title'].tolist(),
                    posters,
                    movies,
                    key_prefix="search",
                    columns=4,  # Always grid
                    show_ratings=True
                )

                # Show genre matching movies if we have a single search result
                if result_count == 1:
                    st.markdown("---")
                    st.markdown(f"""
                    <div style="background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
                                padding: 1rem; border-radius: 10px; margin: 1rem 0;">
                        <h4 style="color: white; margin: 0;">🎭 Similar Movies You Might Like</h4>
                        <p style="color: rgba(255,255,255,0.8); margin: 0.5rem 0 0 0;">Movies with similar genres to '{search_query}'</p>
                    </div>
                    """, unsafe_allow_html=True)

                    genre_matches = get_genre_matching_movies(search_query, movies, limit=8)
                    if not genre_matches.empty:
                        genre_posters = [fetch_poster(mid) for mid in genre_matches['movie_id']]
                        display_movies_grid(
                            genre_matches['title'].tolist(),
                            genre_posters,
                            movies,
                            key_prefix="genre_match",
                            columns=4,
                            show_ratings=True
                        )
                    else:
                        st.info("No similar movies found based on genres.")

        # Random Movies Section
        if not search_query or search_results.empty:
            st.markdown("---")
            
            # Enhanced Random Movies Header
            st.markdown("""
            <div style="background: linear-gradient(90deg, #ff6b6b 0%, #ee5a24 100%); 
                        padding: 1rem; border-radius: 10px; margin: 1rem 0;">
                <h4 style="color: white; margin: 0;">🎲 Discover Random Movies</h4>
                <p style="color: rgba(255,255,255,0.8); margin: 0.5rem 0 0 0;">Explore new movies you might not have seen before</p>
            </div>
            """, unsafe_allow_html=True)
            
            random_header_container = st.container()
            with random_header_container:
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.markdown("### 🎲 Random Movie Discoveries")
                with col2:
                    if st.button("🎲 Get New Random Movies", use_container_width=True, help="Generate new random movies"):
                        with st.spinner("🔄 Generating random movies..."):
                            st.session_state.random_movies = movies.sample(8)
                        st.rerun()

            # Initialize random movies if not exists or empty
            if 'random_movies' not in st.session_state or st.session_state.random_movies.empty:
                st.session_state.random_movies = movies.sample(8)

            # Display random movies with better styling
            if isinstance(st.session_state.random_movies, pd.DataFrame) and not st.session_state.random_movies.empty:
                try:
                    # Add a subtle background for the random movies section
                    st.markdown("""
                    <div style="background: rgba(255,255,255,0.05); padding: 1rem; border-radius: 8px; margin: 1rem 0;">
                    </div>
                    """, unsafe_allow_html=True)
                    
                    posters = [fetch_poster(mid) for mid in st.session_state.random_movies['movie_id']]
                    display_movies_grid(
                        st.session_state.random_movies['title'].tolist(), 
                        posters, 
                        movies,
                        key_prefix="random",
                        columns=4,
                        show_ratings=True
                    )
                    
                    # Add a tip about random movies
                    st.markdown("""
                    <div style="background: rgba(255,255,255,0.1); padding: 0.5rem; border-radius: 5px; margin-top: 1rem;">
                        <p style="color: rgba(255,255,255,0.8); margin: 0; font-size: 0.9rem;">
                            💡 <strong>Tip:</strong> Like or dislike these movies to improve your future recommendations!
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                except Exception as e:
                    st.error(f"Error displaying random movies: {e}")
                    st.session_state.random_movies = movies.sample(8)
                    st.rerun()

        # Add a tip/banner to encourage feedback
        st.markdown("""
        <div style='background: #222; color: #FFD700; border-radius: 8px; padding: 0.7em 1em; margin-bottom: 1em; text-align: center; font-size: 1.05em;'>
            💡 <strong>Tip:</strong> Like or dislike movies to improve your recommendations!
        </div>
        """, unsafe_allow_html=True)

    # Recommendations Tab
    with tabs[1]:
        st.session_state.current_tab = 1
        st.markdown("### 🎯 Your Personal Recommendations")
        
        liked = st.session_state.get('liked_movies', [])
        disliked = st.session_state.get('disliked_movies', [])
        feedback_count = len(liked) + len(disliked)

        # Show AI insights about user preferences
        if liked or disliked:
            breakdown = get_recommendation_breakdown(liked, disliked, movies)
            if breakdown:
                with st.expander("🤖 AI Insights About Your Taste", expanded=False):
                    display_ai_insights(breakdown)
        
        # Add option to learn about the hybrid model
        with st.expander("🧠 How Our Hybrid AI Works", expanded=False):
            explain_hybrid_recommendation_model()

        # === Show Feedback Summary inside EXISTING Sidebar ===
        with st.sidebar.expander("🧠 Recommendation Feedback Summary", expanded=True):
            st.write(f"👍 **Liked Movies**: {len(liked)}")
            st.write(f"👎 **Disliked Movies**: {len(disliked)}")
            st.write(f"📊 **Total Feedback**: {feedback_count}")
            if feedback_count >= 5:
                st.success("🎯 Excellent Match Confidence")
            elif feedback_count >= 3:
                st.info("🙂 Good Confidence — Like a few more for better matches!")
            else:
                st.warning("📈 Still Learning — Keep rating to improve recommendations!")

        # === CASE: No feedback yet ===
        if not liked and not disliked:
            st.info("💡 **Get Started:** Like or dislike some movies to get personalized recommendations!")
            
            st.markdown("#### 🌟 Popular Movies to Get You Started")
            try:
                popular_movies = get_popular_movies(movies, 8)
                posters = [fetch_poster(mid) for mid in popular_movies['movie_id']]
                display_movies_grid(
                    popular_movies['title'].tolist(), 
                    posters, 
                    movies,
                    key_prefix="popular",
                    columns=4
                )
            except Exception as e:
                st.error("🚫 Could not load popular movies.")
                st.exception(e)
        else:
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                recommend_btn = st.button("🎯 Get My Recommendations", key="get_recommendations_btn", use_container_width=True)
            with col2:
                st.metric("👍 Likes", len(liked))
                st.metric("👎 Dislikes", len(disliked))
            with col3:
                quality = "Excellent" if feedback_count >= 5 else "Good" if feedback_count >= 3 else "Basic"
                st.metric("🔍 Quality", quality)

            if recommend_btn or st.session_state.get("show_recommendations", False):
                st.session_state.show_recommendations = True
                st.session_state.current_tab = 1  # Force stay on recommendations tab
                
                with st.spinner("🤖 Analyzing your preferences and finding perfect matches..."):
                    try:
                        # Debug information
                        if DEBUG:
                            st.write("Debug Info:")
                            st.write(f"Liked Movies: {len(liked)}")
                            st.write(f"Disliked Movies: {len(disliked)}")
                            st.write(f"Movies DataFrame Shape: {movies.shape}")
                            st.write(f"Similarity Matrix Shape: {similarity.shape if similarity is not None else 'None'}")
                            st.write(f"Movies Columns: {movies.columns.tolist()}")

                        names, posters, sources = get_ultimate_recommendations(
                            liked_movies=liked,
                            disliked_movies=disliked,
                            movies=movies,
                            similarity=similarity,
                            top_n=10
                        )
                    except Exception as e:
                        st.error("🚫 Recommendation engine failed.")
                        st.exception(e)
                        names, posters, sources = [], [], []

                if names:
                    with st.expander("🧠 How we chose these for you", expanded=True):
                        st.markdown(f"""
                        - **Feedback Used:** {feedback_count} entries
                        - **Genre Boosting:** Based on most liked genres
                        - **Genre Filtering:** Excludes disliked genres
                        - **Model Type:** Hybrid (Content + Genre Feedback)
                        """)
                        hybrid_count = sum("Hybrid" in src for src in sources)
                        st.info(f"🔄 **{hybrid_count} Hybrid Matches** blending your taste and genre interests")
                    
                    st.success("🎉 Here are your personalized recommendations!")
                    
                    # Brief explanation of hybrid benefits
                    st.info("""
                    🧠 **Powered by Hybrid AI**: These recommendations combine content analysis, genre preferences, 
                    mood matching, and quality filtering to find movies you'll love!
                    """)
                    
                    display_movies_grid(
                        names, 
                        posters, 
                        movies,
                        key_prefix="recommend", 
                        allow_like=True, 
                        columns=4,
                        sources=sources,
                        show_explanation=True
                    )
                    
                    st.markdown("---")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.info("💡 **Tip**: Like or dislike more movies to improve accuracy!")
                    with col2:
                        st.info("🎯 **Pro Tip**: The smarter the feedback, the smarter the match!")
                else:
                    st.warning("🤔 No strong matches found. Try liking or disliking more movies.")
                    
                    st.markdown("#### 🎲 Popular fallback movies you might enjoy:")
                    try:
                        fallback_movies = get_popular_movies(movies, 4)
                        fallback_posters = [fetch_poster(mid) for mid in fallback_movies['movie_id']]
                        display_movies_grid(
                            fallback_movies['title'].tolist(),
                            fallback_posters,
                            movies,
                            key_prefix="fallback",
                            columns=4
                        )
                    except Exception as e:
                        st.error("⚠️ Failed to load fallback recommendations.")
                        st.exception(e)

        # Add a tip/banner to encourage feedback
        st.markdown("""
        <div style='background: #222; color: #FFD700; border-radius: 8px; padding: 0.7em 1em; margin-bottom: 1em; text-align: center; font-size: 1.05em;'>
            💡 <strong>Tip:</strong> The more feedback you give, the smarter your recommendations get!
        </div>
        """, unsafe_allow_html=True)

    # My Movies Tab
    with tabs[2]:
        st.session_state.current_tab = 2
        st.markdown("### ❤️ Your Movie Collection")
        
        liked = st.session_state.liked_movies
        if liked:
            col1, col2 = st.columns([2, 1])
            with col1:
                st.markdown(f"**You have {len(liked)} liked movies**")
            with col2:
                if st.button("🧹 Clear All Likes", use_container_width=True):
                    st.session_state.liked_movies = []
                    st.session_state.disliked_movies = []
                    st.session_state.movie_feedback = {}
                    st.session_state.preferences_set = False
                    try:
                        db.collection('users').document(st.session_state.uid).set({
                            'liked_movies': [],
                            'disliked_movies': [],
                            'movie_feedback': {},
                            'preferences_set': False,
                            'email': st.session_state.username
                        }, merge=True)
                        st.success("🧹 All likes cleared!")
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to clear likes: {e}")

            # Display liked movies
            posters = []
            for movie in liked:
                try:
                    movie_data = movies[movies['title'] == movie]
                    if not movie_data.empty:
                        movie_id = movie_data.iloc[0]['movie_id']
                        poster = fetch_poster(movie_id)
                        posters.append(poster)
                    else:
                        posters.append("https://via.placeholder.com/500x750?text=No+Image")
                except:
                    posters.append("https://via.placeholder.com/500x750?text=No+Image")
            
            display_movies_grid(liked, posters, movies, key_prefix="liked", columns=4)
        else:
            st.info("💔 Your movie collection is empty!")
            st.markdown("Go to the **Discover** tab to start building your collection by liking movies you enjoy.")
            
            st.markdown("#### 🔥 Trending Movies")
            trending = movies.sample(4)
            posters = [fetch_poster(mid) for mid in trending['movie_id']]
            display_movies_grid(
                trending['title'].tolist(), 
                posters, 
                movies,
                key_prefix="trending_suggestions",
                columns=4
            )

    # st.session_state.debug_mode = True

if __name__ == '__main__':
    main()