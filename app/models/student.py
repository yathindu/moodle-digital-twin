from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.assignment_submission import AssignmentSubmission
    from app.models.completion_record import CompletionRecord
    from app.models.enrollment import Enrollment
    from app.models.grade_record import GradeRecord
    from app.models.quiz_attempt import QuizAttempt


class Student(TimestampMixin, Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(primary_key=True)
    moodle_user_id: Mapped[int] = mapped_column(unique=True, index=True)
    username: Mapped[str] = mapped_column(String(100))
    firstname: Mapped[str] = mapped_column(String(100))
    lastname: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255))

    enrollments: Mapped[list["Enrollment"]] = relationship(back_populates="student")
    grade_records: Mapped[list["GradeRecord"]] = relationship(back_populates="student")
    assignment_submissions: Mapped[list["AssignmentSubmission"]] = relationship(
        back_populates="student"
    )
    quiz_attempts: Mapped[list["QuizAttempt"]] = relationship(back_populates="student")
    completion_records: Mapped[list["CompletionRecord"]] = relationship(
        back_populates="student"
    )
