from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.completion_record import CompletionRecord
    from app.models.enrollment import Enrollment
    from app.models.grade_record import GradeRecord


class Course(TimestampMixin, Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(primary_key=True)
    moodle_course_id: Mapped[int] = mapped_column(unique=True, index=True)
    shortname: Mapped[str] = mapped_column(String(255))
    fullname: Mapped[str] = mapped_column(String(255))
    category_id: Mapped[int | None] = mapped_column(nullable=True)
    start_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    end_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    enrollments: Mapped[list["Enrollment"]] = relationship(back_populates="course")
    grade_records: Mapped[list["GradeRecord"]] = relationship(back_populates="course")
    completion_records: Mapped[list["CompletionRecord"]] = relationship(
        back_populates="course"
    )
