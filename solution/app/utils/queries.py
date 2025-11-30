"""
CymbalFlix Discover - Database Queries

This module contains all the SQL queries and data access functions for
the CymbalFlix application. This is where AlloyDB's powerful features
come to life:

- Semantic Search: Vector similarity using ScaNN index
- Full-Text Search: Traditional keyword matching  
- Analytics: Aggregations powered by the columnar engine
- Transactional: User ratings and watchlist operations

Each function handles its own connection management and returns
Python-native data structures (dicts, lists) ready for the UI.
"""

import sqlalchemy
from sqlalchemy import text
from typing import List, Dict, Optional, Any
from .database import get_db_connection


# =============================================================================
# QUICK STATS (Home Page)
# =============================================================================

def get_stats() -> Dict[str, int]:
    """
    Get quick statistics for the home page.
    
    Returns counts of movies, ratings, users, and genres.
    These queries are simple but demonstrate AlloyDB handling
    aggregations efficiently.
    
    Returns:
        dict with movie_count, rating_count, user_count, genre_count
    """
    with get_db_connection() as conn:
        stats = {}
        
        # Movie count
        result = conn.execute(text("SELECT COUNT(*) FROM movies"))
        stats["movie_count"] = result.scalar()
        
        # Rating count  
        result = conn.execute(text("SELECT COUNT(*) FROM ratings"))
        stats["rating_count"] = result.scalar()
        
        # User count
        result = conn.execute(text("SELECT COUNT(*) FROM users"))
        stats["user_count"] = result.scalar()
        
        # Genre count
        result = conn.execute(text("SELECT COUNT(*) FROM genres"))
        stats["genre_count"] = result.scalar()
        
        return stats


# =============================================================================
# SEMANTIC SEARCH (Discover Page)
# =============================================================================

