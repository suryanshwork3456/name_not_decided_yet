# ============================================================
# File: app/api/v1/fields.py
# ============================================================
"""
Field endpoints (Path 1 feature).
Defines routes to create/manage field polygons and fetch NDVI
scan results for a given field.
"""

import os
import uuid
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, status
from sqlalchemy.orm import Session

# Import your database session dependency and model
from app.db.session import get_db
from app.models.leaf_scan import LeafScan

router = APIRouter(prefix="/api/v1/leaf", tags=["Leaf Scans"])

# Define path where uploads will be stored
UPLOAD_DIR = os.path.join("uploads", "leaf_scans")
os.makedirs(UPLOAD_DIR, exist_ok=True)  # Create folder if it doesn't exist

# Allowed MIME types
ALLOWED_TYPES = ["image/jpeg", "image/png", "image/jpg", "image/webp"]

@router.post("/scan", status_code=status.HTTP_201_CREATED)
async def upload_and_create_scan(
    field_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # 1. Validate file type
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400, 
            detail="Invalid file type. Only JPEG, PNG, and WebP images are allowed."
        )

    # 2. Generate a unique filename to prevent overwrites
    file_extension = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    # 3. Read and save file locally on server
    try:
        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to save image locally: {str(e)}"
        )

    # 4. Construct accessible static URL (points to FastAPI static server)
    # Serves at: http://localhost:8000/static/leaf_scans/<uuid>.jpg
    relative_image_url = f"/static/leaf_scans/{unique_filename}"

    # 5. Insert record into Postgres DB with status 'pending'
    new_scan = LeafScan(
        field_id=field_id,
        image_url=relative_image_url,
        status="pending"
    )
    db.add(new_scan)
    db.commit()
    db.refresh(new_scan)

    # Note for Step 3: Trigger Celery task here
    # task = process_leaf_scan.delay(scan_id=new_scan.id, file_path=file_path)

    return {
        "scan_id": new_scan.id,
        "field_id": new_scan.field_id,
        "image_url": new_scan.image_url,
        "status": new_scan.status,
        "message": "Image uploaded and scan queued successfully."
    }



