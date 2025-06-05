import os
import pickle
import pandas as pd
import streamlit as st
import requests
import ast
import random
import difflib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from auth import sign_in, sign_up, get_name
import firebase_admin
from firebase_admin import credentials, firestore
import time
from css import load_css  # Import custom CSS for styling

# Firebase Init
if not firebase_admin._apps:
    cred = credentials.Certificate("firebase.json")
    firebase_admin.initialize_app(cred)
db = firestore.client()

# Paths
DATA_DIR = "D:/spring 2025S/project/Dataset"
MOVIES_PATH = os.path.join(DATA_DIR, "tmdb_5000_movies.csv")
CREDITS_PATH = os.path.join(DATA_DIR, "tmdb_5000_credits.csv")
MODEL_DIR = "model"
MOVIE_PKL = os.path.join(MODEL_DIR, "movie_list.pkl")
SIMILARITY_PKL = os.path.join(MODEL_DIR, "similarity.pkl")

# --- Helper Functions ---
def fetch_poster(movie_id):
    api_key = st.secrets.get("tmdb_api_key", "")
    if not api_key:
        return "https://via.placeholder.com/500x750?text=No+API+Key"
    try:
        url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}&language=en-US"
        response = requests.get(url, timeout=10)
        data = response.json()
        return "https://image.tmdb.org/t/p/w500/" + data.get('poster_path', '') if data.get('poster_path') else "https://via.placeholder.com/500x750?text=No+Image"
    except:
        return "https://via.placeholder.com/500x750?text=Error"

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

def recommend_based_on_preferences(liked_movies, movies, similarity, top_n=8):
    """Enhanced recommendation system with better user preference matching"""
    indices = [movies[movies['title'] == m].index[0] for m in liked_movies if not movies[movies['title'] == m].empty]
    if not indices:
        return [], []
    
    # Weighted similarity scoring based on user preference strength
    sim_scores = {}
    total_weight = len(indices)
    
    for idx in indices:
        # Give more weight to recent likes (last in the list)
        weight = (indices.index(idx) + 1) / total_weight
        
        for i, score in enumerate(similarity[idx]):
            if i not in indices:  # Don't recommend already liked movies
                sim_scores[i] = sim_scores.get(i, 0) + (score * weight)
    
    # Filter out low-quality recommendations (similarity < 0.1)
    filtered_scores = {i: score for i, score in sim_scores.items() if score > 0.1}
    
    if not filtered_scores:
        # Fallback to unfiltered if no good matches
        filtered_scores = sim_scores
    
    # Sort and get top recommendations
    sorted_movies = sorted(filtered_scores.items(), key=lambda x: x[1], reverse=True)[:top_n]
    
    names = [movies.iloc[i]['title'] for i, _ in sorted_movies]
    posters = [fetch_poster(movies.iloc[i]['movie_id']) for i, _ in sorted_movies]
    scores = [score for _, score in sorted_movies]  # Keep scores for debugging
    
    return names, posters, scores

def get_genre_based_recommendations(liked_movies, movies, n=8):
    """Get recommendations based on genre preferences"""
    if not liked_movies:
        return [], []
    
    # Extract genres from liked movies (if genre column exists)
    if 'genres' in movies.columns:
        liked_genres = []
        for movie in liked_movies:
            movie_data = movies[movies['title'] == movie]
            if not movie_data.empty and pd.notna(movie_data.iloc[0]['genres']):
                try:
                    # Parse genres (assuming it's stored as string representation of list)
                    genres = ast.literal_eval(movie_data.iloc[0]['genres'])
                    if isinstance(genres, list):
                        liked_genres.extend([g['name'] for g in genres if isinstance(g, dict) and 'name' in g])
                except:
                    pass
        
        if liked_genres:
            # Count genre preferences
            from collections import Counter
            genre_counts = Counter(liked_genres)
            top_genres = [genre for genre, _ in genre_counts.most_common(3)]
            
            # Find movies with similar genres
            recommendations = []
            for _, movie in movies.iterrows():
                if movie['title'] not in liked_movies:
                    try:
                        movie_genres = ast.literal_eval(movie['genres'])
                        if isinstance(movie_genres, list):
                            movie_genre_names = [g['name'] for g in movie_genres if isinstance(g, dict) and 'name' in g]
                            # Check if movie has any of user's preferred genres
                            if any(genre in movie_genre_names for genre in top_genres):
                                recommendations.append(movie)
                    except:
                        continue
            
            if recommendations:
                # Convert to DataFrame and sample
                rec_df = pd.DataFrame(recommendations).sample(min(n, len(recommendations)))
                names = rec_df['title'].tolist()
                posters = [fetch_poster(mid) for mid in rec_df['movie_id']]
                return names, posters
    
    return [], []

