# ============================================================
# File: app/db/base.py
# ============================================================
"""
Central import point for all SQLAlchemy models.
Ensures every model is registered on Base.metadata so Alembic's
autogenerate can detect schema changes correctly.
"""

print("app/db/base.py")