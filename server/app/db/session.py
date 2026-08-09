# ============================================================
# File: app/db/session.py
# ============================================================
"""
Database session management.
Creates the SQLAlchemy engine and sessionmaker, and provides the
get_db() dependency used by API routes to access the database.
"""