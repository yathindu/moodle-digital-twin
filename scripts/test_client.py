"""Sanity-check the full Moodle auth + fetch + validate path.

Calls each MoodleClient method against the local instance using real data
from the seeded course and prints the validated Pydantic objects.

Usage:
    python scripts/test_client.py [course_id]
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.moodle.client import MoodleClient  # noqa: E402


async def main() -> None:
    course_id = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    client = MoodleClient()

    print(f"=== get_enrolled_users(course_id={course_id}) ===")
    users = await client.get_enrolled_users(course_id)
    print(f"{len(users)} users")
    for u in users[:3]:
        print(" ", u)
    if not users:
        print("No enrolled users -- stopping, remaining calls need a real user_id.")
        return

    user_id = users[0].id
    print(f"\nUsing user_id={user_id} ({users[0].fullname}) for per-user calls")

    print(f"\n=== get_grade_items(course_id={course_id}, user_id={user_id}) ===")
    try:
        print(await client.get_grade_items(course_id, user_id))
    except Exception as e:
        print("FAILED:", repr(e))

    print(f"\n=== get_completion_status(course_id={course_id}, user_id={user_id}) ===")
    try:
        print(await client.get_completion_status(course_id, user_id))
    except Exception as e:
        print("FAILED:", repr(e))

    print(f"\n=== scanning course_id={course_id} contents for assign/quiz modules ===")
    contents = await client.call("core_course_get_contents", courseid=course_id)
    assign_id: int | None = None
    quiz_id: int | None = None
    for section in contents:
        for module in section.get("modules", []):
            if module.get("modname") == "assign" and assign_id is None:
                assign_id = module["instance"]
            if module.get("modname") == "quiz" and quiz_id is None:
                quiz_id = module["instance"]

    if assign_id is not None:
        print(f"\n=== get_assignment_submissions(assign_id={assign_id}) ===")
        try:
            print(await client.get_assignment_submissions(assign_id))
        except Exception as e:
            print("FAILED:", repr(e))
    else:
        print("No assignment module in this course -- skipping get_assignment_submissions.")

    if quiz_id is not None:
        print(f"\n=== get_quiz_attempts(quiz_id={quiz_id}, user_id={user_id}) ===")
        try:
            print(await client.get_quiz_attempts(quiz_id, user_id))
        except Exception as e:
            print("FAILED:", repr(e))
    else:
        print("No quiz module in this course -- skipping get_quiz_attempts.")


if __name__ == "__main__":
    asyncio.run(main())
