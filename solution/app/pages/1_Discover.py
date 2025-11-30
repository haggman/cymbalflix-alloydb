"""
🔮 CymbalFlix Discover - Semantic Search Page

This page demonstrates AlloyDB's most powerful AI feature: semantic search
using vector embeddings and the ScaNN index.

How it works:
1. Your natural language query is converted to a 3072-dimensional vector
   using Gemini's embedding model (called directly in SQL!)
2. AlloyDB uses the ScaNN index to find movies with similar vectors
3. Results are ranked by cosine similarity (higher = more relevant)

The magic happens in queries.py - check out search_movies_semantic()!
"""

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from utils import search_movies_semantic, is_configured

# -----------------------------------------------------------------------------
# Page Configuration
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Discover - CymbalFlix",
    page_icon="🔮",
    layout="wide",
)

# -----------------------------------------------------------------------------
# Header
# -----------------------------------------------------------------------------
st.title("🔮 Discover Movies")
st.markdown("""
**Semantic search** - Find movies by meaning, not just keywords.

Describe what you're looking for in natural language, and AlloyDB will find 
movies that match the *concept*, even if your exact words don't appear in the description.
""")

# -----------------------------------------------------------------------------
# Search Input
# -----------------------------------------------------------------------------
st.markdown("---")

# Example queries for inspiration
example_queries = [
    "A heartwarming story about unlikely friendship",
    "Mind-bending sci-fi with plot twists",
    "Dark thriller with psychological tension",
    "Feel-good comedy for a rainy day",
    "Epic adventure in a fantasy world",
    "Romantic drama set in Europe",
    "Action movie with car chases",
    "Documentary about nature and wildlife",
]

col1, col2 = st.columns([3, 1])

with col1:
    query = st.text_input(
        "What kind of movie are you looking for?",
        placeholder="e.g., A heartwarming story about unlikely friendship",
    )

with col2:
    st.markdown("<br>", unsafe_allow_html=True)  # Spacing
    search_clicked = st.button("🔮 Discover", type="primary", use_container_width=True)

# Show example queries - clicking one runs that search immediately
with st.expander("💡 Need inspiration? Try these example searches"):
    cols = st.columns(2)
    for i, example in enumerate(example_queries):
        with cols[i % 2]:
            if st.button(example, key=f"example_{i}", use_container_width=True):
                # Store the example to search and trigger search
                st.session_state.example_search = example

# Determine what to search: user input OR clicked example
search_query = None
if st.session_state.get("example_search"):
    search_query = st.session_state.example_search
    del st.session_state.example_search  # Clear after using
elif query and (search_clicked or query != st.session_state.get("last_query", "")):
    search_query = query
# -----------------------------------------------------------------------------
# Search Results
# -----------------------------------------------------------------------------
if search_query:
    if not is_configured():
        st.error("⚠️ Database not configured. Please set up your connection first.")
    else:
        with st.spinner("🔮 Searching with AI..."):
            try:
                results = search_movies_semantic(search_query, limit=12)
                
                st.markdown("---")
                st.subheader(f"Found {len(results)} movies for: _{search_query}_")
                
                if not results:
                    st.info("No movies found. Try a different search query.")
                else:
                    # Display results in a grid
                    for i in range(0, len(results), 2):
                        cols = st.columns(2)
                        
                        for j, col in enumerate(cols):
                            if i + j < len(results):
                                movie = results[i + j]
                                
                                with col:
                                    # Similarity score badge
                                    similarity_pct = movie["similarity"] * 100
                                    if similarity_pct >= 60:
                                        badge_color = "🟢"
                                    elif similarity_pct >= 50:
                                        badge_color = "🟡"
                                    else:
                                        badge_color = "🟠"
                                    
                                    st.markdown(f"""
                                    ### {movie['title']} ({movie['year'] or 'N/A'})
                                    
                                    {badge_color} **{similarity_pct:.1f}% match**
                                    
                                    **Genres:** {', '.join(movie['genres']) if movie['genres'] else 'N/A'}
                                    """)
                                    
                                    # Truncate summary for display
                                    summary = movie['summary'] or "No summary available."
                                    if len(summary) > 300:
                                        summary = summary[:300] + "..."
                                    
                                    st.markdown(f"_{summary}_")
                                    
                                    # View details button - sets session state and navigates
                                    if st.button(
                                        "🎬 View Details →", 
                                        key=f"discover_view_{movie['movie_id']}",
                                        use_container_width=True
                                    ):
                                        st.session_state.selected_movie_id = movie['movie_id']
                                        st.switch_page("pages/5_Movie.py")
                                    
                                    st.markdown("---")
                    
                    # Explain the technology
                    with st.expander("🔬 How does semantic search work?"):
                        st.markdown("""
                        **The Technology Behind Discover**
                        
                        1. **Embedding Generation**: Your query is converted to a 3072-dimensional 
                           vector using Gemini's `embedding()` function - called directly in SQL!
                        
                        2. **ScaNN Index**: AlloyDB's ScaNN (Scalable Nearest Neighbors) index 
                           efficiently finds similar vectors among millions in milliseconds.
                        
                        3. **Cosine Similarity**: Results are ranked by how similar their meaning 
                           is to your query (1.0 = identical, 0.0 = completely different).
                        
                        **The SQL that powers this:**
                        ```sql
                        SELECT 
                            title,
                            1 - (summary_embedding <=> query_embedding) AS similarity
                        FROM movies
                        ORDER BY summary_embedding <=> query_embedding
                        LIMIT 10;
                        ```
                        
                        The `<=>` operator calculates cosine distance between vectors.
                        The ScaNN index makes this query fast even with millions of movies!
                        """)
            
            except Exception as e:
                st.error("An error occurred during search.")
                with st.expander("Error Details"):
                    st.code(str(e))

# -----------------------------------------------------------------------------
# Sidebar - Search Tips
# -----------------------------------------------------------------------------
with st.sidebar:
    st.subheader("🎯 Search Tips")
    st.markdown("""
    **Be descriptive!** The more context you provide, the better the results.
    
    ✅ **Good queries:**
    - "A story about overcoming adversity and finding hope"
    - "Funny movie about a group of friends on an adventure"
    - "Dark mystery with an unexpected ending"
    
    ❌ **Less effective:**
    - "Good movie"
    - "Action"
    - "Tom Hanks" (use keyword search for names)
    
    ---
    
    **Pro tip:** Semantic search understands concepts! 
    Searching for "automobile chase" will find movies about car chases 
    even if they use the word "car" instead of "automobile".
    """)
    
    st.markdown("---")
    st.page_link("pages/3_Search.py", label="Try Keyword Search →", icon="🔍")