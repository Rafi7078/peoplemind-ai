from datetime import datetime, timezone
from sqlalchemy import (
    DateTime,
    Integer,
    LargeBinary,
    String,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)
from backend.app.db.database import Base
class FileBlob(Base):
    __tablename__ = "file_blobs"
    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )
    storage_key: Mapped[str] = mapped_column(
        String(500),
        unique=True,
        index=True,
        nullable=False,
    )
    content: Mapped[bytes] = mapped_column(
        LargeBinary,
        nullable=False,
    )
    size_bytes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    sha256: Mapped[str] = mapped_column(
        String(64),
        index=True,
        nullable=False,
    )
    mime_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
