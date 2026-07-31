from __future__ import annotations

from pydantic import BaseModel


class EnrolledUser(BaseModel):
    id: int
    username: str
    firstname: str
    lastname: str
    fullname: str
    email: str


class GradeItem(BaseModel):
    id: int
    itemname: str | None = None
    itemtype: str
    itemmodule: str | None = None
    graderaw: float | None = None
    gradeformatted: str | None = None
    percentageformatted: str | None = None


class UserGrades(BaseModel):
    courseid: int
    userid: int
    userfullname: str
    gradeitems: list[GradeItem]


class GradeItemsResponse(BaseModel):
    usergrades: list[UserGrades]
    warnings: list[dict] = []


class AssignmentSubmission(BaseModel):
    id: int
    userid: int
    status: str
    timecreated: int
    timemodified: int
    gradingstatus: str | None = None


class AssignmentSubmissions(BaseModel):
    assignmentid: int
    submissions: list[AssignmentSubmission]


class AssignmentSubmissionsResponse(BaseModel):
    assignments: list[AssignmentSubmissions]
    warnings: list[dict] = []


class QuizAttempt(BaseModel):
    id: int
    quiz: int
    userid: int
    attempt: int
    state: str
    timestart: int
    timefinish: int
    sumgrades: float | None = None


class QuizAttemptsResponse(BaseModel):
    attempts: list[QuizAttempt]
    warnings: list[dict] = []


class CompletionCriteria(BaseModel):
    type: int
    title: str
    status: str
    complete: bool
    timecompleted: int | None = None
    details: dict | None = None


class CourseCompletionStatus(BaseModel):
    type: int | None = None
    aggregation: int | None = None
    completions: list[CompletionCriteria] = []


class CompletionStatusResponse(BaseModel):
    completionstatus: CourseCompletionStatus
    warnings: list[dict] = []