def search_movies_semantic(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Search for movies using semantic similarity (vector search).
    
    This is where AlloyDB's AI capabilities shine! The query:
    1. Converts the user's natural language query into a vector embedding
       using Gemini's embedding model (called directly in SQL!)
    2. Finds movies with similar embeddings using cosine distance
    3. The ScaNN index makes this lightning fast even with millions of vectors
    
    Example searches that work great:
    - "A heartwarming story about unlikely friendship"
    - "Sci-fi movie with time travel paradoxes"
    - "Dark thriller with plot twists"
    
    Args:
        query: Natural language search query
        limit: Maximum number of results (default 10)
        
    Returns:
        List of movies with similarity scores
    """
    # The magic: embedding() function converts text to vectors RIGHT IN SQL
    # The <=> operator calculates cosine distance (lower = more similar)
    # We convert distance to similarity (1 - distance) for intuitive scores
    
    sql = text("""
        WITH query_embedding AS (
            SELECT embedding(
                'gemini-embedding-001',
                :query
            )::vector AS embedding
        )
        SELECT 
            m.movie_id,
            m.title,
            m.year,
            m.summary,
            ROUND((1 - (m.summary_embedding <=> q.embedding))::numeric, 3) AS similarity,
            ARRAY_AGG(DISTINCT g.genre_name ORDER BY g.genre_name) AS genres
        FROM movies m
        CROSS JOIN query_embedding q
        LEFT JOIN movie_genres mg ON m.movie_id = mg.movie_id
        LEFT JOIN genres g ON mg.genre_id = g.genre_id
        WHERE m.summary_embedding IS NOT NULL
        GROUP BY m.movie_id, m.title, m.year, m.summary, m.summary_embedding, q.embedding
        ORDER BY m.summary_embedding <=> q.embedding
        LIMIT :limit
    """)
    
    with get_db_connection() as conn:
        result = conn.execute(sql, {"query": query, "limit": limit})
        
        movies = []
        for row in result:
            movies.append({
                "movie_id": row.movie_id,
                "title": row.title,
                "year": row.year,
                "summary": row.summary,
                "similarity": float(row.similarity) if row.similarity else 0,
                "genres": row.genres if row.genres and row.genres[0] else [],
            })
        
        return movies


# =============================================================================
# KEYWORD SEARCH (Search Page)
# =============================================================================

def search_movies_keyword(query: str, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Search for movies using traditional keyword matching.
    
    This demonstrates standard PostgreSQL text search capabilities.
    Searches both title and summary using case-insensitive matching.
    
    Contrast this with semantic search:
    - Keyword: Finds "robot" only if the word appears
    - Semantic: Finds movies ABOUT robots even if the word isn't used
    
    Args:
        query: Search keywords
        limit: Maximum number of results
        
    Returns:
        List of matching movies
    """
    # Using ILIKE for case-insensitive matching
    # In production, you might use PostgreSQL's full-text search (tsvector/tsquery)
    
    sql = text("""
        SELECT 
            m.movie_id,
            m.title,
            m.year,
            m.summary,
            ARRAY_AGG(DISTINCT g.genre_name ORDER BY g.genre_name) AS genres
        FROM movies m
        LEFT JOIN movie_genres mg ON m.movie_id = mg.movie_id
        LEFT JOIN genres g ON mg.genre_id = g.genre_id
        WHERE 
            m.title ILIKE :pattern
            OR m.summary ILIKE :pattern
        GROUP BY m.movie_id, m.title, m.year, m.summary
        ORDER BY 
            CASE WHEN m.title ILIKE :pattern THEN 0 ELSE 1 END,
            m.title
        LIMIT :limit
    """)
    
    pattern = f"%{query}%"
    
    with get_db_connection() as conn:
        result = conn.execute(sql, {"pattern": pattern, "limit": limit})
        
        movies = []
        for row in result:
            movies.append({
                "movie_id": row.movie_id,
                "title": row.title,
                "year": row.year,
                "summary": row.summary,
                "genres": row.genres if row.genres and row.genres[0] else [],
            })
        
        return movies


# =============================================================================
# BROWSE & FILTER (Browse Page)
# =============================================================================

def get_genres() -> List[Dict[str, Any]]:
    """
    Get all genres for the filter dropdown.
    
    Returns:
        List of genres with id and name
    """
    sql = text("""
        SELECT genre_id, genre_name
        FROM genres
        ORDER BY genre_name
    """)
    
    with get_db_connection() as conn:
        result = conn.execute(sql)
        return [{"genre_id": row.genre_id, "genre_name": row.genre_name} for row in result]


def browse_movies(
    genre_id: Optional[int] = None,
    year_min: Optional[int] = None,
    year_max: Optional[int] = None,
    rating_min: Optional[float] = None,
    limit: int = 20,
    offset: int = 0
) -> Dict[str, Any]:
    """
    Browse movies with optional filters.
    
    This query demonstrates combining multiple filter conditions
    with aggregations (average rating). The columnar engine helps
    make the rating calculations fast.
    
    Args:
        genre_id: Filter by genre (optional)
        year_min: Minimum release year (optional)
        year_max: Maximum release year (optional)  
        rating_min: Minimum average rating (optional)
        limit: Results per page
        offset: Pagination offset
        
    Returns:
        Dict with movies list and total_count for pagination
    """
    # Build the query dynamically based on filters
    where_clauses = ["1=1"]  # Always true, simplifies building AND clauses
    params = {"limit": limit, "offset": offset}
    
    if genre_id:
        where_clauses.append("mg.genre_id = :genre_id")
        params["genre_id"] = genre_id
    
    if year_min:
        where_clauses.append("m.year >= :year_min")
        params["year_min"] = year_min
    
    if year_max:
        where_clauses.append("m.year <= :year_max")
        params["year_max"] = year_max
    
    where_sql = " AND ".join(where_clauses)
    
    # Main query with rating aggregation
    if rating_min:
        # When filtering by rating, we need to calculate it first
        sql = text(f"""
            WITH movie_ratings AS (
                SELECT 
                    m.movie_id,
                    m.title,
                    m.year,
                    m.summary,
                    COALESCE(AVG(r.rating), 0) AS avg_rating,
                    COUNT(r.rating_id) AS rating_count
                FROM movies m
                LEFT JOIN movie_genres mg ON m.movie_id = mg.movie_id
                LEFT JOIN ratings r ON m.movie_id = r.movie_id
                WHERE {where_sql}
                GROUP BY m.movie_id, m.title, m.year, m.summary
                HAVING COALESCE(AVG(r.rating), 0) >= :rating_min
            )
            SELECT 
                mr.*,
                ARRAY_AGG(DISTINCT g.genre_name ORDER BY g.genre_name) AS genres
            FROM movie_ratings mr
            LEFT JOIN movie_genres mg ON mr.movie_id = mg.movie_id
            LEFT JOIN genres g ON mg.genre_id = g.genre_id
            GROUP BY mr.movie_id, mr.title, mr.year, mr.summary, mr.avg_rating, mr.rating_count
            ORDER BY mr.avg_rating DESC, mr.rating_count DESC
            LIMIT :limit OFFSET :offset
        """)
        params["rating_min"] = rating_min
    else:
        sql = text(f"""
            SELECT 
                m.movie_id,
                m.title,
                m.year,
                m.summary,
                COALESCE(AVG(r.rating), 0) AS avg_rating,
                COUNT(r.rating_id) AS rating_count,
                ARRAY_AGG(DISTINCT g.genre_name ORDER BY g.genre_name) AS genres
            FROM movies m
            LEFT JOIN movie_genres mg ON m.movie_id = mg.movie_id
            LEFT JOIN genres g ON mg.genre_id = g.genre_id
            LEFT JOIN ratings r ON m.movie_id = r.movie_id
            WHERE {where_sql}
            GROUP BY m.movie_id, m.title, m.year, m.summary
            ORDER BY avg_rating DESC, rating_count DESC
            LIMIT :limit OFFSET :offset
        """)
    
    # Count query for pagination
    count_sql = text(f"""
        SELECT COUNT(DISTINCT m.movie_id)
        FROM movies m
        LEFT JOIN movie_genres mg ON m.movie_id = mg.movie_id
        WHERE {where_sql}
    """)
    
    with get_db_connection() as conn:
        # Get movies
        result = conn.execute(sql, params)
        movies = []
        for row in result:
            movies.append({
                "movie_id": row.movie_id,
                "title": row.title,
                "year": row.year,
                "summary": row.summary,
                "avg_rating": round(float(row.avg_rating), 2) if row.avg_rating else 0,
                "rating_count": row.rating_count,
                "genres": row.genres if row.genres and row.genres[0] else [],
            })
        
        # Get total count (without rating filter for simplicity)
        count_params = {k: v for k, v in params.items() if k not in ["limit", "offset", "rating_min"]}
        total_result = conn.execute(count_sql, count_params)
        total_count = total_result.scalar()
        
        return {
            "movies": movies,
            "total_count": total_count,
        }


# =============================================================================
# MOVIE DETAILS (Detail Page)
# =============================================================================

def get_movie_details(movie_id: int) -> Optional[Dict[str, Any]]:
    """
    Get complete details for a single movie.
    
    Includes genres, average rating, rating count, and external links.
    
    Args:
        movie_id: The movie's ID
        
    Returns:
        Movie details dict or None if not found
    """
    sql = text("""
        SELECT 
            m.movie_id,
            m.title,
            m.year,
            m.summary,
            COALESCE(AVG(r.rating), 0) AS avg_rating,
            COUNT(r.rating_id) AS rating_count,
            ARRAY_AGG(DISTINCT g.genre_name ORDER BY g.genre_name) AS genres,
            l.imdb_id,
            l.tmdb_id
        FROM movies m
        LEFT JOIN movie_genres mg ON m.movie_id = mg.movie_id
        LEFT JOIN genres g ON mg.genre_id = g.genre_id
        LEFT JOIN ratings r ON m.movie_id = r.movie_id
        LEFT JOIN links l ON m.movie_id = l.movie_id
        WHERE m.movie_id = :movie_id
        GROUP BY m.movie_id, m.title, m.year, m.summary, l.imdb_id, l.tmdb_id
    """)
    
    with get_db_connection() as conn:
        result = conn.execute(sql, {"movie_id": movie_id})
        row = result.fetchone()
        
        if not row:
            return None
        
        return {
            "movie_id": row.movie_id,
            "title": row.title,
            "year": row.year,
            "summary": row.summary,
            "avg_rating": round(float(row.avg_rating), 2) if row.avg_rating else 0,
            "rating_count": row.rating_count,
            "genres": row.genres if row.genres and row.genres[0] else [],
            "imdb_id": row.imdb_id,
            "tmdb_id": row.tmdb_id,
            "imdb_url": f"https://www.imdb.com/title/{row.imdb_id}/" if row.imdb_id else None,
            "tmdb_url": f"https://www.themoviedb.org/movie/{row.tmdb_id}" if row.tmdb_id else None,
        }


# =============================================================================
# RATINGS (Transactional Operations)
# =============================================================================

def add_rating(user_id: int, movie_id: int, rating: float) -> Dict[str, Any]:
    """
    Add or update a user's rating for a movie.
    
    This demonstrates AlloyDB handling transactional writes.
    Uses upsert logic - if the user already rated this movie,
    update the rating instead of creating a duplicate.
    
    Args:
        user_id: The user's ID (1-610 in our dataset)
        movie_id: The movie's ID
        rating: Rating value (0.5 to 5.0 in 0.5 increments)
        
    Returns:
        Dict with success status and the rating details
    """
    # First, check if a rating already exists
    check_sql = text("""
        SELECT rating_id FROM ratings 
        WHERE user_id = :user_id AND movie_id = :movie_id
    """)
    
    with get_db_connection() as conn:
        existing = conn.execute(check_sql, {"user_id": user_id, "movie_id": movie_id}).fetchone()
        
        if existing:
            # Update existing rating
            update_sql = text("""
                UPDATE ratings 
                SET rating = :rating, rated_at = CURRENT_TIMESTAMP
                WHERE user_id = :user_id AND movie_id = :movie_id
                RETURNING rating_id, rating, rated_at
            """)
            result = conn.execute(update_sql, {
                "user_id": user_id,
                "movie_id": movie_id,
                "rating": rating
            })
            conn.commit()
            row = result.fetchone()
            action = "updated"
        else:
            # Insert new rating
            insert_sql = text("""
                INSERT INTO ratings (user_id, movie_id, rating, rated_at)
                VALUES (:user_id, :movie_id, :rating, CURRENT_TIMESTAMP)
                RETURNING rating_id, rating, rated_at
            """)
            result = conn.execute(insert_sql, {
                "user_id": user_id,
                "movie_id": movie_id,
                "rating": rating
            })
            conn.commit()
            row = result.fetchone()
            action = "created"
        
        return {
            "success": True,
            "action": action,
            "rating_id": row.rating_id,
            "user_id": user_id,
            "movie_id": movie_id,
            "rating": float(row.rating),
            "rated_at": row.rated_at.isoformat() if row.rated_at else None,
        }


# =============================================================================
# ANALYTICS (Analytics Page)
# =============================================================================

def get_analytics_data() -> Dict[str, Any]:
    """
    Get analytics data for the dashboard.
    
    These queries demonstrate AlloyDB's columnar engine capabilities.
    Aggregations over 100K+ ratings run quickly thanks to the
    column-oriented storage format.
    
    Returns:
        Dict with various analytics: top_movies, genre_distribution,
        ratings_by_year, avg_rating_by_genre
    """
    analytics = {}
    
    with get_db_connection() as conn:
        # Top rated movies (minimum 50 ratings for statistical significance)
        top_movies_sql = text("""
            SELECT 
                m.title,
                m.year,
                ROUND(AVG(r.rating)::numeric, 2) AS avg_rating,
                COUNT(r.rating_id) AS rating_count
            FROM movies m
            JOIN ratings r ON m.movie_id = r.movie_id
            GROUP BY m.movie_id, m.title, m.year
            HAVING COUNT(r.rating_id) >= 50
            ORDER BY AVG(r.rating) DESC
            LIMIT 10
        """)
        result = conn.execute(top_movies_sql)
        analytics["top_movies"] = [
            {
                "title": row.title,
                "year": row.year,
                "avg_rating": float(row.avg_rating),
                "rating_count": row.rating_count,
            }
            for row in result
        ]
        
        # Genre distribution (number of movies per genre)
        genre_dist_sql = text("""
            SELECT 
                g.genre_name,
                COUNT(DISTINCT mg.movie_id) AS movie_count
            FROM genres g
            JOIN movie_genres mg ON g.genre_id = mg.genre_id
            GROUP BY g.genre_id, g.genre_name
            ORDER BY movie_count DESC
        """)
        result = conn.execute(genre_dist_sql)
        analytics["genre_distribution"] = [
            {"genre": row.genre_name, "count": row.movie_count}
            for row in result
        ]
        
        # Ratings over time (by year of rating)
        ratings_time_sql = text("""
            SELECT 
                EXTRACT(YEAR FROM rated_at)::int AS year,
                COUNT(*) AS rating_count,
                ROUND(AVG(rating)::numeric, 2) AS avg_rating
            FROM ratings
            WHERE rated_at IS NOT NULL
            GROUP BY EXTRACT(YEAR FROM rated_at)
            ORDER BY year
        """)
        result = conn.execute(ratings_time_sql)
        analytics["ratings_by_year"] = [
            {
                "year": row.year,
                "count": row.rating_count,
                "avg_rating": float(row.avg_rating),
            }
            for row in result
        ]
        
        # Average rating by genre
        genre_ratings_sql = text("""
            SELECT 
                g.genre_name,
                ROUND(AVG(r.rating)::numeric, 2) AS avg_rating,
                COUNT(r.rating_id) AS rating_count
            FROM genres g
            JOIN movie_genres mg ON g.genre_id = mg.genre_id
            JOIN ratings r ON mg.movie_id = r.movie_id
            GROUP BY g.genre_id, g.genre_name
            ORDER BY avg_rating DESC
        """)
        result = conn.execute(genre_ratings_sql)
        analytics["avg_rating_by_genre"] = [
            {
                "genre": row.genre_name,
                "avg_rating": float(row.avg_rating),
                "rating_count": row.rating_count,
            }
            for row in result
        ]
        
        # Movies by decade
        decade_sql = text("""
            SELECT 
                (year / 10) * 10 AS decade,
                COUNT(*) AS movie_count
            FROM movies
            WHERE year IS NOT NULL
            GROUP BY (year / 10) * 10
            ORDER BY decade
        """)
        result = conn.execute(decade_sql)
        analytics["movies_by_decade"] = [
            {"decade": f"{row.decade}s", "count": row.movie_count}
            for row in result
        ]
    
    return analytics
