import firebase_admin
from firebase_admin import credentials, firestore
import streamlit as st
from functools import lru_cache
import json

# Initialize Firebase Admin once using secrets
def initialize_firebase():
    if not firebase_admin._apps:
        # Get Firebase service account from secrets
        firebase_secrets = st.secrets["firebase"]["service_account"]
        
        # Convert the secrets to a dictionary for credentials
        cred_dict = {
            "type": firebase_secrets["type"],
            "project_id": firebase_secrets["project_id"],
            "private_key_id": firebase_secrets["private_key_id"],
            "private_key": firebase_secrets["private_key"].replace("\\n", "\n"),
            "client_email": firebase_secrets["client_email"],
            "client_id": firebase_secrets["client_id"],
            "auth_uri": firebase_secrets["auth_uri"],
            "token_uri": firebase_secrets["token_uri"],
            "auth_provider_x509_cert_url": firebase_secrets["auth_provider_x509_cert_url"],
            "client_x509_cert_url": firebase_secrets["client_x509_cert_url"]
        }
        
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)

# Initialize Firebase
initialize_firebase()
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