import requests
import streamlit as st

# Get Firebase Web API key from secrets
API_KEY = st.secrets["firebase"]["web_api_key"]

# Firebase endpoints
SIGNUP_URL = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={API_KEY}"
SIGNIN_URL = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={API_KEY}"
UPDATE_PROFILE_URL = f"https://identitytoolkit.googleapis.com/v1/accounts:update?key={API_KEY}"
GET_USER_URL = f"https://identitytoolkit.googleapis.com/v1/accounts:lookup?key={API_KEY}"

def sign_up(username, email, password, full_name):
    payload = {
        "email": email,
        "password": password,
        "returnSecureToken": True
    }

    try:
        response = requests.post(SIGNUP_URL, json=payload)
        result = response.json()
        if "error" in result:
            return {"status": "error", "message": result["error"]["message"]}

        id_token = result["idToken"]
        uid = result["localId"]  # Get UID from response

        # Set display name
        update_payload = {
            "idToken": id_token,
            "displayName": full_name,
            "returnSecureToken": True
        }
        update_response = requests.post(UPDATE_PROFILE_URL, json=update_payload)

        return {
            "status": "success",
            "message": "Signup successful!",
            "idToken": id_token,
            "displayName": full_name,
            "uid": uid,  # Include UID in response
            "email": email
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}

def sign_in(email, password):
    payload = {
        "email": email,
        "password": password,
        "returnSecureToken": True
    }

    try:
        response = requests.post(SIGNIN_URL, json=payload)
        result = response.json()
        if "error" in result:
            return {"status": "error", "message": result["error"]["message"]}

        return {
            "status": "success",
            "message": "Login successful!",
            "idToken": result["idToken"],
            "email": result["email"],
            "uid": result["localId"]  # Include UID in response
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}

def get_name(id_token):
    try:
        response = requests.post(GET_USER_URL, json={"idToken": id_token})
        result = response.json()
        if "users" in result and result["users"]:
            return result["users"][0].get("displayName", "")
        return ""
    except Exception:
        return ""