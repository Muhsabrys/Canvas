"""Canvas LMS activity creators.

Each class models one activity type and knows how to POST itself to the
Canvas REST API via a :class:`~canvas_facilitator.api.CanvasAPI` instance.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .api import CanvasAPI


# ---------------------------------------------------------------------------
# Quiz
# ---------------------------------------------------------------------------


@dataclass
class QuizQuestion:
    """A single question inside a :class:`Quiz`.

    Parameters
    ----------
    question_text:
        The text body of the question.
    question_type:
        One of the Canvas quiz question types, e.g. ``"multiple_choice_question"``,
        ``"true_false_question"``, ``"short_answer_question"``, etc.
    points_possible:
        Point value for this question (default 1).
    answers:
        List of answer dicts accepted by the Canvas API, e.g.
        ``[{"text": "Yes", "weight": 100}, {"text": "No", "weight": 0}]``.
    """

    question_text: str
    question_type: str = "multiple_choice_question"
    points_possible: float = 1.0
    answers: list[dict[str, Any]] = field(default_factory=list)

    def to_payload(self) -> dict:
        return {
            "question": {
                "question_text": self.question_text,
                "question_type": self.question_type,
                "points_possible": self.points_possible,
                "answers": self.answers,
            }
        }


@dataclass
class Quiz:
    """Represents a Canvas quiz activity.

    Parameters
    ----------
    title:
        Quiz title shown to students.
    description:
        Optional HTML description / instructions.
    quiz_type:
        One of ``"assignment"``, ``"practice_quiz"``, ``"graded_survey"``,
        ``"survey"`` (default ``"assignment"``).
    time_limit:
        Time limit in minutes, or ``None`` for no limit.
    shuffle_answers:
        Whether answer options are randomised (default ``False``).
    questions:
        :class:`QuizQuestion` objects to add after the quiz is created.
    """

    title: str
    description: str = ""
    quiz_type: str = "assignment"
    time_limit: int | None = None
    shuffle_answers: bool = False
    questions: list[QuizQuestion] = field(default_factory=list)

    def _quiz_payload(self) -> dict:
        payload: dict[str, Any] = {
            "quiz": {
                "title": self.title,
                "description": self.description,
                "quiz_type": self.quiz_type,
                "shuffle_answers": self.shuffle_answers,
            }
        }
        if self.time_limit is not None:
            payload["quiz"]["time_limit"] = self.time_limit
        return payload

    def create(self, api: CanvasAPI, course_id: int) -> dict:
        """Create the quiz (and its questions) in Canvas.

        Returns the Canvas API response for the created quiz.
        """
        quiz_data = api.post(f"courses/{course_id}/quizzes", self._quiz_payload())
        quiz_id = quiz_data["id"]
        for question in self.questions:
            api.post(
                f"courses/{course_id}/quizzes/{quiz_id}/questions",
                question.to_payload(),
            )
        return quiz_data


# ---------------------------------------------------------------------------
# Assignment
# ---------------------------------------------------------------------------


@dataclass
class Assignment:
    """Represents a Canvas assignment activity.

    Parameters
    ----------
    title:
        Assignment name.
    description:
        Optional HTML description / instructions.
    points_possible:
        Maximum score (default ``100``).
    submission_types:
        List of allowed submission types, e.g. ``["online_text_entry"]``.
        Defaults to ``["online_upload"]``.
    due_at:
        ISO-8601 due date/time string, e.g. ``"2024-12-31T23:59:00Z"``, or
        ``None`` for no due date.
    grading_type:
        One of ``"points"``, ``"percent"``, ``"letter_grade"``, etc.
        (default ``"points"``).
    published:
        Whether the assignment is visible to students immediately
        (default ``False``).
    """

    title: str
    description: str = ""
    points_possible: float = 100.0
    submission_types: list[str] = field(default_factory=lambda: ["online_upload"])
    due_at: str | None = None
    grading_type: str = "points"
    published: bool = False

    def _assignment_payload(self) -> dict:
        payload: dict[str, Any] = {
            "assignment": {
                "name": self.title,
                "description": self.description,
                "points_possible": self.points_possible,
                "submission_types": self.submission_types,
                "grading_type": self.grading_type,
                "published": self.published,
            }
        }
        if self.due_at is not None:
            payload["assignment"]["due_at"] = self.due_at
        return payload

    def create(self, api: CanvasAPI, course_id: int) -> dict:
        """Create the assignment in Canvas.

        Returns the Canvas API response for the created assignment.
        """
        return api.post(
            f"courses/{course_id}/assignments", self._assignment_payload()
        )


# ---------------------------------------------------------------------------
# Discussion
# ---------------------------------------------------------------------------


@dataclass
class Discussion:
    """Represents a Canvas discussion-topic activity.

    Parameters
    ----------
    title:
        Discussion title.
    message:
        Optional HTML body / prompt.
    discussion_type:
        ``"side_comment"`` (default, threaded replies disabled) or
        ``"threaded"``.
    published:
        Whether the discussion is visible to students immediately
        (default ``False``).
    """

    title: str
    message: str = ""
    discussion_type: str = "side_comment"
    published: bool = False

    def _discussion_payload(self) -> dict:
        return {
            "title": self.title,
            "message": self.message,
            "discussion_type": self.discussion_type,
            "published": self.published,
        }

    def create(self, api: CanvasAPI, course_id: int) -> dict:
        """Create the discussion topic in Canvas.

        Returns the Canvas API response for the created discussion.
        """
        return api.post(
            f"courses/{course_id}/discussion_topics", self._discussion_payload()
        )


# ---------------------------------------------------------------------------
# Page
# ---------------------------------------------------------------------------


@dataclass
class Page:
    """Represents a Canvas wiki page activity.

    Parameters
    ----------
    title:
        Page title (also used to generate the URL slug).
    body:
        HTML body content.
    editing_roles:
        Who can edit the page. One of ``"teachers"``, ``"students"``,
        ``"members"``, ``"public"`` (default ``"teachers"``).
    published:
        Whether the page is visible to students immediately
        (default ``False``).
    """

    title: str
    body: str = ""
    editing_roles: str = "teachers"
    published: bool = False

    def _page_payload(self) -> dict:
        return {
            "wiki_page": {
                "title": self.title,
                "body": self.body,
                "editing_roles": self.editing_roles,
                "published": self.published,
            }
        }

    def create(self, api: CanvasAPI, course_id: int) -> dict:
        """Create the wiki page in Canvas.

        Returns the Canvas API response for the created page.
        """
        return api.post(f"courses/{course_id}/pages", self._page_payload())
