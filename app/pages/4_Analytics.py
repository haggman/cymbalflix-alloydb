"""
📈 CymbalFlix Discover - Analytics Dashboard

This page demonstrates AlloyDB's columnar engine capabilities.
The columnar engine accelerates analytical queries by up to 100x
by storing data in a column-oriented format optimized for aggregations.

Analytics shown:
- Top rated movies (with minimum rating threshold)
- Genre distribution
- Ratings over time
- Average ratings by genre
- Movies by decade

All queries run on LIVE data - no ETL or separate data warehouse needed!
This is HTAP (Hybrid Transactional/Analytical Processing) in action.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

from utils import get_analytics_data, is_configured

# -----------------------------------------------------------------------------
# Page Configuration
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Analytics - CymbalFlix",
    page_icon="📈",
    layout="wide",
)

# -----------------------------------------------------------------------------
# Header
# -----------------------------------------------------------------------------
st.title("📈 Analytics Dashboard")
st.markdown("""
Explore trends and patterns in our movie database.

These analytics run on **live transactional data** using AlloyDB's columnar engine - 
no separate data warehouse or ETL pipeline needed!
""")

# -----------------------------------------------------------------------------
# Load Analytics Data
# -----------------------------------------------------------------------------
if not is_configured():
    st.error("⚠️ Database not configured. Please set up your connection first.")
else:
    try:
        with st.spinner("Loading analytics... (powered by the columnar engine)"):
            analytics = get_analytics_data()
        
        # -----------------------------------------------------------------
        # Row 1: Top Movies and Genre Distribution
        # -----------------------------------------------------------------
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🏆 Top Rated Movies")
            st.caption("Minimum 50 ratings for statistical significance")
            
            top_movies = analytics.get("top_movies", [])
            if top_movies:
                df = pd.DataFrame(top_movies)
                
                # Create a horizontal bar chart
                fig = px.bar(
                    df,
                    x="avg_rating",
                    y="title",
                    orientation="h",
                    color="avg_rating",
                    color_continuous_scale="Viridis",
                    labels={"avg_rating": "Average Rating", "title": ""},
                    hover_data=["year", "rating_count"],
                )
                fig.update_layout(
                    yaxis=dict(autorange="reversed"),
                    showlegend=False,
                    height=400,
                    margin=dict(l=0, r=0, t=10, b=0),
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No rating data available")
        
        with col2:
            st.subheader("🎭 Genre Distribution")
            st.caption("Number of movies per genre")
            
            genre_dist = analytics.get("genre_distribution", [])
            if genre_dist:
                df = pd.DataFrame(genre_dist)
                
                fig = px.pie(
                    df,
                    values="count",
                    names="genre",
                    hole=0.4,
                    color_discrete_sequence=px.colors.qualitative.Set3,
                )
                fig.update_traces(textposition="inside", textinfo="percent+label")
                fig.update_layout(
                    showlegend=False,
                    height=400,
                    margin=dict(l=0, r=0, t=10, b=0),
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No genre data available")
        
        # -----------------------------------------------------------------
        # Row 2: Ratings Over Time and By Genre
        # -----------------------------------------------------------------
        st.markdown("---")
        col3, col4 = st.columns(2)
        
        with col3:
            st.subheader("📅 Ratings Over Time")
            st.caption("Rating activity by year")
            
            ratings_time = analytics.get("ratings_by_year", [])
            if ratings_time:
                df = pd.DataFrame(ratings_time)
                
                fig = go.Figure()
                
                # Add bar chart for count
                fig.add_trace(go.Bar(
                    x=df["year"],
                    y=df["count"],
                    name="Number of Ratings",
                    marker_color="lightblue",
                    yaxis="y",
                ))
                
                # Add line chart for average rating
                fig.add_trace(go.Scatter(
                    x=df["year"],
                    y=df["avg_rating"],
                    name="Average Rating",
                    mode="lines+markers",
                    line=dict(color="red", width=2),
                    yaxis="y2",
                ))
                
                fig.update_layout(
                    yaxis=dict(title="Number of Ratings", side="left"),
                    yaxis2=dict(title="Average Rating", side="right", overlaying="y", range=[0, 5]),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02),
                    height=350,
                    margin=dict(l=0, r=0, t=30, b=0),
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No time series data available")
        
        with col4:
            st.subheader("⭐ Average Rating by Genre")
            st.caption("Which genres rate highest?")
            
            genre_ratings = analytics.get("avg_rating_by_genre", [])
            if genre_ratings:
                df = pd.DataFrame(genre_ratings)
                
                fig = px.bar(
                    df,
                    x="genre",
                    y="avg_rating",
                    color="avg_rating",
                    color_continuous_scale="RdYlGn",
                    labels={"avg_rating": "Average Rating", "genre": ""},
                    hover_data=["rating_count"],
                )
                fig.update_layout(
                    xaxis_tickangle=-45,
                    showlegend=False,
                    height=350,
                    margin=dict(l=0, r=0, t=10, b=100),
                )
                # Add reference line at overall average
                overall_avg = sum(g["avg_rating"] * g["rating_count"] for g in genre_ratings) / sum(g["rating_count"] for g in genre_ratings)
                fig.add_hline(y=overall_avg, line_dash="dash", line_color="gray", 
                             annotation_text=f"Overall Avg: {overall_avg:.2f}")
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No genre rating data available")
        
        # -----------------------------------------------------------------
        # Row 3: Movies by Decade
        # -----------------------------------------------------------------
        st.markdown("---")
        st.subheader("📆 Movies by Decade")
        st.caption("Distribution of movies across decades")
        
        decade_data = analytics.get("movies_by_decade", [])
        if decade_data:
            df = pd.DataFrame(decade_data)
            
            fig = px.bar(
                df,
                x="decade",
                y="count",
                color="count",
                color_continuous_scale="Blues",
                labels={"count": "Number of Movies", "decade": "Decade"},
            )
            fig.update_layout(
                showlegend=False,
                height=300,
                margin=dict(l=0, r=0, t=10, b=0),
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # -----------------------------------------------------------------
        # Technical Note
        # -----------------------------------------------------------------
        st.markdown("---")
        with st.expander("🔬 How does AlloyDB make this fast?"):
            st.markdown("""
            **The Columnar Engine**
            
            Traditional databases store data row-by-row. When you run an aggregation 
            like `AVG(rating)`, the database must read entire rows even though it only 
            needs one column.
            
            AlloyDB's columnar engine stores popular columns separately, so analytical 
            queries only read the data they need. This can be **up to 100x faster** for 
            aggregations!
            
            **HTAP = No ETL Required**
            
            Traditional approach:
            ```
            Operational DB → ETL Pipeline → Data Warehouse → Analytics
            ```
            
            With AlloyDB:
            ```
            AlloyDB (OLTP + OLAP in one database) → Analytics
            ```
            
            The columnar engine runs on the same data as your transactions - 
            no copying, no syncing, no staleness.
            
            **Key Benefits:**
            - Real-time analytics on live data
            - Simpler architecture (one database instead of two + pipeline)
            - Reduced costs and complexity
            - No data synchronization delays
            """)
    
    except Exception as e:
        st.error("An error occurred while loading analytics.")
        with st.expander("Error Details"):
            st.code(str(e))

# -----------------------------------------------------------------------------
# Sidebar
# -----------------------------------------------------------------------------
with st.sidebar:
    st.subheader("📊 About This Dashboard")
    st.markdown("""
    All analytics queries run on **live transactional data**.
    
    **What powers this:**
    - AlloyDB's columnar engine
    - Automatic query optimization
    - In-memory column caching
    
    **Try it yourself:**
    Add a new rating through the app, then refresh this page to see it reflected in the analytics!
    """)
    
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.rerun()
