# import streamlit as st
# import base64
# import os

# def load_css():
#     st.markdown("""
#     <style>
#         @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');
        
#         * {
#             box-sizing: border-box; 
#             margin: 0;
#             padding: 0;
#             font-family: 'Poppins', sans-serif;
#         }
                
#         /* Main app styling */
#         .main {
#             background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
#             padding: 1rem;
#             min-height: 100vh;
#         }
        
#         /* Header styling */
#         .movie-header {
#             text-align: center;
#             color: white;
#             margin-bottom: 2rem;
#             padding: 2rem;
#             background: rgba(0,0,0,0.2);
#             border-radius: 15px;
#             backdrop-filter: blur(10px);
#             box-shadow: 0 8px 32px rgba(0,0,0,0.1);
#         }
        
#         .movie-header h1 {
#             font-size: 2.5rem;
#             font-weight: 600;
#             margin-bottom: 0.5rem;
#             text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
#         }
        
#         .movie-header p {
#             font-size: 1.1rem;
#             opacity: 0.9;
#         }
        
#         /* Movie card styling */
#         .movie-card {
#             background: rgba(255,255,255,0.1);
#             border-radius: 15px;
#             padding: 1.5rem;
#             margin: 0.5rem;
#             backdrop-filter: blur(10px);
#             border: 1px solid rgba(255,255,255,0.2);
#             transition: all 0.3s ease;
#             box-shadow: 0 4px 15px rgba(0,0,0,0.1);
#         }
        
#         .movie-card:hover {
#             transform: translateY(-8px);
#             box-shadow: 0 15px 25px rgba(0,0,0,0.3);
#             background: rgba(255,255,255,0.15);
#         }
        
#         /* Button styling */
#         .stButton > button {
#             background: linear-gradient(45deg, #ff6b6b, #ee5a24);
#             color: white;
#             border: none;
#             border-radius: 25px;
#             padding: 0.75rem 1.5rem;
#             font-weight: 500;
#             font-size: 1rem;
#             cursor: pointer;
#             transition: all 0.3s ease;
#             box-shadow: 0 4px 15px rgba(255,107,107,0.3);
#         }
        
#         .stButton > button:hover {
#             transform: scale(1.05);
#             box-shadow: 0 8px 25px rgba(255,107,107,0.4);
#             background: linear-gradient(45deg, #ff5252, #d63031);
#         }
        
#         .stButton > button:active {
#             transform: scale(0.98);
#         }
        
#         /* Tab styling */
#         .stTabs [data-baseweb="tab-list"] {
#             gap: 1rem;
#             background: rgba(255,255,255,0.1);
#             border-radius: 15px;
#             padding: 0.75rem;
#             backdrop-filter: blur(10px);
#             border: 1px solid rgba(255,255,255,0.2);
#         }
        
#         .stTabs [data-baseweb="tab"] {
#             background: transparent;
#             border-radius: 10px;
#             color: white;
#             font-weight: 500;
#             padding: 0.5rem 1rem;
#             transition: all 0.3s ease;
#         }
        
#         .stTabs [data-baseweb="tab"]:hover {
#             background: rgba(255,255,255,0.1);
#         }
        
#         .stTabs [aria-selected="true"] {
#             background: rgba(255,255,255,0.25);
#             backdrop-filter: blur(10px);
#             box-shadow: 0 2px 10px rgba(0,0,0,0.1);
#         }
        
#         /* Search styling */
#         .stTextInput > div > div > input {
#             background: rgba(255,255,255,0.15);
#             border-radius: 25px;
#             border: 1px solid rgba(255,255,255,0.3);
#             padding: 1rem 1.5rem;
#             font-size: 1.1rem;
#             color: white;
#             backdrop-filter: blur(10px);
#             transition: all 0.3s ease;
#         }
        
#         .stTextInput > div > div > input:focus {
#             background: rgba(255,255,255,0.2);
#             border-color: rgba(255,255,255,0.5);
#             box-shadow: 0 0 0 3px rgba(255,255,255,0.1);
#             outline: none;
#         }
        
#         .stTextInput > div > div > input::placeholder {
#             color: rgba(255,255,255,0.7);
#         }
        
#         /* Like button special styling */
#         .like-btn {
#             font-size: 1.5rem;
#             transition: all 0.2s ease;
#             background: transparent;
#             border: none;
#             cursor: pointer;
#             padding: 0.5rem;
#             border-radius: 50%;
#         }
        
#         .like-btn:hover {
#             transform: scale(1.3);
#             background: rgba(255,107,107,0.2);
#         }
        
