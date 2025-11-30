"""
📚 CymbalFlix Discover - Browse Page

Browse movies with traditional filters: genre, year range, and minimum rating.

This page demonstrates:
- Standard relational queries with multiple filter conditions
- Aggregations (average ratings) - accelerated by the columnar engine
- Pagination for large result sets
- Dynamic query building based on user selections
"""

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from utils import browse_movies, get_genres, is_configured

# -----------------------------------------------------------------------------
# Page Configuration
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Browse - CymbalFlix",
    page_icon="📚",
    layout="wide",
)

# -----------------------------------------------------------------------------
# Header
# -----------------------------------------------------------------------------
st.title("📚 Browse Movies")
st.markdown("""
Filter and explore our catalog of nearly 10,000 movies.
Use the filters to narrow down by genre, release year, or minimum rating.
""")

# -----------------------------------------------------------------------------
# Filters in Sidebar
# -----------------------------------------------------------------------------
with st.sidebar:
    st.subheader("🎛️ Filters")
    
    # Genre filter
    try:
        genres = get_genres()
        genre_options = {g["genre_name"]: g["genre_id"] for g in genres}
        genre_options = {"All Genres": None, **genre_options}
        
        selected_genre_name = st.selectbox(
            "Genre",
            options=list(genre_options.keys()),
            index=0,
        )
        selected_genre_id = genre_options[selected_genre_name]
    except Exception:
        st.warning("Unable to load genres")
        selected_genre_id = None
    
    st.markdown("---")
    
    # Year range filter
    st.markdown("**Release Year**")
    year_range = st.slider(
        "Year Range",
        min_value=1900,
        max_value=2020,
        value=(1980, 2018),
        label_visibility="collapsed",
    )
    year_min, year_max = year_range
    
    st.markdown("---")
    
    # Rating filter
    rating_min = st.slider(
        "Minimum Average Rating",
        min_value=0.0,
        max_value=5.0,
        value=0.0,
        step=0.5,
    )
    if rating_min == 0.0:
        rating_min = None  # No filter
    
    st.markdown("---")
    
    # Results per page
    results_per_page = st.selectbox(
        "Results per page",
        options=[10, 20, 50],
        index=1,
    )
    
    st.markdown("---")
    
    # Clear filters button
    if st.button("Clear Filters", use_container_width=True):
        st.session_state.page = 0
        st.rerun()

# -----------------------------------------------------------------------------
# Pagination State
# -----------------------------------------------------------------------------
if "page" not in st.session_state:
    st.session_state.page = 0

# Reset to page 0 when filters change
filter_key = f"{selected_genre_id}-{year_min}-{year_max}-{rating_min}"
if st.session_state.get("last_filter_key") != filter_key:
    st.session_state.page = 0
    st.session_state.last_filter_key = filter_key

# -----------------------------------------------------------------------------
# Load and Display Movies
# -----------------------------------------------------------------------------
if not is_configured():
    st.error("⚠️ Database not configured. Please set up your connection first.")
else:
    try:
        offset = st.session_state.page * results_per_page
        
        with st.spinner("Loading movies..."):
            result = browse_movies(
                genre_id=selected_genre_id,
                year_min=year_min,
                year_max=year_max,
                rating_min=rating_min,
                limit=results_per_page,
                offset=offset,
            )
        
        movies = result["movies"]
        total_count = result["total_count"]
        total_pages = (total_count + results_per_page - 1) // results_per_page
        
        # Show current filter summary
        filter_summary = []
        if selected_genre_name != "All Genres":
            filter_summary.append(f"Genre: {selected_genre_name}")
        filter_summary.append(f"Years: {year_min}-{year_max}")
        if rating_min:
            filter_summary.append(f"Min Rating: {rating_min}⭐")
        
        st.markdown(f"**Filters:** {' | '.join(filter_summary)}")
        st.markdown(f"Showing {offset + 1}-{min(offset + results_per_page, total_count)} of {total_count:,} movies")
        
        st.markdown("---")
        
        if not movies:
            st.info("No movies found matching your filters. Try adjusting your criteria.")
        else:
            # Display movies in a grid
            for i in range(0, len(movies), 2):
                cols = st.columns(2)
                
                for j, col in enumerate(cols):
                    if i + j < len(movies):
                        movie = movies[i + j]
                        
                        with col:
                            # Rating display
                            rating = movie["avg_rating"]
                            rating_count = movie["rating_count"]
                            
                            if rating_count > 0:
                                stars = "⭐" * int(round(rating))
                                rating_display = f"{stars} {rating:.1f} ({rating_count:,} ratings)"
                            else:
                                rating_display = "No ratings yet"
                            
                            st.markdown(f"""
                            ### {movie['title']} ({movie['year'] or 'N/A'})
                            
                            {rating_display}
                            
                            **Genres:** {', '.join(movie['genres']) if movie['genres'] else 'N/A'}
                            """)
                            
                            # Truncate summary
                            summary = movie['summary'] or "No summary available."
                            if len(summary) > 250:
                                summary = summary[:250] + "..."
                            
                            st.markdown(f"_{summary}_")
                            
                            if st.button(
                                "🎬 View Details →", 
                                key=f"browse_view_{movie['movie_id']}",
                                use_container_width=True
                            ):
                                st.session_state.selected_movie_id = movie['movie_id']
                                st.switch_page("pages/5_Movie.py")
                            
                            st.markdown("---")
            
            # Pagination controls
            col1, col2, col3 = st.columns([1, 2, 1])
            
            with col1:
                if st.session_state.page > 0:
                    if st.button("← Previous"):
                        st.session_state.page -= 1
                        st.rerun()
            
            with col2:
                st.markdown(f"<center>Page {st.session_state.page + 1} of {total_pages}</center>", 
                           unsafe_allow_html=True)
            
            with col3:
                if st.session_state.page < total_pages - 1:
                    if st.button("Next →"):
                        st.session_state.page += 1
                        st.rerun()
    
    except Exception as e:
        st.error("An error occurred while loading movies.")
        with st.expander("Error Details"):
            st.code(str(e))
