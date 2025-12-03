"""
🎬 CymbalFlix Discover - Movie Detail Page

View complete details for a single movie and add your own rating.

This page demonstrates:
- Detailed record retrieval with joins (genres, ratings, links)
- Transactional operations (adding/updating ratings)
- External links to IMDb and TMDb
"""

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from utils import get_movie_details, add_rating, is_configured

# -----------------------------------------------------------------------------
# Page Configuration
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Movie Details - CymbalFlix",
    page_icon="🎬",
    layout="wide",
)

# -----------------------------------------------------------------------------
# Get Movie ID from Session State
# -----------------------------------------------------------------------------
# Movie ID is passed via session state from other pages
movie_id = st.session_state.get("selected_movie_id")

if not movie_id:
    st.title("🎬 Movie Details")
    st.warning("No movie selected. Please select a movie from the search results.")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.page_link("pages/1_Discover.py", label="🔮 Discover Movies", icon="🔮")
    with col2:
        st.page_link("pages/2_Browse.py", label="📚 Browse Catalog", icon="📚")
    with col3:
        st.page_link("pages/3_Search.py", label="🔍 Search Movies", icon="🔍")

elif not is_configured():
    st.title("🎬 Movie Details")
    st.error("⚠️ Database not configured. Please set up your connection first.")

else:
    # Load movie details
    try:
        movie = get_movie_details(movie_id)
        
        if not movie:
            st.error(f"Movie with ID {movie_id} not found.")
            st.stop()
        
        # ---------------------------------------------------------------------
        # Movie Header
        # ---------------------------------------------------------------------
        st.title(f"🎬 {movie['title']}")
        
        # Year and genres
        meta_parts = []
        if movie['year']:
            meta_parts.append(f"**{movie['year']}**")
        if movie['genres']:
            meta_parts.append(" • ".join(movie['genres']))
        
        if meta_parts:
            st.markdown(" | ".join(meta_parts))
        
        st.markdown("---")
        
        # ---------------------------------------------------------------------
        # Main Content
        # ---------------------------------------------------------------------
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Summary
            st.subheader("📖 Summary")
            st.markdown(movie['summary'] or "_No summary available._")
            
            # Genres as tags
            if movie['genres']:
                st.markdown("**Genres:**")
                genre_html = " ".join([
                    f'<span style="background-color: #262730; padding: 4px 12px; border-radius: 16px; margin-right: 8px;">{g}</span>'
                    for g in movie['genres']
                ])
                st.markdown(genre_html, unsafe_allow_html=True)
        
        with col2:
            # Rating card
            st.subheader("⭐ Rating")
            
            if movie['rating_count'] > 0:
                st.metric(
                    label="Average Rating",
                    value=f"{movie['avg_rating']:.1f} / 5.0",
                    delta=f"{movie['rating_count']:,} ratings",
                )
                
                # Star visualization
                full_stars = int(movie['avg_rating'])
                half_star = movie['avg_rating'] - full_stars >= 0.5
                stars = "⭐" * full_stars + ("½" if half_star else "")
                st.markdown(f"### {stars}")
            else:
                st.info("No ratings yet. Be the first to rate!")
            
            st.markdown("---")
            
            # External links
            st.subheader("🔗 External Links")
            
            if movie['imdb_url']:
                st.markdown(f"[🎬 View on IMDb]({movie['imdb_url']})")
            
            if not movie['imdb_url']:
                st.caption("No external links available")
        
        # ---------------------------------------------------------------------
        # Add Rating Section
        # ---------------------------------------------------------------------
        st.markdown("---")
        st.subheader("📝 Rate This Movie")
        
        with st.form("rating_form"):
            col1, col2, col3 = st.columns([1, 1, 2])
            
            with col1:
                # User selection (in real app, this would come from authentication)
                user_id = st.selectbox(
                    "Select User",
                    options=list(range(1, 611)),  # Users 1-610 from dataset
                    index=0,
                    help="Select a user ID (1-610)",
                )
            
            with col2:
                rating = st.select_slider(
                    "Your Rating",
                    options=[0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0],
                    value=3.0,
                    format_func=lambda x: f"{'⭐' * int(x)}{'½' if x % 1 else ''} ({x})",
                )
            
            with col3:
                st.markdown("<br>", unsafe_allow_html=True)
                submitted = st.form_submit_button("Submit Rating", type="primary")
            
            if submitted:
                try:
                    result = add_rating(user_id, movie_id, rating)
                    
                    if result["success"]:
                        if result["action"] == "created":
                            st.success(f"✅ Rating added! You rated this movie {rating}/5.0")
                        else:
                            st.success(f"✅ Rating updated! New rating: {rating}/5.0")
                        st.rerun()
                    else:
                        st.error("Failed to add rating")
                except Exception as e:
                    st.error(f"Error adding rating: {e}")
        
        st.caption("""
        **Note:** In a production app, user authentication would handle user IDs automatically.
        For this demo, select any user ID from 1-610 (existing users from the dataset).
        """)
        
        # ---------------------------------------------------------------------
        # Navigation
        # ---------------------------------------------------------------------
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.page_link("pages/1_Discover.py", label="← Back to Discover", icon="🔮")
        
        with col2:
            st.page_link("pages/2_Browse.py", label="← Browse More", icon="📚")
        
        with col3:
            st.page_link("pages/3_Search.py", label="← Search Movies", icon="🔍")
    
    except Exception as e:
        st.error("An error occurred while loading movie details.")
        with st.expander("Error Details"):
            st.code(str(e))

# -----------------------------------------------------------------------------
# Sidebar
# -----------------------------------------------------------------------------
with st.sidebar:
    st.subheader("🎬 Movie Details")
    st.markdown("""
    This page shows complete information for a single movie, including:
    
    - Full summary
    - Genre tags
    - Average rating and count
    - Links to IMDb and TMDb
    - Rating submission form
    
    ---
    
    **Transactional Operations**
    
    Adding a rating demonstrates AlloyDB handling transactional writes:
    - Checks for existing rating
    - Uses upsert logic (update or insert)
    - Updates run on the same database serving analytics
    
    This is HTAP in action - transactions and analytics, together!
    """)
