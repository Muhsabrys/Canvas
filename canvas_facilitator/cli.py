"""Command-line interface for canvas-facilitator."""

from __future__ import annotations

import json
import os
import sys

import click

from .api import CanvasAPI, CanvasAPIError
from .activities import Assignment, Discussion, Page, Quiz, QuizQuestion


def _get_api() -> CanvasAPI:
    """Build a :class:`CanvasAPI` from environment variables.

    Required environment variables
    ------------------------------
    ``CANVAS_BASE_URL``
        Root URL of your Canvas instance (e.g. ``https://canvas.example.com``).
    ``CANVAS_API_TOKEN``
        A Canvas access token.
    """
    base_url = os.environ.get("CANVAS_BASE_URL", "").strip()
    api_token = os.environ.get("CANVAS_API_TOKEN", "").strip()
    if not base_url or not api_token:
        click.echo(
            "Error: CANVAS_BASE_URL and CANVAS_API_TOKEN environment variables must be set.",
            err=True,
        )
        sys.exit(1)
    return CanvasAPI(base_url, api_token)


@click.group()
def main() -> None:
    """Facilitate creating Canvas LMS activities from the command line."""


# ---------------------------------------------------------------------------
# courses
# ---------------------------------------------------------------------------


@main.command("list-courses")
def list_courses() -> None:
    """List courses accessible to the authenticated user."""
    api = _get_api()
    try:
        courses = api.list_courses()
    except CanvasAPIError as exc:
        click.echo(str(exc), err=True)
        sys.exit(1)

    for course in courses:
        click.echo(f"{course.get('id'):>8}  {course.get('name', '(no name)')}")


# ---------------------------------------------------------------------------
# quiz
# ---------------------------------------------------------------------------


@main.command("create-quiz")
@click.argument("course_id", type=int)
@click.option("--title", required=True, help="Quiz title.")
@click.option("--description", default="", show_default=True, help="HTML description.")
@click.option(
    "--quiz-type",
    default="assignment",
    show_default=True,
    type=click.Choice(["assignment", "practice_quiz", "graded_survey", "survey"]),
    help="Type of quiz.",
)
@click.option("--time-limit", type=int, default=None, help="Time limit in minutes.")
@click.option(
    "--shuffle-answers",
    is_flag=True,
    default=False,
    help="Randomise answer order.",
)
@click.option(
    "--questions-json",
    default=None,
    help=(
        "Path to a JSON file containing a list of question objects. "
        "Each object should have keys: question_text, question_type, "
        "points_possible, answers."
    ),
)
def create_quiz(
    course_id: int,
    title: str,
    description: str,
    quiz_type: str,
    time_limit: int | None,
    shuffle_answers: bool,
    questions_json: str | None,
) -> None:
    """Create a quiz in COURSE_ID."""
    api = _get_api()
    questions: list[QuizQuestion] = []
    if questions_json:
        try:
            with open(questions_json) as fh:
                raw = json.load(fh)
        except (OSError, json.JSONDecodeError) as exc:
            click.echo(f"Error reading questions file: {exc}", err=True)
            sys.exit(1)
        for item in raw:
            questions.append(
                QuizQuestion(
                    question_text=item["question_text"],
                    question_type=item.get("question_type", "multiple_choice_question"),
                    points_possible=item.get("points_possible", 1.0),
                    answers=item.get("answers", []),
                )
            )

    quiz = Quiz(
        title=title,
        description=description,
        quiz_type=quiz_type,
        time_limit=time_limit,
        shuffle_answers=shuffle_answers,
        questions=questions,
    )
    try:
        result = quiz.create(api, course_id)
    except CanvasAPIError as exc:
        click.echo(str(exc), err=True)
        sys.exit(1)
    click.echo(json.dumps(result, indent=2))


# ---------------------------------------------------------------------------
# assignment
# ---------------------------------------------------------------------------


@main.command("create-assignment")
@click.argument("course_id", type=int)
@click.option("--title", required=True, help="Assignment title.")
@click.option("--description", default="", show_default=True, help="HTML description.")
@click.option(
    "--points",
    type=float,
    default=100.0,
    show_default=True,
    help="Maximum points possible.",
)
@click.option(
    "--submission-types",
    default="online_upload",
    show_default=True,
    help="Comma-separated list of submission types.",
)
@click.option("--due-at", default=None, help="Due date in ISO-8601 format.")
@click.option(
    "--grading-type",
    default="points",
    show_default=True,
    type=click.Choice(["points", "percent", "letter_grade", "gpa_scale", "pass_fail"]),
    help="Grading type.",
)
@click.option("--published", is_flag=True, default=False, help="Publish immediately.")
def create_assignment(
    course_id: int,
    title: str,
    description: str,
    points: float,
    submission_types: str,
    due_at: str | None,
    grading_type: str,
    published: bool,
) -> None:
    """Create an assignment in COURSE_ID."""
    api = _get_api()
    assignment = Assignment(
        title=title,
        description=description,
        points_possible=points,
        submission_types=[s.strip() for s in submission_types.split(",")],
        due_at=due_at,
        grading_type=grading_type,
        published=published,
    )
    try:
        result = assignment.create(api, course_id)
    except CanvasAPIError as exc:
        click.echo(str(exc), err=True)
        sys.exit(1)
    click.echo(json.dumps(result, indent=2))


# ---------------------------------------------------------------------------
# discussion
# ---------------------------------------------------------------------------


@main.command("create-discussion")
@click.argument("course_id", type=int)
@click.option("--title", required=True, help="Discussion title.")
@click.option("--message", default="", show_default=True, help="HTML body / prompt.")
@click.option(
    "--discussion-type",
    default="side_comment",
    show_default=True,
    type=click.Choice(["side_comment", "threaded"]),
    help="Discussion threading type.",
)
@click.option("--published", is_flag=True, default=False, help="Publish immediately.")
def create_discussion(
    course_id: int,
    title: str,
    message: str,
    discussion_type: str,
    published: bool,
) -> None:
    """Create a discussion topic in COURSE_ID."""
    api = _get_api()
    discussion = Discussion(
        title=title,
        message=message,
        discussion_type=discussion_type,
        published=published,
    )
    try:
        result = discussion.create(api, course_id)
    except CanvasAPIError as exc:
        click.echo(str(exc), err=True)
        sys.exit(1)
    click.echo(json.dumps(result, indent=2))


# ---------------------------------------------------------------------------
# page
# ---------------------------------------------------------------------------


@main.command("create-page")
@click.argument("course_id", type=int)
@click.option("--title", required=True, help="Page title.")
@click.option("--body", default="", show_default=True, help="HTML body content.")
@click.option(
    "--editing-roles",
    default="teachers",
    show_default=True,
    type=click.Choice(["teachers", "students", "members", "public"]),
    help="Who can edit the page.",
)
@click.option("--published", is_flag=True, default=False, help="Publish immediately.")
def create_page(
    course_id: int,
    title: str,
    body: str,
    editing_roles: str,
    published: bool,
) -> None:
    """Create a wiki page in COURSE_ID."""
    api = _get_api()
    page = Page(
        title=title,
        body=body,
        editing_roles=editing_roles,
        published=published,
    )
    try:
        result = page.create(api, course_id)
    except CanvasAPIError as exc:
        click.echo(str(exc), err=True)
        sys.exit(1)
    click.echo(json.dumps(result, indent=2))
