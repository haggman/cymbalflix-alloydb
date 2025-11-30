"""
🎬 CymbalFlix Discover - Home Page

Welcome to CymbalFlix Discover! This AI-powered movie discovery application
demonstrates AlloyDB's powerful features:

- Semantic Search: Find movies by meaning, not just keywords
- Real-Time Analytics: Aggregations on live data using the columnar engine
- Full PostgreSQL Compatibility: Standard drivers and familiar SQL patterns
- IAM Authentication: Secure, passwordless database access
"""

import streamlit as st
from dotenv import load_dotenv

# Load environment variables from .env file (for local development)
load_dotenv()

from utils import get_stats, test_connection, is_configured, get_config_status

# -----------------------------------------------------------------------------
# Page Configuration
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="CymbalFlix Discover",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------------------------------------------------------
# Sidebar - Connection Status
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## 🎬 CymbalFlix")
    st.caption("Discover your next favorite movie")
    st.markdown("---")
    
    # Show connection status
    st.subheader("🔌 Database Connection")
    
    if is_configured():
        config = get_config_status()
        with st.expander("Connection Details", expanded=False):
            st.code(f"""
Project: {config['project_id']}
Region: {config['region']}
Cluster: {config['cluster_id']}
Database: {config['db_name']}
User: {config['db_user']}
            """)
        
        # Test connection button
        if st.button("Test Connection", type="secondary"):
            with st.spinner("Connecting to AlloyDB..."):
                result = test_connection()
                if result["status"] == "connected":
                    st.success(f"✅ Connected to {result['database']}")
                    st.caption(f"User: {result['user']}")
                else:
                    st.error(f"❌ Connection failed")
                    st.caption(result.get("error", "Unknown error"))
    else:
        st.warning("⚠️ Database not configured")
        st.caption("Set environment variables in .env file")
        config = get_config_status()
        with st.expander("Missing Configuration"):
            for key, value in config.items():
                if value == "(not set)":
                    st.text(f"❌ {key}")

# -----------------------------------------------------------------------------
# Main Content
# -----------------------------------------------------------------------------
st.title("🎬 CymbalFlix Discover")
st.markdown("""
**AI-Powered Movie Discovery** built on AlloyDB

Find your next favorite movie using the power of semantic search, 
or explore our catalog of nearly 10,000 films with traditional filters.
""")

# -----------------------------------------------------------------------------
# Quick Stats
# -----------------------------------------------------------------------------
st.markdown("---")
st.subheader("📊 Quick Stats")

try:
    stats = get_stats()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🎬 Movies", f"{stats['movie_count']:,}")
    
    with col2:
        st.metric("⭐ Ratings", f"{stats['rating_count']:,}")
    
    with col3:
        st.metric("👥 Users", f"{stats['user_count']:,}")
    
    with col4:
        st.metric("🏷️ Genres", f"{stats['genre_count']:,}")

except Exception as e:
    st.error("Unable to load statistics. Please check your database connection.")
    with st.expander("Error Details"):
        st.code(str(e))

# -----------------------------------------------------------------------------
# Feature Cards
# -----------------------------------------------------------------------------
st.markdown("---")
st.subheader("🚀 Explore CymbalFlix")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    ### 🔮 Discover (Semantic Search)
    
    Use natural language to find movies by *meaning*, not just keywords.
    
    **Try searches like:**
    - "A heartwarming story about unlikely friendship"
    - "Sci-fi with mind-bending plot twists"
    - "Feel-good comedy for a rainy day"
    
    *Powered by AlloyDB's ScaNN vector index and Gemini embeddings*
    """)
    st.page_link("pages/1_Discover.py", label="Open Discover →", icon="🔮")

with col2:
    st.markdown("""
    ### 🔍 Search (Keyword)
    
    Traditional search through movie titles and summaries.
    
    **Great for:**
    - Finding a specific movie by name
    - Searching for actor or director mentions
    - Quick lookups when you know what you want
    
    *Standard PostgreSQL text search capabilities*
    """)
    st.page_link("pages/3_Search.py", label="Open Search →", icon="🔍")

col3, col4 = st.columns(2)

with col3:
    st.markdown("""
    ### 📚 Browse
    
    Filter movies by genre, year, and rating.
    
    **Features:**
    - Filter by any of 19 genres
    - Year range slider (1902-2018)
    - Minimum rating threshold
    - Paginated results
    
    *Relational queries with aggregations*
    """)
    st.page_link("pages/2_Browse.py", label="Open Browse →", icon="📚")

with col4:
    st.markdown("""
    ### 📈 Analytics
    
    Explore trends and patterns in our movie database.
    
    **Dashboards:**
    - Top rated movies
    - Genre distribution
    - Ratings over time
    - Average ratings by genre
    
    *Powered by AlloyDB's columnar engine for fast analytics*
    """)
    st.page_link("pages/4_Analytics.py", label="Open Analytics →", icon="📈")

# -----------------------------------------------------------------------------
# Technology Section
# -----------------------------------------------------------------------------
st.markdown("---")
st.subheader("🛠️ Built with AlloyDB")

st.markdown("""
This application showcases AlloyDB's key capabilities:

| Feature | How It's Used |
|---------|---------------|
| **Vector Search (ScaNN)** | Semantic movie search using 3072-dimensional embeddings |
| **Columnar Engine** | Fast analytics on 100K+ ratings |
| **PostgreSQL Compatibility** | Standard Python connector and SQL patterns |
| **IAM Authentication** | Secure, passwordless database access |
| **Vertex AI Integration** | In-database embedding generation |

**Data Source:** [MovieLens Dataset](https://grouplens.org/datasets/movielens/) with AI-generated summaries
""")

# -----------------------------------------------------------------------------
# Footer
# -----------------------------------------------------------------------------
st.markdown("---")
st.caption("""
🎬 CymbalFlix Discover | Built with Streamlit and AlloyDB | 
Part of the "AlloyDB: PostgreSQL Evolved" lab
""")
