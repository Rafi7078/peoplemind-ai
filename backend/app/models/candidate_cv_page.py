
from sqlalchemy import (
    ForeignKey,
    Integer,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)
from backend.app.db.database import Base
class CandidateCVPage(Base):
    __tablename__ = "candidate_cv_pages"
    __table_args__ = (
        UniqueConstraint(
            "candidate_cv_id",
            "page_number",
            name=(
                "uq_candidate_cv_page_number"
            ),
        ),
    )
    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )
    candidate_cv_id: Mapped[int] = (
        mapped_column(
            ForeignKey(
                "candidate_cvs.id",
                ondelete="CASCADE",
            ),
            nullable=False,
            index=True,
        )
    )
    page_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    text: Mapped[str] = mapped_column(
        Text,
        default="",
        nullable=False,
    )
    char_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
