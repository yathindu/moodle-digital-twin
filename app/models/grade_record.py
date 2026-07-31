from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.course import Course
    from app.models.student import Student


class GradeRecord(TimestampMixin, Base):
    """Append-only snapshot of one grade item's value for a student at a point in time."""

    __tablename__ = "grade_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), index=True)
    moodle_grade_item_id: Mapped[int] = mapped_column(index=True)
    item_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    item_type: Mapped[str] = mapped_column(String(50))
    item_module: Mapped[str | None] = mapped_column(String(50), nullable=True)
    grade_raw: Mapped[float | None] = mapped_column(Float, nullable=True)
    grade_formatted: Mapped[str | None] = mapped_column(String(50), nullable=True)
    percentage_formatted: Mapped[str | None] = mapped_column(String(50), nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)

    student: Mapped["Student"] = relationship(back_populates="grade_records")
    course: Mapped["Course"] = relationship(back_populates="grade_records")