def get_smart_recommendations(liked_movies, movies, similarity, strategy='mixed'):
    """Get recommendations using multiple strategies"""
    all_recommendations = {'names': [], 'posters': [], 'sources': []}
    
    if strategy == 'mixed' and len(liked_movies) >= 2:
        # Content-based recommendations (primary)
        content_names, content_posters, _ = recommend_based_on_preferences(liked_movies, movies, similarity, top_n=6)
        all_recommendations['names'].extend(content_names)
        all_recommendations['posters'].extend(content_posters)
        all_recommendations['sources'].extend(['Content-Based'] * len(content_names))
        
        # Genre-based recommendations (secondary)
        genre_names, genre_posters = get_genre_based_recommendations(liked_movies, movies, n=2)
        all_recommendations['names'].extend(genre_names)
        all_recommendations['posters'].extend(genre_posters)
        all_recommendations['sources'].extend(['Genre-Based'] * len(genre_names))
        
    else:
        # Fallback to content-based only
        names, posters, _ = recommend_based_on_preferences(liked_movies, movies, similarity, top_n=8)
        all_recommendations['names'] = names
        all_recommendations['posters'] = posters
        all_recommendations['sources'] = ['Content-Based'] * len(names)
    
    return all_recommendations

def handle_like_toggle(movie_name, key_suffix=""):
    """Handle like/unlike functionality with proper state management"""
    if movie_name in st.session_state.liked_movies:
        st.session_state.liked_movies.remove(movie_name)
        st.success(f"❤️ Removed '{movie_name}' from your likes!")
    else:
        st.session_state.liked_movies.append(movie_name)
        st.success(f"💖 Added '{movie_name}' to your likes!")
    
    # Update Firebase
    try:
        db.collection('users').document(st.session_state.username).set({
            'liked_movies': st.session_state.liked_movies,
            'preferences_set': bool(st.session_state.liked_movies)
        }, merge=True)
    except Exception as e:
        st.error(f"Failed to save to database: {e}")

def display_movies_grid(names, posters, key_prefix="", allow_like=True, columns=4, sources=None, show_explanation=False):
    """Enhanced movie grid display with recommendation explanations"""
    if not names:
        return
    
    num_movies = len(names)
    cols = st.columns(min(columns, num_movies))
    
    for idx, (name, poster) in enumerate(zip(names, posters)):
        with cols[idx % columns]:
            with st.container():
                st.image(poster, use_container_width=True)
                st.markdown(f"<h6 style='text-align: center; color: white; margin: 0.5rem 0;'>{name}</h6>", 
                           unsafe_allow_html=True)
                
                # Show recommendation explanation
                if show_explanation and sources and idx < len(sources):
                    source = sources[idx]
                    if source == 'Content-Based':
                        st.caption("🎯 Based on your liked movies")
                    elif source == 'Genre-Based':
                        st.caption("🎭 Matches your genre preferences")
                    else:
                        st.caption("✨ Recommended for you")
                
                if allow_like:
                    button_key = f"{key_prefix}_like_{idx}_{name}_{hash(name) % 10000}"
                    is_liked = name in st.session_state.liked_movies
                    button_text = "💖 Liked" if is_liked else "🤍 Like"
                    
                    if st.button(button_text, key=button_key, use_container_width=True):
                        handle_like_toggle(name, key_suffix=str(idx))
                        time.sleep(0.1)
                        st.rerun()
                        
                    # Add feedback buttons for recommendations
                    if show_explanation and key_prefix == "recommend":
                        col_a, col_b = st.columns(2)
                        with col_a:
                            if st.button("👍", key=f"good_{key_prefix}_{idx}", help="Good recommendation"):
                                st.success("Thanks for the feedback!")
                        with col_b:
                            if st.button("👎", key=f"bad_{key_prefix}_{idx}", help="Not interested"):
                                st.info("We'll learn from this!")

def get_movie_suggestions(query, movies, limit=5):
    """Get movie suggestions for autocomplete"""
    if not query or len(query) < 2:
        return []
    
    # Filter movies that start with or contain the query
    query_lower = query.lower()
    suggestions = []
    
    # First priority: movies that start with the query
    for title in movies['title']:
        if title.lower().startswith(query_lower):
            suggestions.append(title)
    
    # Second priority: movies that contain the query
    if len(suggestions) < limit:
        for title in movies['title']:
            if query_lower in title.lower() and title not in suggestions:
                suggestions.append(title)
    
    return suggestions[:limit]

