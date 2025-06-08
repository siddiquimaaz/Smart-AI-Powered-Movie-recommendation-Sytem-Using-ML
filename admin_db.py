import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase Admin once
cred = credentials.Certificate("firebase.json")
firebase_admin.initialize_app(cred)

db = firestore.client()

def save_likes_to_db(user_id, liked_movies):
    try:
        doc_ref = db.collection('users').document(user_id)
        doc_ref.set({'liked_movies': liked_movies}, merge=True)
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def get_likes_from_db(user_id):
    try:
        print(f"[DEBUG] Fetching likes for user_id: {user_id}")
        doc_ref = db.collection('users').document(user_id)
        doc = doc_ref.get()
        if doc.exists:
            liked_movies = doc.to_dict().get('liked_movies', [])
            print(f"[DEBUG] Retrieved liked_movies: {liked_movies}")
            return liked_movies
        else:
            print(f"[DEBUG] No document found for user_id: {user_id}")
            return []
    except Exception as e:
        print(f"[ERROR] Error getting likes from Firestore: {e}")
        return []
