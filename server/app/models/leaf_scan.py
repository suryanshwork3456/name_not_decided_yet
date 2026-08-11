import uuid
from typing import Dict, Any
from datetime import datetime

from sqlalchemy import String, DateTime, Float, ForeignKey, text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB

from app.db.session import Base

class LeafScan(Base):

    __tablename__ = "leaf_scans"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    field_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), nullable=False, index=True
    )  # ForeignKey removed temporarily — add back once 'field' table exists
    image_url: Mapped[str] = mapped_column(String, nullable=True)
    predicted_disease: Mapped[str] = mapped_column(String, nullable=True)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default="pending")
    followup_answers: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
        default=dict,
    )
    final_diagnosis: Mapped[str] = mapped_column(String, nullable=True)
    action_plan: Mapped[str] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)