import streamlit as st
import base64
import os

def load_css():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');
        
        * {
            box-sizing: border-box; 
            margin: 0;
            padding: 0;
            font-family: 'Poppins', sans-serif;
        }
                
        /* Main app styling */
        .main {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 1rem;
            min-height: 100vh;
        }
        
        /* Header styling */
        .movie-header {
            text-align: center;
            color: white;
            margin-bottom: 2rem;
            padding: 2rem;
            background: rgba(0,0,0,0.2);
            border-radius: 15px;
            backdrop-filter: blur(10px);
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        }
        
        .movie-header h1 {
            font-size: 2.5rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .movie-header p {
            font-size: 1.1rem;
            opacity: 0.9;
        }
        
        /* Movie card styling */
        .movie-card {
            background: rgba(255,255,255,0.1);
            border-radius: 15px;
            padding: 1.5rem;
            margin: 0.5rem;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.2);
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }
        
        .movie-card:hover {
            transform: translateY(-8px);
            box-shadow: 0 15px 25px rgba(0,0,0,0.3);
            background: rgba(255,255,255,0.15);
        }
        
        /* Button styling */
        .stButton > button {
            background: linear-gradient(45deg, #ff6b6b, #ee5a24);
            color: white;
            border: none;
            border-radius: 25px;
            padding: 0.75rem 1.5rem;
            font-weight: 500;
            font-size: 1rem;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(255,107,107,0.3);
        }
        
        .stButton > button:hover {
            transform: scale(1.05);
            box-shadow: 0 8px 25px rgba(255,107,107,0.4);
            background: linear-gradient(45deg, #ff5252, #d63031);
        }
        
        .stButton > button:active {
            transform: scale(0.98);
        }
        
        /* Tab styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 1rem;
            background: rgba(255,255,255,0.1);
            border-radius: 15px;
            padding: 0.75rem;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.2);
        }
        
        .stTabs [data-baseweb="tab"] {
            background: transparent;
            border-radius: 10px;
            color: white;
            font-weight: 500;
            padding: 0.5rem 1rem;
            transition: all 0.3s ease;
        }
        
        .stTabs [data-baseweb="tab"]:hover {
            background: rgba(255,255,255,0.1);
        }
        
        .stTabs [aria-selected="true"] {
            background: rgba(255,255,255,0.25);
            backdrop-filter: blur(10px);
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        /* Search styling */
        .stTextInput > div > div > input {
            background: rgba(255,255,255,0.15);
            border-radius: 25px;
            border: 1px solid rgba(255,255,255,0.3);
            padding: 1rem 1.5rem;
            font-size: 1.1rem;
            color: white;
            backdrop-filter: blur(10px);
            transition: all 0.3s ease;
        }
        
        .stTextInput > div > div > input:focus {
            background: rgba(255,255,255,0.2);
            border-color: rgba(255,255,255,0.5);
            box-shadow: 0 0 0 3px rgba(255,255,255,0.1);
            outline: none;
        }
        
        .stTextInput > div > div > input::placeholder {
            color: rgba(255,255,255,0.7);
        }
        
        /* Like button special styling */
        .like-btn {
            font-size: 1.5rem;
            transition: all 0.2s ease;
            background: transparent;
            border: none;
            cursor: pointer;
            padding: 0.5rem;
            border-radius: 50%;
        }
        
        .like-btn:hover {
            transform: scale(1.3);
            background: rgba(255,107,107,0.2);
        }
        
        .like-btn.liked {
            color: #ff6b6b;
            animation: heartbeat 0.6s ease-in-out;
        }
        
        @keyframes heartbeat {
            0% { transform: scale(1); }
            50% { transform: scale(1.3); }
            100% { transform: scale(1); }
        }
        
        /* Success/Error message styling */
        .stAlert {
            border-radius: 15px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.2);
        }
        
        .stSuccess {
            background: rgba(46,204,113,0.1);
            border-color: rgba(46,204,113,0.3);
        }
        
        .stError {
            background: rgba(231,76,60,0.1);
            border-color: rgba(231,76,60,0.3);
        }
        
        .stInfo {
            background: rgba(52,152,219,0.1);
            border-color: rgba(52,152,219,0.3);
        }
        
        /* Movie grid styling */
        .movie-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 1.5rem;
            padding: 1rem;
        }
        
        /* Selectbox styling */
        .stSelectbox > div > div > div {
            background: rgba(255,255,255,0.15);
            border-radius: 15px;
            border: 1px solid rgba(255,255,255,0.3);
            backdrop-filter: blur(10px);
        }
        
        /* Sidebar styling */
        .css-1d391kg {
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
        }
        
        /* Text styling for better readability */
        .stMarkdown, .stText {
            color: white;
        }
        
        /* Rating stars */
        .rating-stars {
            color: #ffd700;
            font-size: 1.2rem;
            margin: 0.5rem 0;
        }
        
        /* Loading spinner */
        .stSpinner > div {
            border-color: rgba(255,255,255,0.3);
            border-top-color: white;
        }
        
        /* Scrollbar styling */
        ::-webkit-scrollbar {
            width: 8px;
        }
        
        ::-webkit-scrollbar-track {
            background: rgba(255,255,255,0.1);
            border-radius: 10px;
        }
        
        ::-webkit-scrollbar-thumb {
            background: rgba(255,255,255,0.3);
            border-radius: 10px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: rgba(255,255,255,0.5);
        }
        
        /* Mobile responsiveness */
        @media (max-width: 768px) {
            .movie-header h1 {
                font-size: 2rem;
            }
            
            .movie-grid {
                grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
                gap: 1rem;
            }
            
            .movie-card {
                padding: 1rem;
            }
        }
    </style>
    """, unsafe_allow_html=True)