#         .like-btn.liked {
#             color: #ff6b6b;
#             animation: heartbeat 0.6s ease-in-out;
#         }
        
#         @keyframes heartbeat {
#             0% { transform: scale(1); }
#             50% { transform: scale(1.3); }
#             100% { transform: scale(1); }
#         }
        
#         /* Success/Error message styling */
#         .stAlert {
#             border-radius: 15px;
#             backdrop-filter: blur(10px);
#             border: 1px solid rgba(255,255,255,0.2);
#         }
        
#         .stSuccess {
#             background: rgba(46,204,113,0.1);
#             border-color: rgba(46,204,113,0.3);
#         }
        
#         .stError {
#             background: rgba(231,76,60,0.1);
#             border-color: rgba(231,76,60,0.3);
#         }
        
#         .stInfo {
#             background: rgba(52,152,219,0.1);
#             border-color: rgba(52,152,219,0.3);
#         }
        
#         /* Movie grid styling */
#         .movie-grid {
#             display: grid;
#             grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
#             gap: 1.5rem;
#             padding: 1rem;
#         }
        
#         /* Selectbox styling */
#         .stSelectbox > div > div > div {
#             background: rgba(255,255,255,0.15);
#             border-radius: 15px;
#             border: 1px solid rgba(255,255,255,0.3);
#             backdrop-filter: blur(10px);
#         }
        
#         /* Sidebar styling */
#         .css-1d391kg {
#             background: rgba(255,255,255,0.1);
#             backdrop-filter: blur(10px);
#         }
        
#         /* Text styling for better readability */
#         .stMarkdown, .stText {
#             color: white;
#         }
        
#         /* Rating stars */
#         .rating-stars {
#             color: #ffd700;
#             font-size: 1.2rem;
#             margin: 0.5rem 0;
#         }
        
#         /* Loading spinner */
#         .stSpinner > div {
#             border-color: rgba(255,255,255,0.3);
#             border-top-color: white;
#         }
        
#         /* Scrollbar styling */
#         ::-webkit-scrollbar {
#             width: 8px;
#         }
        
#         ::-webkit-scrollbar-track {
#             background: rgba(255,255,255,0.1);
#             border-radius: 10px;
#         }
        
#         ::-webkit-scrollbar-thumb {
#             background: rgba(255,255,255,0.3);
#             border-radius: 10px;
#         }
        
#         ::-webkit-scrollbar-thumb:hover {
#             background: rgba(255,255,255,0.5);
#         }
        
#         /* Mobile responsiveness */
#         @media (max-width: 768px) {
#             .movie-header h1 {
#                 font-size: 2rem;
#             }
            
#             .movie-grid {
#                 grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
#                 gap: 1rem;
#             }
            
#             .movie-card {
#                 padding: 1rem;
#             }
#         }
#     </style>
#     """, unsafe_allow_html=True)

import streamlit as st
import base64
import os

