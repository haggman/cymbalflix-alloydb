"""
🔍 CymbalFlix Discover - Keyword Search Page

Traditional keyword search through movie titles and summaries.

This page contrasts with the Discover (semantic search) page:
- Keyword: Finds "robot" only if that exact word appears
- Semantic: Finds movies ABOUT robots even if "robot" isn't mentioned

Use this when you:
- Know the exact movie title
- Want to search for specific names (actors, directors)
- Need precise string matching
"""

import re
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from utils import search_movies_keyword, is_configured

# -----------------------------------------------------------------------------
# Page Configuration
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Search - CymbalFlix",
    page_icon="🔍",
    layout="wide",
)

# -----------------------------------------------------------------------------
# Header
# -----------------------------------------------------------------------------
st.title("🔍 Keyword Search")
st.markdown("""
**Traditional search** - Find movies containing specific words or phrases.

Best for searching by title, actor names, or specific terms you know appear in the description.
""")

# -----------------------------------------------------------------------------
# Search Input
# -----------------------------------------------------------------------------
st.markdown("---")

col1, col2 = st.columns([3, 1])

with col1:
    query = st.text_input(
        "Search for movies",
        placeholder="e.g., Toy Story, time travel, Tom Hanks",
        key="keyword_query",
    )

with col2:
    st.markdown("<br>", unsafe_allow_html=True)
    search_clicked = st.button("🔍 Search", type="primary", use_container_width=True)

# Quick search suggestions
st.markdown("**Quick searches:**")
quick_searches = ["Star Wars", "romantic comedy", "thriller", "animation", "documentary"]
cols = st.columns(len(quick_searches))
for i, term in enumerate(quick_searches):
    with cols[i]:
        if st.button(term, key=f"quick_{i}", use_container_width=True):
            st.session_state.quick_search = term

# Determine what to search: user input OR clicked quick search
search_query = None
if st.session_state.get("quick_search"):
    search_query = st.session_state.quick_search
    del st.session_state.quick_search
elif query and (search_clicked or query != st.session_state.get("last_keyword_query", "")):
    search_query = query
    st.session_state.last_keyword_query = query

# -----------------------------------------------------------------------------
# Search Results
# -----------------------------------------------------------------------------
if search_query:
    
    if not is_configured():
        st.error("⚠️ Database not configured. Please set up your connection first.")
    else:
        with st.spinner("Searching..."):
            try:
                results = search_movies_keyword(search_query, limit=20)
                
                st.markdown("---")
                st.subheader(f"Found {len(results)} movies containing \"{search_query}\"")
                
                if not results:
                    st.info(f"No movies found containing \"{search_query}\". Try different keywords or use Semantic Search for concept-based searching.")
                    st.page_link("pages/1_Discover.py", label="Try Semantic Search →", icon="🔮")
                else:
                    for movie in results:
                        with st.container():
                            col1, col2 = st.columns([4, 1])
                            
                            with col1:
                                st.markdown(f"""
                                ### {movie['title']} ({movie['year'] or 'N/A'})
                                
                                **Genres:** {', '.join(movie['genres']) if movie['genres'] else 'N/A'}
                                """)
                                
                                summary = movie['summary'] or "No summary available."
                                
                                # Highlight search term in summary (simple approach)
                                if search_query.lower() in summary.lower():
                                    # Find and highlight (case-insensitive)
                                    pattern = re.compile(re.escape(search_query), re.IGNORECASE)
                                    summary_highlighted = pattern.sub(f"**{search_query}**", summary)
                                else:
                                    summary_highlighted = summary
                                
                                if len(summary_highlighted) > 400:
                                    summary_highlighted = summary_highlighted[:400] + "..."
                                
                                st.markdown(f"_{summary_highlighted}_")
                            
                            with col2:
                                if st.button(
                                    "Details →", 
                                    key=f"search_view_{movie['movie_id']}",
                                ):
                                    st.session_state.selected_movie_id = movie['movie_id']
                                    st.switch_page("pages/5_Movie.py")
                            
                            st.markdown("---")
                    
                    # Compare with semantic search
                    st.info(f"""
                    💡 **Tip:** Keyword search finds exact matches. If you're looking for movies 
                    *about* a concept rather than containing specific words, try **Semantic Search**!
                    """)
                    st.page_link("pages/1_Discover.py", label="Try Semantic Search →", icon="🔮")
            
            except Exception as e:
                st.error("An error occurred during search.")
                with st.expander("Error Details"):
                    st.code(str(e))

# -----------------------------------------------------------------------------
# Sidebar - Search Tips
# -----------------------------------------------------------------------------
with st.sidebar:
    st.subheader("🔍 Keyword vs Semantic")
    
    st.markdown("""
    **When to use Keyword Search:**
    - You know the movie title
    - Searching for specific names
    - Need exact phrase matching
    
    **When to use Semantic Search:**
    - Describing what you're in the mood for
    - Looking for similar themes/concepts
    - Don't know exact titles
    
    ---
    
    **Example Comparison:**
    
    *Query: "automobile chase"*
    
    🔍 **Keyword:** Only finds movies with "automobile chase" in the text
    
    🔮 **Semantic:** Finds car chase movies even if they use "car", "vehicle", or just describe the chase
    """)
    
    st.markdown("---")
    st.page_link("pages/1_Discover.py", label="Try Semantic Search →", icon="🔮")