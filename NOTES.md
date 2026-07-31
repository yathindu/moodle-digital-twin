# NOTES

## Week 1

- Enabled function list on the local instance was checked via
  `core_webservice_get_site_info` before writing any MoodleClient methods.
  Read functions (`core_enrol_get_enrolled_users`,
  `gradereport_user_get_grade_items`, `mod_assign_get_submissions`,
  `mod_quiz_get_user_attempts`, `core_completion_get_course_completion_status`)
  are all on the "Moodle mobile web service" (the one MOODLE_TOKEN in .env
  points to).
- Write functions needed for synthetic data seeding
  (`core_user_create_users`, `core_course_create_courses`,
  `enrol_manual_enrol_users`) are NOT on that service by default. Created a
  separate custom external service, "Digital Twin API" (service id=4), with
  those 3 plus `core_course_get_categories`, and a separate admin token for
  it. Kept it separate from the main .env MOODLE_TOKEN on purpose (least
  privilege: the app's regular token stays read-only).
- Gotcha: the "Add functions to service" admin page only becomes interactive
  with Edit mode toggled on (top-right of any admin page), and the service
  itself has a separate "Enabled" checkbox on its Edit page, independent of
  which functions are attached to it. Both tripped us up before functions
  actually took effect.
- `scripts/seed_moodle.py` seeds 1 course + 30 synthetic students, run with
  the write-capable token as a one-off env override:
  `MOODLE_TOKEN=<digital-twin-api-token> python scripts/seed_moodle.py`
- Moodle core's Web Service API has no function to create course modules
  (assignments, quizzes, questions) or configure course completion criteria
  -- confirmed by checking the full enabled-function list, not just this
  instance's config. Added the assignment ("Programming Fundamentals
  Homework 1"), quiz ("Week 1 Quiz", 2 True/False questions), and course
  completion criteria to course 2 manually via the web UI.
- `scripts/test_client.py` exercises all 5 MoodleClient methods against
  real course/student data end to end -- all validated successfully as of
  2026-07-31.
- `MoodleClient.call()` now raises `MoodleAPIError` when Moodle's REST
  response is an exception payload (`{"exception": ...}`), instead of
  silently passing the error dict into Pydantic validation and producing a
  confusing "field required" error.