def load_css():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');
        
        * {
            box-sizing: border-box; 
            margin: 0;
            padding: 0;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }
                
        /* Main app styling with dark premium theme */
        .main {
            background: linear-gradient(135deg, #0f0f23 0%, #1a0a2e 50%, #16213e 100%);
            background-attachment: fixed;
            padding: 1rem;
            min-height: 100vh;
            position: relative;
        }
        
        .main::before {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: 
                radial-gradient(circle at 20% 20%, rgba(120, 119, 198, 0.1) 0%, transparent 50%),
                radial-gradient(circle at 80% 80%, rgba(255, 119, 198, 0.1) 0%, transparent 50%),
                radial-gradient(circle at 40% 40%, rgba(120, 219, 255, 0.05) 0%, transparent 50%);
            pointer-events: none;
            z-index: -1;
        }
        
        /* Header styling with premium dark theme */
        .movie-header {
            text-align: center;
            color: #ffffff;
            margin-bottom: 3rem;
            padding: 3rem 2rem;
            background: rgba(0, 0, 0, 0.4);
            border-radius: 24px;
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            box-shadow: 
                0 20px 40px rgba(0, 0, 0, 0.3),
                inset 0 1px 0 rgba(255, 255, 255, 0.1);
            position: relative;
            overflow: hidden;
        }
        
        .movie-header::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.05), transparent);
            animation: shimmer 3s infinite;
        }
        
        @keyframes shimmer {
            0% { left: -100%; }
            100% { left: 100%; }
        }
        
        .movie-header h1 {
            font-size: 3rem;
            font-weight: 800;
            margin-bottom: 1rem;
            background: linear-gradient(135deg, #ffffff 0%, #e0e7ff 50%, #c7d2fe 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            text-shadow: none;
            position: relative;
            z-index: 1;
        }
        
        .movie-header p {
            font-size: 1.2rem;
            opacity: 0.8;
            color: #a8b3cf;
            font-weight: 400;
            position: relative;
            z-index: 1;
        }
        
        /* Movie card styling - premium dark */
        .movie-card {
            background: rgba(0, 0, 0, 0.6);
            border-radius: 20px;
            padding: 2rem;
            margin: 0.75rem;
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.08);
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: 
                0 8px 32px rgba(0, 0, 0, 0.3),
                inset 0 1px 0 rgba(255, 255, 255, 0.05);
            position: relative;
            overflow: hidden;
        }
        
        .movie-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 2px;
            background: linear-gradient(90deg, #7c3aed, #06b6d4, #10b981);
            opacity: 0;
            transition: opacity 0.4s ease;
        }
        
        .movie-card:hover {
            transform: translateY(-12px) scale(1.02);
            box-shadow: 
                0 25px 50px rgba(0, 0, 0, 0.5),
                0 0 0 1px rgba(255, 255, 255, 0.1),
                inset 0 1px 0 rgba(255, 255, 255, 0.1);
            background: rgba(0, 0, 0, 0.7);
        }
        
        .movie-card:hover::before {
            opacity: 1;
        }
        
        /* Button styling - premium dark */
        .stButton > button {
            background: linear-gradient(135deg, #7c3aed 0%, #a855f7 50%, #c084fc 100%);
            color: white;
            border: none;
            border-radius: 14px;
            padding: 1rem 2rem;
            font-weight: 600;
            font-size: 1rem;
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: 
                0 8px 20px rgba(124, 58, 237, 0.3),
                inset 0 1px 0 rgba(255, 255, 255, 0.2);
            position: relative;
            overflow: hidden;
        }
        
        .stButton > button::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
            transition: left 0.5s;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 
                0 12px 30px rgba(124, 58, 237, 0.4),
                inset 0 1px 0 rgba(255, 255, 255, 0.3);
            background: linear-gradient(135deg, #8b5cf6 0%, #a855f7 50%, #c084fc 100%);
        }
        
        .stButton > button:hover::before {
            left: 100%;
        }
        
        .stButton > button:active {
            transform: translateY(0);
        }
        
        /* Tab styling - premium dark */
        .stTabs [data-baseweb="tab-list"] {
            gap: 0.5rem;
            background: rgba(0, 0, 0, 0.4);
            border-radius: 16px;
            padding: 0.5rem;
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.05);
        }
        
        .stTabs [data-baseweb="tab"] {
            background: transparent;
            border-radius: 12px;
            color: #a8b3cf;
            font-weight: 500;
            padding: 0.75rem 1.5rem;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            border: 1px solid transparent;
        }
        
        .stTabs [data-baseweb="tab"]:hover {
            background: rgba(255, 255, 255, 0.05);
            color: #ffffff;
            border-color: rgba(255, 255, 255, 0.1);
        }
        
        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, rgba(124, 58, 237, 0.3) 0%, rgba(168, 85, 247, 0.3) 100%);
            color: #ffffff;
            border-color: rgba(124, 58, 237, 0.5);
            box-shadow: 
                0 4px 12px rgba(124, 58, 237, 0.2),
                inset 0 1px 0 rgba(255, 255, 255, 0.1);
        }
        
        /* Search styling - premium dark */
        .stTextInput > div > div > input {
            background: rgba(0, 0, 0, 0.4);
            border-radius: 16px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            padding: 1.25rem 1.75rem;
            font-size: 1.1rem;
            color: #ffffff;
            backdrop-filter: blur(20px);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.05);
        }
        
        .stTextInput > div > div > input:focus {
            background: rgba(0, 0, 0, 0.6);
            border-color: rgba(124, 58, 237, 0.5);
            box-shadow: 
                0 0 0 3px rgba(124, 58, 237, 0.2),
                inset 0 1px 0 rgba(255, 255, 255, 0.1);
            outline: none;
        }
        
        .stTextInput > div > div > input::placeholder {
            color: #6b7280;
            font-weight: 400;
        }
        
        /* Like button special styling */
        .like-btn {
            font-size: 1.5rem;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(255, 255, 255, 0.1);
            cursor: pointer;
            padding: 0.75rem;
            border-radius: 50%;
            backdrop-filter: blur(10px);
        }
        
        .like-btn:hover {
            transform: scale(1.3);
            background: rgba(239, 68, 68, 0.2);
            border-color: rgba(239, 68, 68, 0.3);
            box-shadow: 0 8px 20px rgba(239, 68, 68, 0.3);
        }
        
        .like-btn.liked {
            color: #ef4444;
            background: rgba(239, 68, 68, 0.1);
            border-color: rgba(239, 68, 68, 0.3);
            animation: heartbeat 0.6s ease-in-out;
        }
        
        @keyframes heartbeat {
            0% { transform: scale(1); }
            50% { transform: scale(1.3); }
            100% { transform: scale(1); }
        }
        
        /* Alert styling - premium dark */
        .stAlert {
            border-radius: 16px;
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            box-shadow: 0 8px 20px rgba(0, 0, 0, 0.2);
        }
        
        .stSuccess {
            background: rgba(16, 185, 129, 0.1);
            border-color: rgba(16, 185, 129, 0.3);
            color: #34d399;
        }
        
        .stError {
            background: rgba(239, 68, 68, 0.1);
            border-color: rgba(239, 68, 68, 0.3);
            color: #f87171;
        }
        
        .stInfo {
            background: rgba(59, 130, 246, 0.1);
            border-color: rgba(59, 130, 246, 0.3);
            color: #60a5fa;
        }
        
        /* Movie grid styling */
        .movie-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 2rem;
            padding: 1.5rem;
        }
        
        /* Selectbox styling - premium dark */
        .stSelectbox > div > div > div {
            background: rgba(0, 0, 0, 0.4);
            border-radius: 16px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(20px);
            color: #ffffff;
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.05);
        }
        
        /* Sidebar styling */
        .css-1d391kg {
            background: rgba(0, 0, 0, 0.3);
            backdrop-filter: blur(20px);
            border-right: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        /* Text styling for better readability */
        .stMarkdown, .stText {
            color: #e2e8f0;
        }
        
        /* Rating stars - premium styling */
        .rating-stars {
            color: #fbbf24;
            font-size: 1.3rem;
            margin: 0.75rem 0;
            text-shadow: 0 2px 4px rgba(251, 191, 36, 0.3);
            filter: drop-shadow(0 0 6px rgba(251, 191, 36, 0.4));
        }
        
        /* Loading spinner */
        .stSpinner > div {
            border-color: rgba(124, 58, 237, 0.2);
            border-top-color: #7c3aed;
        }
        
        /* Custom scrollbar */
        ::-webkit-scrollbar {
            width: 8px;
        }
        
        ::-webkit-scrollbar-track {
            background: rgba(0, 0, 0, 0.2);
            border-radius: 10px;
        }
        
        ::-webkit-scrollbar-thumb {
            background: linear-gradient(135deg, #7c3aed, #a855f7);
            border-radius: 10px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: linear-gradient(135deg, #8b5cf6, #c084fc);
        }
        
        /* Premium glow effects */
        .glow-effect {
            box-shadow: 
                0 0 20px rgba(124, 58, 237, 0.3),
                0 0 40px rgba(124, 58, 237, 0.1),
                0 0 80px rgba(124, 58, 237, 0.05);
        }
        
        /* Glassmorphism containers */
        .glass-container {
            background: rgba(0, 0, 0, 0.25);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            box-shadow: 
                0 8px 32px rgba(0, 0, 0, 0.3),
                inset 0 1px 0 rgba(255, 255, 255, 0.05);
        }
        
        /* Animated gradient text */
        .gradient-text {
            background: linear-gradient(135deg, #7c3aed 0%, #06b6d4 50%, #10b981 100%);
            background-size: 200% 200%;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            animation: gradientShift 3s ease infinite;
        }
        
        @keyframes gradientShift {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        
        /* Mobile responsiveness */
        @media (max-width: 768px) {
            .movie-header h1 {
                font-size: 2.2rem;
            }
            
            .movie-header {
                padding: 2rem 1.5rem;
                margin-bottom: 2rem;
            }
            
            .movie-grid {
                grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
                gap: 1.5rem;
                padding: 1rem;
            }
            
            .movie-card {
                padding: 1.5rem;
                margin: 0.5rem;
            }
            
            .stButton > button {
                padding: 0.875rem 1.5rem;
                font-size: 0.95rem;
            }
        }
        
        /* Ultra-wide screen optimizations */
        @media (min-width: 1920px) {
            .movie-grid {
                grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
                gap: 2.5rem;
            }
            
            .movie-header h1 {
                font-size: 3.5rem;
            }
        }
    </style>
    """, unsafe_allow_html=True)