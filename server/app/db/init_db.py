# ============================================================
# File: app/db/init_db.py
# ============================================================
"""
Standalone script to initialize the database — creates all tables
defined by models that inherit from Base.

Run with: python -m app.db.init_db
"""

import asyncio

# Import Base + engine setup
from app.db.session import init_db as _init_db

# IMPORTANT: import every model module here so Base.metadata
# actually knows about these tables before create_all runs.
# Even though these imports look "unused", they register the
# models with SQLAlchemy's metadata via Base subclassing.
# from app.models import field        # noqa: F401
from app.models import leaf_scan    # noqa: F401
# from app.models import user         # noqa: F401
# add any other model files you have, e.g.:
# from app.models import soil_data  # noqa: F401


async def main():
    print("Creating tables...")
    await _init_db()
    print("Done. Tables created (if they didn't already exist).")


if __name__ == "__main__":
    asyncio.run(main())