def search_movies_improved(query, movies):
    """Improved movie search with exact and fuzzy matching"""
    if not query or len(query.strip()) < 2:
        return pd.DataFrame()
    
    query = query.strip()
    results = []
    
    # Exact matches (case insensitive)
    exact_matches = movies[movies['title'].str.lower().str.contains(query.lower(), na=False, regex=False)]
    results.append(exact_matches)
    
    # If we have few exact matches, add fuzzy matches
    if len(exact_matches) < 10:
        # Get close matches using difflib
        all_titles = movies['title'].tolist()
        fuzzy_matches = difflib.get_close_matches(
            query.lower(), 
            [title.lower() for title in all_titles], 
            n=15, 
            cutoff=0.4
        )
        
        # Convert back to original case and get movies
        fuzzy_movies = pd.DataFrame()
        for match in fuzzy_matches:
            match_movies = movies[movies['title'].str.lower() == match]
            fuzzy_movies = pd.concat([fuzzy_movies, match_movies], ignore_index=True)
        
        # Remove duplicates from exact matches
        fuzzy_movies = fuzzy_movies[~fuzzy_movies['title'].isin(exact_matches['title'])]
        results.append(fuzzy_movies)
    
    # Combine results
    final_results = pd.concat(results, ignore_index=True) if results else pd.DataFrame()
    
    # Remove duplicates and limit results
    if not final_results.empty:
        final_results = final_results.drop_duplicates(subset=['title']).head(20)
    
    return final_results

def debug_dataframe_columns(df, name="DataFrame"):
    """Debug helper to show dataframe columns"""
    st.expander(f"🔍 Debug: {name} Columns", expanded=False).write({
        "Columns": list(df.columns),
        "Shape": df.shape,
        "Sample Data": df.head(2).to_dict() if not df.empty else "No data"
    })

