# 🎬 Smart Movie Recommender

An AI-powered, Firebase-authenticated Streamlit app that recommends movies based on your personal preferences. Discover, like, and get recommendations—all in a sleek and interactive interface.

---

## 🚀 Features

- 🔐 **User Authentication** (Login/Signup via Firebase)
- ❤️ **Like and Save Movies** to your personal collection
- 🎯 **Personalized Recommendations** using content-based filtering (TF-IDF + Cosine Similarity)
- 🔍 **Smart Search** with fuzzy matching
- 🎲 **Random Movie Discovery**
- 🌐 **Poster Fetching** via TMDB API
- 🧠 **Stateful UI** with interactive movie grid and seamless reruns
- 🧩 **Custom Styling** via CSS integration

---

## 🛠 Tech Stack

- **Frontend:** Streamlit
- **Backend:** Python
- **Authentication & Storage:** Firebase Firestore
- **Machine Learning:** Scikit-learn (TF-IDF & Cosine Similarity)
- **Data:** TMDB 5000 Movies & Credits CSV datasets
- **API:** TMDB (for movie posters)

---

## 📂 Project Structure

```
.
├── updated.py              # Main Streamlit app
├── auth.py                 # Handles sign in/up logic
├── css.py                  # Loads custom styling
├── firebase.json           # Firebase credentials
├── model/
│   ├── movie_list.pkl      # Preprocessed movie data
│   └── similarity.pkl      # Cosine similarity matrix
└── Dataset/
    ├── tmdb_5000_movies.csv
    └── tmdb_5000_credits.csv
```

---

## 🧪 Setup Instructions

### 1. 🔑 Get a TMDB API Key

- Sign up at [TMDB](https://www.themoviedb.org/)
- Go to Account Settings → API → Generate a new API key
- Add it to Streamlit secrets (`.streamlit/secrets.toml`):

```toml
[general]
tmdb_api_key = "************************8"
```

---

### 2. 🔥 Firebase Setup

- Go to [Firebase Console](https://console.firebase.google.com/)
- Create a project → Enable Firestore database
- Download the service account key as `firebase.json` and place it in the project root

---

### 3. 📦 Install Requirements

Make sure you have Python 3.8 or above. Then install dependencies:

```bash
pip install streamlit firebase-admin scikit-learn pandas requests
```

---

### 4. 🧠 Build Recommendation Model

If you don’t already have the `.pkl` files, run a preprocessing script to generate:

- `model/movie_list.pkl`
- `model/similarity.pkl`

To run the preprocessing script

```bash
python build_model.py
```

---

## ▶️ Run the App

```bash
streamlit run updated.py
```

## To Run the test cases

```bash
python test-case.py
```

---

## 🌍 Deployment Options (Free)

### 👉 Recommended: [Streamlit Community Cloud](https://streamlit.io/cloud)

1. Push your project to a **public GitHub repo**
2. Log into [Streamlit Cloud](https://streamlit.io/cloud)
3. Click **"New App"**, connect your repo
4. Set `updated.py` as the entry point
5. Add secrets in app settings

---


## 🙌 Acknowledgements

- [TMDB](https://www.themoviedb.org/) for movie data and posters
- [Firebase](https://firebase.google.com/) for authentication and Firestore
- [Streamlit](https://streamlit.io/) for rapid web app development

---

## 📜 License

MIT License – Free to use and modify for personal and academic projects.



## 👨‍💻 Author

Built with ❤️ by [Maaz Siddiqui, SSUET End-Sem project, Batch 2022F]
#
