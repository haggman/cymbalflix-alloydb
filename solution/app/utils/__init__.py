"""
CymbalFlix Discover - Utility Modules

This package contains:
- database.py: AlloyDB connection handling
- queries.py: SQL queries and data access functions
"""

from .database import (
    get_db_connection,
    test_connection,
    is_configured,
    get_config_status,
    cleanup,
)

from .queries import (
    get_stats,
    search_movies_semantic,
    search_movies_keyword,
    browse_movies,
    get_movie_details,
    get_genres,
    add_rating,
    get_analytics_data,
)

__all__ = [
    # Database
    "get_db_connection",
    "test_connection", 
    "is_configured",
    "get_config_status",
    "cleanup",
    # Queries
    "get_stats",
    "search_movies_semantic",
    "search_movies_keyword",
    "browse_movies",
    "get_movie_details",
    "get_genres",
    "add_rating",
    "get_analytics_data",
]