def main():
    st.set_page_config(
        page_title="🎬 Smart Movie Recommender", 
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    debug_info = {}
    # Load custom CSS
    load_css()
    
    if st.sidebar.button("🔍 Debug Info"):
      st.sidebar.write("Session State Debug:")
      debug_info = {
        'logged_in': st.session_state.get('logged_in', 'Not set'),
        'username': st.session_state.get('username', 'Not set'),
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
    # Initialize session state - IMPORTANT: Initialize all keys at once
    if 'logged_in' not in st.session_state:
        st.session_state.update({
            'logged_in': False,
            'username': '',
            'liked_movies': [],
            'preferences_set': False,
            'current_tab': 'Discover',
            'first_login': True,
            'random_movies': pd.DataFrame(),
            'search_query': '',
            'search_results': pd.DataFrame(),
            'show_suggestions': False,
            'selected_suggestion': '',
            'login_attempted': False,  # Add this flag
            'signup_attempted': False  # Add this flag
        })

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
                                        
                                        # Load user data
                                        try:
                                            user_data = db.collection('users').document(email).get().to_dict() or {}
                                            st.session_state.liked_movies = user_data.get('liked_movies', [])
                                            st.session_state.preferences_set = bool(st.session_state.liked_movies)
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
                                        st.session_state.liked_movies = []
                                        st.session_state.preferences_set = False
                                        st.session_state.first_login = True
                                        
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
    @st.cache_data
    def load_movies():
        return pickle.load(open(MOVIE_PKL, 'rb'))

    @st.cache_data
    def load_similarity():
        return pickle.load(open(SIMILARITY_PKL, 'rb'))

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
                st.session_state.movies = movies
                st.session_state.similarity = similarity
                st.session_state.models_loaded = True
        else:
            movies = st.session_state.movies
            similarity = st.session_state.similarity
            
        with st.sidebar:
            if st.checkbox("🔧 Debug Mode"):
                debug_dataframe_columns(movies, "Movies")
                
    except Exception as e:
        st.error(f"Error loading model files: {e}")
        return

    # Main App Header
    st.markdown(f"""
    <div class="movie-header">
        <h1>🎬 Welcome back, {st.session_state.username.split('@')[0].title()}!</h1>
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
        st.metric("Available Movies", len(movies))

    # Main Tabs
    tabs = st.tabs(["🔍 Discover", "🎯 Recommendations", "❤️ My Movies"])

    # Discover Tab
    with tabs[0]:
        st.markdown("### 🔍 Discover Amazing Movies")
        
        # Search Section - Fixed Layout
        search_container = st.container()
        with search_container:
            col1, col2 = st.columns([3, 1])
            with col1:
                # Search input with session state persistence
                search_query = st.text_input(
                    "🔎 Search for movies...", 
                    value=st.session_state.get('search_query', ''),
                    placeholder="Type movie name (e.g., Avatar, Inception, Titanic...)",
                    key="movie_search_input"
                )
            
            with col2:
                clear_search = st.button("🗑️ Clear", use_container_width=True)
                if clear_search:
                    st.session_state.search_query = ""
                    st.session_state.search_results = pd.DataFrame()
                    st.session_state.show_suggestions = False
                    st.rerun()

            # Auto-suggestions
            if search_query and len(search_query) >= 2:
                suggestions = get_movie_suggestions(search_query, movies, limit=5)
                if suggestions and search_query != st.session_state.get('selected_suggestion', ''):
                    st.markdown("**💡 Suggestions:**")
                    cols = st.columns(len(suggestions))
                    for idx, suggestion in enumerate(suggestions):
                        with cols[idx]:
                            if st.button(f"🎬 {suggestion}", key=f"suggestion_{idx}", use_container_width=True):
                                st.session_state.search_query = suggestion
                                st.session_state.selected_suggestion = suggestion
                                st.rerun()

        # Process search query
        if search_query and search_query.strip():
            if search_query != st.session_state.get('search_query', ''):
                st.session_state.search_query = search_query
                st.session_state.search_results = search_movies_improved(search_query, movies)
                st.session_state.selected_suggestion = ""
            
            search_results = st.session_state.get('search_results', pd.DataFrame())
        else:
            search_results = pd.DataFrame()
            st.session_state.search_query = ""
            st.session_state.search_results = pd.DataFrame()

        # Display search results
        if not search_results.empty:
            # Fixed: Show actual count of results
            result_count = len(search_results)
            st.success(f"🎯 Found {result_count} movie{'s' if result_count != 1 else ''} matching '{search_query}'")
            
            # Display search results
            posters = [fetch_poster(mid) for mid in search_results['movie_id']]
            display_movies_grid(
                search_results['title'].tolist(), 
                posters, 
                key_prefix="search",
                columns=4
            )
        elif search_query and search_query.strip():
            st.warning(f"🤔 No movies found for '{search_query}'. Try a different search term or check the suggestions above.")

        # Separator between search and random movies
        if not search_query or search_results.empty:
            st.markdown("---")
            
            # Random Movies Section - Fixed Layout
            random_header_container = st.container()
            with random_header_container:
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.markdown("### 🎲 Random Movie Discoveries")
                with col2:
                    if st.button("🎲 Get New Random Movies", use_container_width=True):
                        st.session_state.random_movies = movies.sample(8)
                        st.rerun()

            # Initialize random movies if not exists or empty
            if 'random_movies' not in st.session_state or st.session_state.random_movies.empty:
                st.session_state.random_movies = movies.sample(8)

            # Display random movies
            if isinstance(st.session_state.random_movies, pd.DataFrame) and not st.session_state.random_movies.empty:
                try:
                    posters = [fetch_poster(mid) for mid in st.session_state.random_movies['movie_id']]
                    display_movies_grid(
                        st.session_state.random_movies['title'].tolist(), 
                        posters, 
                        key_prefix="random",
                        columns=4
                    )
                except Exception as e:
                    st.error(f"Error displaying random movies: {e}")
                    st.session_state.random_movies = movies.sample(8)
                    st.rerun()

    # Recommendations Tab
    with tabs[1]:
        st.markdown("### 🎯 Your Personal Recommendations")
        
        if not st.session_state.liked_movies:
            st.info("💡 **Get Started:** Like some movies in the Discover tab to get personalized recommendations!")
            
            st.markdown("#### 🌟 Popular Movies to Get You Started")
            try:
                popular_movies = get_popular_movies(movies, 8)
                posters = [fetch_poster(mid) for mid in popular_movies['movie_id']]
                display_movies_grid(
                    popular_movies['title'].tolist(), 
                    posters, 
                    key_prefix="popular",
                    columns=4
                )
            except Exception as e:
                st.error(f"Error loading popular movies: {e}")
                random_movies = movies.sample(8)
                posters = [fetch_poster(mid) for mid in random_movies['movie_id']]
                display_movies_grid(
                    random_movies['title'].tolist(), 
                    posters, 
                    key_prefix="popular_fallback",
                    columns=4
                )
        else:
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                recommend_btn = st.button("🎯 Get My Recommendations", use_container_width=True)
            with col2:
                st.metric("Your Likes", len(st.session_state.liked_movies))
            with col3:
                recommendation_quality = "Excellent" if len(st.session_state.liked_movies) >= 5 else "Good" if len(st.session_state.liked_movies) >= 3 else "Basic"
                st.metric("Quality", recommendation_quality)

            if recommend_btn or st.session_state.get('show_recommendations', False):
                st.session_state.show_recommendations = True
                
                with st.spinner("🤖 Analyzing your preferences and finding perfect matches..."):
                    # Use enhanced recommendation system
                    recommendations = get_smart_recommendations(
                        st.session_state.liked_movies, movies, similarity, strategy='mixed'
                    )
                
                if recommendations['names']:
                    # Show recommendation insights
                    with st.expander("🧠 How we chose these for you", expanded=True):
                        liked_count = len(st.session_state.liked_movies)
                        if liked_count >= 5:
                            st.success(f"✨ **Excellent Match Confidence** - Based on your {liked_count} liked movies, we're confident these recommendations match your taste!")
                        elif liked_count >= 3:
                            st.info(f"👍 **Good Match Confidence** - With {liked_count} likes, we have a solid understanding of your preferences.")
                        else:
                            st.warning(f"📚 **Learning Your Taste** - Like more movies to get better recommendations! Current likes: {liked_count}")
                        
                        # Show recommendation strategy breakdown
                        content_count = recommendations['sources'].count('Content-Based')
                        genre_count = recommendations['sources'].count('Genre-Based')
                        
                        if content_count > 0:
                            st.write(f"🎯 **{content_count} Content-Based**: Movies similar to what you've liked")
                        if genre_count > 0:
                            st.write(f"🎭 **{genre_count} Genre-Based**: Movies matching your favorite genres")
                    
                    st.success("🎉 Here are your personalized recommendations!")
                    display_movies_grid(
                        recommendations['names'], 
                        recommendations['posters'], 
                        key_prefix="recommend", 
                        allow_like=True, 
                        columns=4,
                        sources=recommendations['sources'],
                        show_explanation=True
                    )
                    
                    # Recommendation tips
                    st.markdown("---")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.info("💡 **Tip**: Like more movies from different genres to get diverse recommendations!")
                    with col2:
                        st.info("🎯 **Pro Tip**: Use 👍/👎 buttons to help us learn your preferences better!")
                        
                else:
                    st.info("🤔 Try liking more diverse movies to get better recommendations!")
                    
                    # Show fallback recommendations
                    st.markdown("#### 🎲 Here are some popular movies you might enjoy:")
                    try:
                        popular_movies = get_popular_movies(movies, 4)
                        posters = [fetch_poster(mid) for mid in popular_movies['movie_id']]
                        display_movies_grid(
                            popular_movies['title'].tolist(), 
                            posters, 
                            key_prefix="fallback_popular",
                            columns=4
                        )
                    except Exception as e:
                        st.error(f"Error loading fallback recommendations: {e}")

    # My Movies Tab
    with tabs[2]:
        st.markdown("### ❤️ Your Movie Collection")
        
        liked = st.session_state.liked_movies
        if liked:
            col1, col2 = st.columns([2, 1])
            with col1:
                st.markdown(f"**You have {len(liked)} liked movies**")
            with col2:
                if st.button("🗑️ Clear All Likes", use_container_width=True):
                    st.session_state.liked_movies = []
                    st.session_state.preferences_set = False
                    try:
                        db.collection('users').document(st.session_state.username).set({
                            'liked_movies': [], 
                            'preferences_set': False
                        }, merge=True)
                        st.success("🧹 All likes cleared!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to clear likes: {e}")

            # Display liked movies
            posters = []
            for movie in liked:
                movie_data = movies[movies['title'] == movie]
                if not movie_data.empty:
                    posters.append(fetch_poster(movie_data.iloc[0]['movie_id']))
                else:
                    posters.append("https://via.placeholder.com/500x750?text=No+Image")
            
            display_movies_grid(liked, posters, key_prefix="liked", columns=4)
        else:
            st.info("💔 Your movie collection is empty!")
            st.markdown("Go to the **Discover** tab to start building your collection by liking movies you enjoy.")
            
            st.markdown("#### 🔥 Trending Movies")
            trending = movies.sample(4)
            posters = [fetch_poster(mid) for mid in trending['movie_id']]
            display_movies_grid(
                trending['title'].tolist(), 
                posters, 
                key_prefix="trending_suggestions",
                columns=4
            )

if __name__ == '__main__':
    main()