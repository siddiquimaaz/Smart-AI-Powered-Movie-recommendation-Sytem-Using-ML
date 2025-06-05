import os
import pickle
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import ast

def convert(text):
    """Convert string representation of list to actual list of names"""
    L = []
    try:
        for i in ast.literal_eval(text):
            if isinstance(i, dict) and 'name' in i:
                L.append(i['name'])
        return L
    except:
        return []

def convert3(text):
    """Convert cast data, limiting to top 3"""
    L = []
    counter = 0
    try:
        for i in ast.literal_eval(text):
            if counter < 3:
                if isinstance(i, dict) and 'name' in i:
                    L.append(i['name'])
                counter += 1
            else:
                break
        return L
    except:
        return []

def fetch_director(text):
    """Extract director from crew data"""
    L = []
    try:
        for i in ast.literal_eval(text):
            if isinstance(i, dict) and i.get('job') == 'Director':
                L.append(i['name'])
        return L
    except:
        return []

def collapse(L):
    """Remove spaces from names to avoid issues"""
    if isinstance(L, list):
        L1 = []
        for i in L:
            L1.append(str(i).replace(" ", ""))
        return L1
    return []

def build_recommendation_model():
    """Build and save the movie recommendation model"""
    
    # Paths
    DATA_DIR = "D:\spring 2025S\AI-Lab\Smart-AI-Powered-Movie-recommendation-Sytem-Using-ML\Dataset"
    MOVIES_PATH = os.path.join(DATA_DIR, "tmdb_5000_movies.csv")
    CREDITS_PATH = os.path.join(DATA_DIR, "tmdb_5000_credits.csv")
    MODEL_DIR = "model"
    
    # Create model directory if it doesn't exist
    os.makedirs(MODEL_DIR, exist_ok=True)
    
    print("Loading datasets...")
    
    # Check if files exist
    if not os.path.exists(MOVIES_PATH):
        print(f"Error: Movies file not found at {MOVIES_PATH}")
        print("Please ensure the tmdb_5000_movies.csv file exists in the Dataset folder")
        return False
        
    if not os.path.exists(CREDITS_PATH):
        print(f"Error: Credits file not found at {CREDITS_PATH}")
        print("Please ensure the tmdb_5000_credits.csv file exists in the Dataset folder")
        return False
    
    try:
        # Load datasets
        movies = pd.read_csv(MOVIES_PATH)
        credits = pd.read_csv(CREDITS_PATH)
        
        print(f"Movies dataset shape: {movies.shape}")
        print(f"Credits dataset shape: {credits.shape}")
        
        # Merge datasets
        movies = movies.merge(credits, on='title')
        
        print(f"Merged dataset shape: {movies.shape}")
        
        # Select relevant columns
        movies = movies[['movie_id', 'title', 'overview', 'genres', 'keywords', 'cast', 'crew']]
        
        # Remove rows with missing values
        movies.dropna(inplace=True)
        
        print(f"After removing NaN values: {movies.shape}")
        
        # Convert string representations to lists
        print("Processing genres...")
        movies['genres'] = movies['genres'].apply(convert)
        
        print("Processing keywords...")
        movies['keywords'] = movies['keywords'].apply(convert)
        
        print("Processing cast...")
        movies['cast'] = movies['cast'].apply(convert3)
        
        print("Processing crew...")
        movies['crew'] = movies['crew'].apply(fetch_director)
        
        # Clean overview text
        movies['overview'] = movies['overview'].apply(lambda x: x.split() if isinstance(x, str) else [])
        
        # Remove spaces from names
        movies['cast'] = movies['cast'].apply(collapse)
        movies['crew'] = movies['crew'].apply(collapse)
        movies['genres'] = movies['genres'].apply(collapse)
        movies['keywords'] = movies['keywords'].apply(collapse)
        
        # Create tags column by combining all features
        movies['tags'] = movies['overview'] + movies['genres'] + movies['keywords'] + movies['cast'] + movies['crew']
        
        # Create new dataframe with required columns
        new = movies[['movie_id', 'title', 'tags']].copy()
        
        # Convert tags list to string
        new['tags'] = new['tags'].apply(lambda x: " ".join(x).lower())
        
        print(f"Final dataset shape: {new.shape}")
        print("Sample data:")
        print(new.head(2))
        
        # Create count vectorizer and similarity matrix
        print("Creating count vectorizer...")
        cv = CountVectorizer(max_features=5000, stop_words='english')
        
        print("Fitting and transforming text data...")
        vector = cv.fit_transform(new['tags']).toarray()
        
        print(f"Vector shape: {vector.shape}")
        
        print("Computing cosine similarity... This may take a while...")
        similarity = cosine_similarity(vector)
        
        print(f"Similarity matrix shape: {similarity.shape}")
        
        # Save the processed data and similarity matrix
        print("Saving movie list...")
        pickle.dump(new, open(os.path.join(MODEL_DIR, 'movie_list.pkl'), 'wb'))
        
        print("Saving similarity matrix...")
        pickle.dump(similarity, open(os.path.join(MODEL_DIR, 'similarity.pkl'), 'wb'))
        
        print("✅ Model built successfully!")
        print(f"Files saved in {MODEL_DIR}/ directory:")
        print("- movie_list.pkl")
        print("- similarity.pkl")
        
        return True
        
    except Exception as e:
        print(f"Error building model: {str(e)}")
        return False

def test_model():
    """Test the built model"""
    MODEL_DIR = "model"
    MOVIE_PKL = os.path.join(MODEL_DIR, "movie_list.pkl")
    SIMILARITY_PKL = os.path.join(MODEL_DIR, "similarity.pkl")
    
    try:
        print("Testing model files...")
        movies = pickle.load(open(MOVIE_PKL, 'rb'))
        similarity = pickle.load(open(SIMILARITY_PKL, 'rb'))
        
        print(f"✅ Movies loaded: {len(movies)} movies")
        print(f"✅ Similarity matrix loaded: {similarity.shape}")
        
        # Test recommendation function
        def recommend(movie):
            index = movies[movies['title'] == movie].index[0]
            distances = sorted(list(enumerate(similarity[index])), reverse=True, key=lambda x: x[1])
            recommended_movies = []
            for i in distances[1:6]:  # Top 5 recommendations
                recommended_movies.append(movies.iloc[i[0]].title)
            return recommended_movies
        
        # Test with a popular movie
        test_movie = movies.iloc[0]['title']  # First movie in dataset
        print(f"\nTesting recommendations for: {test_movie}")
        recommendations = recommend(test_movie)
        print("Recommendations:")
        for i, movie in enumerate(recommendations, 1):
            print(f"{i}. {movie}")
            
        return True
        
    except Exception as e:
        print(f"❌ Error testing model: {str(e)}")
        return False

if __name__ == "__main__":
    print("🎬 Building Movie Recommendation Model...")
    print("=" * 50)
    
    success = build_recommendation_model()
    
    if success:
        print("\n" + "=" * 50)
        print("Testing the built model...")
        test_success = test_model()
        
        if test_success:
            print("\n🎉 Everything is ready! You can now run your Streamlit app.")
        else:
            print("\n❌ Model built but testing failed. Please check the files.")
    else:
        print("\n❌ Failed to build model. Please check your dataset files.")
        print("\nMake sure you have:")
        print("1. tmdb_5000_movies.csv in D:/spring 2025S/project/Dataset/")
        print("2. tmdb_5000_credits.csv in D:/spring 2025S/project/Dataset/")