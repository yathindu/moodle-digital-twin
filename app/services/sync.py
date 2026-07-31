"""Syncs a Moodle course into the local database.

Student/Course/Enrollment are current-state rows, upserted by unique key.
GradeRecord/AssignmentSubmission/QuizAttempt/CompletionRecord are append-only
time-series snapshots (see CLAUDE.md: time-respecting splits, never shuffle
student time-series data) -- a new row is only appended when the value has
actually changed since the last recorded snapshot, so rerunning sync_course
with unchanged data is a no-op rather than flooding the tables with
duplicates.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AssignmentSubmission as AssignmentSubmissionRecord
from app.models import CompletionRecord, Course, Enrollment, GradeRecord, SessionLocal, Student
from app.models import QuizAttempt as QuizAttemptRecord
from app.moodle.client import MoodleClient
from app.schemas.moodle import AssignmentSubmission as AssignmentSubmissionData
from app.schemas.moodle import CompletionCriteria, EnrolledUser, GradeItem
from app.schemas.moodle import QuizAttempt as QuizAttemptData


def _ts(value: int | None) -> datetime | None:
    return datetime.fromtimestamp(value, tz=timezone.utc) if value else None


def _upsert_course(session: Session, data: dict) -> Course:
    course = session.execute(
        select(Course).where(Course.moodle_course_id == data["id"])
    ).scalar_one_or_none()
    if course is None:
        course = Course(moodle_course_id=data["id"])
        session.add(course)
    course.shortname = data["shortname"]
    course.fullname = data["fullname"]
    course.category_id = data.get("categoryid")
    course.start_date = _ts(data.get("startdate"))
    course.end_date = _ts(data.get("enddate"))
    session.flush()
    return course


def _upsert_student(session: Session, user: EnrolledUser) -> Student:
    student = session.execute(
        select(Student).where(Student.moodle_user_id == user.id)
    ).scalar_one_or_none()
    if student is None:
        student = Student(moodle_user_id=user.id)
        session.add(student)
    student.username = user.username
    student.firstname = user.firstname
    student.lastname = user.lastname
    student.email = user.email
    session.flush()
    return student


def _upsert_enrollment(session: Session, student: Student, course: Course, user: EnrolledUser) -> None:
    role = user.roles[0]["shortname"] if user.roles else "student"
    enrollment = session.execute(
        select(Enrollment).where(
            Enrollment.student_id == student.id, Enrollment.course_id == course.id
        )
    ).scalar_one_or_none()
    if enrollment is None:
        enrollment = Enrollment(student_id=student.id, course_id=course.id)
        session.add(enrollment)
    enrollment.role = role
    enrollment.status = "active"
    session.flush()


def _upsert_grade_record(
    session: Session, student: Student, course: Course, item: GradeItem
) -> bool:
    latest = session.execute(
        select(GradeRecord)
        .where(
            GradeRecord.student_id == student.id,
            GradeRecord.moodle_grade_item_id == item.id,
        )
        .order_by(GradeRecord.recorded_at.desc())
        .limit(1)
    ).scalar_one_or_none()

    if (
        latest is not None
        and latest.grade_raw == item.graderaw
        and latest.grade_formatted == item.gradeformatted
        and latest.percentage_formatted == item.percentageformatted
    ):
        return False

    session.add(
        GradeRecord(
            student_id=student.id,
            course_id=course.id,
            moodle_grade_item_id=item.id,
            item_name=item.itemname,
            item_type=item.itemtype,
            item_module=item.itemmodule,
            grade_raw=item.graderaw,
            grade_formatted=item.gradeformatted,
            percentage_formatted=item.percentageformatted,
            recorded_at=datetime.now(timezone.utc),
        )
    )
    return True


def _completion_identity(details: dict | None) -> str:
    """Moodle's completion status response has no stable numeric criterion id,
    so the rendered 'criteria' description (e.g. a link to the activity) is
    the only reliable way to tell two criteria of the same type/title apart."""
    return (details or {}).get("criteria", "")


def _upsert_completion_record(
    session: Session, student: Student, course: Course, criterion: CompletionCriteria
) -> bool:
    candidates = (
        session.execute(
            select(CompletionRecord)
            .where(
                CompletionRecord.student_id == student.id,
                CompletionRecord.course_id == course.id,
                CompletionRecord.criteria_type == criterion.type,
            )
            .order_by(CompletionRecord.recorded_at.desc())
        )
        .scalars()
        .all()
    )
    target_key = _completion_identity(criterion.details)
    latest = next(
        (c for c in candidates if _completion_identity(c.details) == target_key), None
    )

    if latest is not None and latest.status == criterion.status and latest.complete == criterion.complete:
        return False

    session.add(
        CompletionRecord(
            student_id=student.id,
            course_id=course.id,
            criteria_type=criterion.type,
            title=criterion.title,
            status=criterion.status,
            complete=criterion.complete,
            time_completed=_ts(criterion.timecompleted),
            details=criterion.details,
            recorded_at=datetime.now(timezone.utc),
        )
    )
    return True


def _upsert_assignment_submission(
    session: Session, student: Student, assign_id: int, sub: AssignmentSubmissionData
) -> bool:
    modified_at = _ts(sub.timemodified)
    latest = session.execute(
        select(AssignmentSubmissionRecord)
        .where(
            AssignmentSubmissionRecord.student_id == student.id,
            AssignmentSubmissionRecord.moodle_assignment_id == assign_id,
        )
        .order_by(AssignmentSubmissionRecord.created_at.desc())
        .limit(1)
    ).scalar_one_or_none()

    if (
        latest is not None
        and latest.moodle_submission_id == sub.id
        and latest.status == sub.status
        and latest.grading_status == sub.gradingstatus
        and latest.modified_at == modified_at
    ):
        return False

    session.add(
        AssignmentSubmissionRecord(
            student_id=student.id,
            moodle_assignment_id=assign_id,
            moodle_submission_id=sub.id,
            status=sub.status,
            grading_status=sub.gradingstatus,
            submitted_at=_ts(sub.timecreated),
            modified_at=modified_at,
        )
    )
    return True


def _upsert_quiz_attempt(
    session: Session, student: Student, quiz_id: int, attempt: QuizAttemptData
) -> bool:
    finished_at = _ts(attempt.timefinish)
    latest = session.execute(
        select(QuizAttemptRecord)
        .where(
            QuizAttemptRecord.student_id == student.id,
            QuizAttemptRecord.moodle_quiz_id == quiz_id,
            QuizAttemptRecord.moodle_attempt_id == attempt.id,
        )
        .order_by(QuizAttemptRecord.created_at.desc())
        .limit(1)
    ).scalar_one_or_none()

    if latest is not None and latest.state == attempt.state and latest.sum_grades == attempt.sumgrades:
        return False

    session.add(
        QuizAttemptRecord(
            student_id=student.id,
            moodle_quiz_id=quiz_id,
            moodle_attempt_id=attempt.id,
            attempt_number=attempt.attempt,
            state=attempt.state,
            sum_grades=attempt.sumgrades,
            started_at=_ts(attempt.timestart),
            finished_at=finished_at,
        )
    )
    return True


async def sync_course(course_id: int) -> dict[str, int]:
    client = MoodleClient()
    session = SessionLocal()
    try:
        courses = await client.call("core_course_get_courses", options={"ids": [course_id]})
        if not courses:
            raise ValueError(f"Course {course_id} not found on Moodle")
        course = _upsert_course(session, courses[0])

        enrolled_users = await client.get_enrolled_users(course_id)
        students_by_moodle_id: dict[int, Student] = {}
        for user in enrolled_users:
            student = _upsert_student(session, user)
            students_by_moodle_id[user.id] = student
            _upsert_enrollment(session, student, course, user)

        grade_count = 0
        for user in enrolled_users:
            student = students_by_moodle_id[user.id]
            grades = await client.get_grade_items(course_id, user.id)
            for usergrade in grades.usergrades:
                for item in usergrade.gradeitems:
                    if _upsert_grade_record(session, student, course, item):
                        grade_count += 1

        completion_count = 0
        for user in enrolled_users:
            student = students_by_moodle_id[user.id]
            try:
                completion = await client.get_completion_status(course_id, user.id)
            except Exception:
                continue  # e.g. no completion criteria configured on this course
            for criterion in completion.completionstatus.completions:
                if _upsert_completion_record(session, student, course, criterion):
                    completion_count += 1

        contents = await client.call("core_course_get_contents", courseid=course_id)
        assign_ids: list[int] = []
        quiz_ids: list[int] = []
        for section in contents:
            for module in section.get("modules", []):
                if module.get("modname") == "assign":
                    assign_ids.append(module["instance"])
                elif module.get("modname") == "quiz":
                    quiz_ids.append(module["instance"])

        submission_count = 0
        for assign_id in assign_ids:
            submissions = await client.get_assignment_submissions(assign_id)
            for assignment in submissions.assignments:
                for sub in assignment.submissions:
                    student = students_by_moodle_id.get(sub.userid)
                    if student is None:
                        continue
                    if _upsert_assignment_submission(session, student, assign_id, sub):
                        submission_count += 1

        attempt_count = 0
        for quiz_id in quiz_ids:
            for user in enrolled_users:
                student = students_by_moodle_id[user.id]
                attempts = await client.get_quiz_attempts(quiz_id, user.id)
                for attempt in attempts.attempts:
                    if _upsert_quiz_attempt(session, student, quiz_id, attempt):
                        attempt_count += 1

        session.commit()
        return {
            "moodle_course_id": course.moodle_course_id,
            "db_course_id": course.id,
            "students_synced": len(enrolled_users),
            "grade_records_added": grade_count,
            "completion_records_added": completion_count,
            "assignment_submissions_added": submission_count,
            "quiz_attempts_added": attempt_count,
        }
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
