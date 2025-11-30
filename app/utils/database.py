"""
CymbalFlix Discover - Database Connection Utilities

This module handles secure connections to AlloyDB using the Python Connector
with IAM authentication. No passwords needed - your Google Cloud identity
is your database identity!

The connection pattern here is production-ready:
- Uses connection pooling via SQLAlchemy
- IAM authentication (no credentials to manage)
- Automatic connection refresh and retry

=============================================================================
STUDENT TASK: Complete the database connection configuration
=============================================================================
You'll need to:
1. Set up the connection parameters using environment variables
2. Complete the getconn() function to create AlloyDB connections
=============================================================================
"""

import os
import sqlalchemy
from google.cloud.alloydb.connector import Connector, IPTypes

# -----------------------------------------------------------------------------
# Configuration from Environment Variables
# -----------------------------------------------------------------------------
# These are set in .env locally or as Cloud Run environment variables

PROJECT_ID = os.environ.get("PROJECT_ID", "")
REGION = os.environ.get("REGION", "us-central1")
CLUSTER_ID = os.environ.get("CLUSTER_ID", "cymbalflix-cluster")
INSTANCE_ID = os.environ.get("INSTANCE_ID", "cymbalflix-primary")
DB_NAME = os.environ.get("DB_NAME", "cymbalflix")
DB_USER = os.environ.get("DB_USER", "")  # Your IAM email

# =============================================================================
# TODO 1: Build the Instance URI
# =============================================================================
# The AlloyDB Python Connector needs the full instance URI in this format:
# projects/{PROJECT}/locations/{REGION}/clusters/{CLUSTER}/instances/{INSTANCE}
#
# Use the variables defined above to construct this URI.
# Hint: Use an f-string to combine the variables.
#
# Example result:
# "projects/my-project/locations/us-central1/clusters/cymbalflix-cluster/instances/cymbalflix-primary"
# =============================================================================

INSTANCE_URI = ""  # TODO: Replace with the correct f-string

# =============================================================================


# -----------------------------------------------------------------------------
# Connection Pool Setup
# -----------------------------------------------------------------------------
# We use a global connector and engine for connection pooling.
# This is the recommended pattern for web applications.

# Global connector instance (reused across requests)
connector = None

# Global SQLAlchemy engine (manages the connection pool)
engine = None


def get_connector():
    """Get or create the AlloyDB connector instance."""
    global connector
    if connector is None:
        connector = Connector()
    return connector


def getconn():
    """
    Create a new database connection using the AlloyDB Python Connector.
    
    This function is called by SQLAlchemy's connection pool when it needs
    a new connection. The connector handles:
    - IAM authentication (no password needed!)
    - TLS encryption
    - Automatic certificate management
    
    Returns:
        A pg8000 database connection
    """
    # ==========================================================================
    # TODO 2: Complete the connection call
    # ==========================================================================
    # Use the AlloyDB connector to create a connection. You need to:
    #
    # 1. Call get_connector().connect() with these parameters:
    #    - INSTANCE_URI (the URI you built in TODO 1)
    #    - "pg8000" (the database driver)
    #    - user=DB_USER (your IAM email)
    #    - db=DB_NAME (the database name)
    #    - enable_iam_auth=True (this enables passwordless IAM authentication!)
    #    - ip_type=IPTypes.PUBLIC (we're using public IP for this lab)
    #
    # Hint: The pattern looks like:
    #   conn = get_connector().connect(
    #       INSTANCE_URI,
    #       "pg8000",
    #       user=...,
    #       db=...,
    #       enable_iam_auth=...,
    #       ip_type=...,
    #   )
    #
    # This is the ONLY place you need to specify connection details!
    # The AlloyDB connector handles all the complexity of secure connections.
    # ==========================================================================
    
    conn = None  # TODO: Replace with the connector.connect() call
    
    # ==========================================================================
    
    return conn


def get_engine():
    """
    Get or create the SQLAlchemy engine with connection pooling.
    
    The engine manages a pool of connections, automatically handling:
    - Connection reuse (efficiency)
    - Connection health checks
    - Automatic reconnection on failure
    
    Returns:
        SQLAlchemy Engine instance
    """
    global engine
    if engine is None:
        engine = sqlalchemy.create_engine(
            "postgresql+pg8000://",
            creator=getconn,
            pool_size=5,
            max_overflow=2,
            pool_timeout=30,
            pool_recycle=1800,  # Recycle connections every 30 minutes
        )
    return engine


def get_db_connection():
    """
    Get a database connection from the pool.
    
    Usage:
        with get_db_connection() as conn:
            result = conn.execute(sqlalchemy.text("SELECT 1"))
    
    Returns:
        SQLAlchemy connection context manager
    """
    return get_engine().connect()


def test_connection():
    """
    Test the database connection and return status info.
    
    Returns:
        dict with connection status and details
    """
    try:
        with get_db_connection() as conn:
            # Test basic connectivity
            result = conn.execute(sqlalchemy.text("SELECT version()"))
            version = result.fetchone()[0]
            
            # Get current user (should be your IAM identity)
            result = conn.execute(sqlalchemy.text("SELECT current_user"))
            current_user = result.fetchone()[0]
            
            # Get database name
            result = conn.execute(sqlalchemy.text("SELECT current_database()"))
            current_db = result.fetchone()[0]
            
            return {
                "status": "connected",
                "database": current_db,
                "user": current_user,
                "version": version[:50] + "..." if len(version) > 50 else version,
                "instance": INSTANCE_URI,
            }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "instance": INSTANCE_URI,
        }


def cleanup():
    """
    Clean up database connections.
    
    Call this when shutting down the application to properly
    close all connections in the pool.
    """
    global engine, connector
    if engine is not None:
        engine.dispose()
        engine = None
    if connector is not None:
        connector.close()
        connector = None


# -----------------------------------------------------------------------------
# Connection Status Check (for health endpoints)
# -----------------------------------------------------------------------------

def is_configured():
    """
    Check if the database connection is properly configured.
    
    Returns:
        bool: True if all required environment variables are set
    """
    required = [PROJECT_ID, DB_USER]
    return all(required)


def get_config_status():
    """
    Get the current configuration status for debugging.
    
    Returns:
        dict with configuration details (sensitive values masked)
    """
    return {
        "project_id": PROJECT_ID if PROJECT_ID else "(not set)",
        "region": REGION,
        "cluster_id": CLUSTER_ID,
        "instance_id": INSTANCE_ID,
        "db_name": DB_NAME,
        "db_user": DB_USER[:20] + "..." if DB_USER and len(DB_USER) > 20 else DB_USER if DB_USER else "(not set)",
        "instance_uri": INSTANCE_URI if PROJECT_ID else "(incomplete)",
        "is_configured": is_configured(),
    }
