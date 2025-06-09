import firebase_admin
from firebase_admin import credentials, firestore
import streamlit as st
from functools import lru_cache

# Initialize Firebase Admin once
cred = credentials.Certificate("firebase.json")
firebase_admin.initialize_app(cred)

db = firestore.client()

# Cache user data for 5 minutes
@lru_cache(maxsize=100)
def get_cached_user_data(user_id):
    try:
        doc_ref = db.collection('users').document(user_id)
        doc = doc_ref.get()
        if doc.exists:
            return doc.to_dict()
        return None
    except Exception as e:
        print(f"[ERROR] Error getting cached user data: {e}")
        return None

def save_likes_to_db(user_id, liked_movies, email=None):
    """Save user likes to Firestore with optimized batch write"""
    try:
        doc_ref = db.collection('users').document(user_id)
        data = {
            'liked_movies': liked_movies,
            'preferences_set': bool(liked_movies)
        }
        if email:
            data['email'] = email
            
        doc_ref.set(data, merge=True)
        return {"status": "success"}
    except Exception as e:
        print(f"[ERROR] Error saving likes to Firestore: {e}")
        return {"status": "error", "message": str(e)}

def get_likes_from_db(user_id):
    """Get user likes from Firestore with caching"""
    try:
        # Try to get from cache first
        cached_data = get_cached_user_data(user_id)
        if cached_data:
            return cached_data.get('liked_movies', [])
            
        # If not in cache, get from Firestore
        doc_ref = db.collection('users').document(user_id)
        doc = doc_ref.get()
        if doc.exists:
            liked_movies = doc.to_dict().get('liked_movies', [])
            return liked_movies
        return []
    except Exception as e:
        print(f"[ERROR] Error getting likes from Firestore: {e}")
        return []

def clear_user_cache(user_id):
    """Clear user data from cache"""
    get_cached_user_data.cache_clear()
