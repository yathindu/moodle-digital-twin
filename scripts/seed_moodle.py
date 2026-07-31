"""One-off script to seed the local Moodle instance with synthetic data.

Creates 30 synthetic students and 1 course, then enrols all students in the
course, via the Moodle Web Services REST API.

Requires MOODLE_TOKEN's external service to have these functions enabled
(verified against core_webservice_get_site_info on this instance as of
2026-07-31 -- NOT enabled by default, must be added via Site Administration
> Server > Web services > External services):
  - core_user_create_users
  - core_course_create_courses
  - enrol_manual_enrol_users

Usage:
    python scripts/seed_moodle.py
"""

from __future__ import annotations

import asyncio
import itertools
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.moodle.client import MoodleClient  # noqa: E402

STUDENT_ROLE_ID = 5  # Default Moodle site role ID for "Student"

FIRST_NAMES = [
    "Nimal", "Kasun", "Chathurika", "Ishara", "Tharindu", "Sanduni",
    "Dilshan", "Piumi", "Ravindu", "Nethmi", "Amal", "Vindya",
    "Sachini", "Lakshan", "Hasini", "Chamod", "Kavindi", "Sahan",
    "Dinithi", "Yasas", "Anushka", "Tharushi", "Malith", "Oshadi",
    "Ruwan", "Senuri", "Kavishka", "Imesha", "Nuwan", "Thilini",
]
LAST_NAMES = [
    "Perera", "Fernando", "Silva", "Bandara", "Jayasuriya", "Wijesinghe",
    "Gunawardena", "Rathnayake", "Karunaratne", "Dissanayake",
]


def generate_students(count: int) -> list[dict[str, str]]:
    combos = list(itertools.product(FIRST_NAMES, LAST_NAMES))
    random.shuffle(combos)
    students = []
    for i, (first, last) in enumerate(combos[:count]):
        username = f"{first.lower()}.{last.lower()}{i}"
        students.append(
            {
                "username": username,
                "password": f"Synth3tic!{i}",
                "firstname": first,
                "lastname": last,
                "email": f"{username}@example.edu",
            }
        )
    return students


async def main() -> None:
    client = MoodleClient()

    print("Fetching course categories...")
    categories = await client.call("core_course_get_categories")
    category_id = categories[0]["id"] if categories else 1
    print(f"  using category id={category_id}")

    print("Creating course...")
    course_result = await client.call(
        "core_course_create_courses",
        courses=[
            {
                "fullname": "Introduction to Computer Science",
                "shortname": f"CS101-{random.randint(1000, 9999)}",
                "categoryid": category_id,
                "summary": "Synthetic course for digital twin development.",
            }
        ],
    )
    course_id = course_result[0]["id"]
    print(f"  created course id={course_id}")

    print("Generating 30 synthetic students...")
    students = generate_students(30)

    print("Creating students...")
    user_result = await client.call("core_user_create_users", users=students)
    for student, created in zip(students, user_result):
        print(f"  created user: {student['username']} (id={created['id']})")

    print(f"Enrolling {len(user_result)} students in course {course_id}...")
    enrolments = [
        {"roleid": STUDENT_ROLE_ID, "userid": created["id"], "courseid": course_id}
        for created in user_result
    ]
    await client.call("enrol_manual_enrol_users", enrolments=enrolments)
    print("  enrolment complete")

    print(f"\nDone. Course id={course_id}, {len(user_result)} students enrolled.")


if __name__ == "__main__":
    asyncio.run(main())
