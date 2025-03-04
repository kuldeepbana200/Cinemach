import streamlit as st
import pickle
import requests
from typing import Tuple, List
from functools import lru_cache
import time

API_KEY = '0b27a94ce84af2198e74f61045430715'
BASE_POSTER_URL = "https://image.tmdb.org/t/p/w500/"
DEFAULT_POSTER = "https://via.placeholder.com/500x750.png?text=No+Image"

def configure_page():
    st.set_page_config(
        page_title="CineMatch - AI Movie Recommender",
        page_icon="🎥",
        layout="centered",
        initial_sidebar_state="collapsed"
    )

@st.cache_data
def load_data():
    try:
        movies = pickle.load(open('movies.pkl', 'rb'))
        similarity = pickle.load(open('similarity.pkl', 'rb'))
        return movies, similarity
    except FileNotFoundError:
        st.error("Error: Data files missing. Please check movies.pkl and similarity.pkl.")
        return None, None
    except Exception as e:
        st.error(f"Unexpected error loading data: {str(e)}")
        return None, None

@lru_cache(maxsize=100)
def fetch_poster(movie_id: int) -> str:
    try:
        url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={API_KEY}&language=en-US"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        return BASE_POSTER_URL + data['poster_path'] if data.get('poster_path') else DEFAULT_POSTER
    except (requests.RequestException, ValueError) as e:
        return DEFAULT_POSTER

def recommend(movie: str, movies, similarity) -> Tuple[List[Tuple[int, str]], List[str]]:
    try:
        movie_index = movies[movies['title'] == movie].index[0]
        distances = similarity[movie_index]
        movies_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:11]
        
        recommendations = []
        posters = []
        
        for i in movies_list:
            movie_id = movies.iloc[i[0]]['movie_id']
            recommendations.append((movie_id, movies.iloc[i[0]]['title']))
            posters.append(fetch_poster(movie_id))
        
        return recommendations, posters
    except IndexError:
        st.error("Movie not found in the database.")
        return [], []
    except Exception as e:
        st.error(f"Error generating recommendations: {str(e)}")
        return [], []

def main():
    configure_page()
    
    st.markdown("""
        <style>
            .title-text { text-align: center; font-size: 28px; font-weight: bold; color: #F39C12; }
            .movie-box { text-align: center; font-size: 14px; margin-top: 5px; }
            .stButton>button { background-color: #3498DB; color: white; width: 100%; }
            .stButton>button:hover { background-color: #2980B9; }
        </style>
    """, unsafe_allow_html=True)
    
    movies, similarity = load_data()
    if movies is None or similarity is None:
        return
    
    st.markdown("<p class='title-text'>🎥 CineMatch - AI Movie Recommender</p>", unsafe_allow_html=True)
    st.write("Select a movie to discover similar recommendations powered by AI.")
    
    movie_options = ['-- Choose a Movie --'] + list(movies['title'].values)
    selected_movie = st.selectbox("Select a movie:", movie_options)
    
    if st.button("Find Similar Movies 🎬"):
        if selected_movie == '-- Choose a Movie --':
            st.warning("Please choose a movie to proceed!")
        else:
            with st.spinner("Finding the best matches for you..."):
                start_time = time.time()
                recommended_movies, posters = recommend(selected_movie, movies, similarity)
                
                if recommended_movies:
                    st.subheader("You might also like:")
                    cols = st.columns(5) + st.columns(5)
                    
                    for col, (movie, poster) in zip(cols, zip(recommended_movies, posters)):
                        with col:
                            st.image(poster, use_container_width=True)
                            st.markdown(f'<div class="movie-box"><b>{movie[1]}</b></div>', unsafe_allow_html=True)
                
                    st.success(f"Found recommendations in {time.time() - start_time:.2f} seconds!")
                else:
                    st.error("No recommendations available at the moment.")
    
    st.markdown("""
        ---
        <div style='text-align: center;'>Powered by <a href='https://www.themoviedb.org/' target='_blank'>TMDB</a></div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
