# ============================================================
# File: app/schemas/field.py
# ============================================================
"""
Pydantic schemas for the Field feature.
Defines GeoJSON-compatible field creation/response models and
scan result response schemas used by app/api/v1/fields.py.
"""

import uuid
from pydantic import BaseModel

class UploadUrlRequest(BaseModel):
    field_id: uuid.UUID
    content_type: str = "image/jpeg"
