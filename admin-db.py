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
        doc_ref = db.collection('users').document(user_id)
        doc = doc_ref.get()
        if doc.exists:
            return doc.to_dict().get('liked_movies', [])
        return []
    except Exception as e:
        print(f"Error getting likes: {e}")
        return []
