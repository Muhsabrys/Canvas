"""Unit tests for canvas_facilitator.activities."""

from unittest.mock import MagicMock, call, patch

import pytest

from canvas_facilitator.activities import (
    Assignment,
    Discussion,
    Page,
    Quiz,
    QuizQuestion,
)
from canvas_facilitator.api import CanvasAPI


COURSE_ID = 101


@pytest.fixture()
def mock_api() -> MagicMock:
    return MagicMock(spec=CanvasAPI)


# ---------------------------------------------------------------------------
# QuizQuestion
# ---------------------------------------------------------------------------


class TestQuizQuestion:
    def test_to_payload_defaults(self) -> None:
        q = QuizQuestion(question_text="What is 2+2?")
        payload = q.to_payload()
        assert payload["question"]["question_text"] == "What is 2+2?"
        assert payload["question"]["question_type"] == "multiple_choice_question"
        assert payload["question"]["points_possible"] == 1.0
        assert payload["question"]["answers"] == []

    def test_to_payload_custom_values(self) -> None:
        answers = [{"text": "True", "weight": 100}, {"text": "False", "weight": 0}]
        q = QuizQuestion(
            question_text="Is Python fun?",
            question_type="true_false_question",
            points_possible=5.0,
            answers=answers,
        )
        payload = q.to_payload()
        assert payload["question"]["question_type"] == "true_false_question"
        assert payload["question"]["points_possible"] == 5.0
        assert payload["question"]["answers"] == answers


# ---------------------------------------------------------------------------
# Quiz
# ---------------------------------------------------------------------------


class TestQuiz:
    def test_create_without_questions(self, mock_api: MagicMock) -> None:
        mock_api.post.return_value = {"id": 10, "title": "My Quiz"}
        quiz = Quiz(title="My Quiz", description="<p>Instructions</p>")
        result = quiz.create(mock_api, COURSE_ID)
        assert result["id"] == 10
        # Only one POST call (to create the quiz itself)
        mock_api.post.assert_called_once_with(
            f"courses/{COURSE_ID}/quizzes",
            {
                "quiz": {
                    "title": "My Quiz",
                    "description": "<p>Instructions</p>",
                    "quiz_type": "assignment",
                    "shuffle_answers": False,
                }
            },
        )

    def test_create_with_time_limit(self, mock_api: MagicMock) -> None:
        mock_api.post.return_value = {"id": 11, "title": "Timed Quiz"}
        quiz = Quiz(title="Timed Quiz", time_limit=30)
        quiz.create(mock_api, COURSE_ID)
        payload = mock_api.post.call_args_list[0][0][1]
        assert payload["quiz"]["time_limit"] == 30

    def test_create_without_time_limit_omits_key(self, mock_api: MagicMock) -> None:
        mock_api.post.return_value = {"id": 12}
        quiz = Quiz(title="No Limit Quiz")
        quiz.create(mock_api, COURSE_ID)
        payload = mock_api.post.call_args_list[0][0][1]
        assert "time_limit" not in payload["quiz"]

    def test_create_posts_questions_after_quiz(self, mock_api: MagicMock) -> None:
        quiz_response = {"id": 20}
        mock_api.post.return_value = quiz_response
        q1 = QuizQuestion(question_text="Q1?")
        q2 = QuizQuestion(question_text="Q2?")
        quiz = Quiz(title="Quiz with Questions", questions=[q1, q2])
        quiz.create(mock_api, COURSE_ID)
        assert mock_api.post.call_count == 3  # 1 quiz + 2 questions

        # Check question endpoint
        question_calls = mock_api.post.call_args_list[1:]
        for c in question_calls:
            assert f"courses/{COURSE_ID}/quizzes/20/questions" in c[0][0]

    def test_shuffle_answers_flag(self, mock_api: MagicMock) -> None:
        mock_api.post.return_value = {"id": 13}
        quiz = Quiz(title="Shuffled", shuffle_answers=True)
        quiz.create(mock_api, COURSE_ID)
        payload = mock_api.post.call_args_list[0][0][1]
        assert payload["quiz"]["shuffle_answers"] is True


# ---------------------------------------------------------------------------
# Assignment
# ---------------------------------------------------------------------------


class TestAssignment:
    def test_create_defaults(self, mock_api: MagicMock) -> None:
        mock_api.post.return_value = {"id": 50, "name": "Homework 1"}
        assignment = Assignment(title="Homework 1")
        result = assignment.create(mock_api, COURSE_ID)
        assert result["id"] == 50
        mock_api.post.assert_called_once()
        path, payload = mock_api.post.call_args[0]
        assert path == f"courses/{COURSE_ID}/assignments"
        assert payload["assignment"]["name"] == "Homework 1"
        assert payload["assignment"]["points_possible"] == 100.0
        assert payload["assignment"]["submission_types"] == ["online_upload"]
        assert payload["assignment"]["grading_type"] == "points"
        assert payload["assignment"]["published"] is False
        assert "due_at" not in payload["assignment"]

    def test_create_with_due_at(self, mock_api: MagicMock) -> None:
        mock_api.post.return_value = {"id": 51}
        assignment = Assignment(title="Essay", due_at="2024-12-01T23:59:00Z")
        assignment.create(mock_api, COURSE_ID)
        payload = mock_api.post.call_args[0][1]
        assert payload["assignment"]["due_at"] == "2024-12-01T23:59:00Z"

    def test_create_published(self, mock_api: MagicMock) -> None:
        mock_api.post.return_value = {"id": 52}
        assignment = Assignment(title="Published HW", published=True)
        assignment.create(mock_api, COURSE_ID)
        payload = mock_api.post.call_args[0][1]
        assert payload["assignment"]["published"] is True

    def test_custom_submission_types(self, mock_api: MagicMock) -> None:
        mock_api.post.return_value = {"id": 53}
        assignment = Assignment(
            title="Online",
            submission_types=["online_text_entry", "online_url"],
        )
        assignment.create(mock_api, COURSE_ID)
        payload = mock_api.post.call_args[0][1]
        assert payload["assignment"]["submission_types"] == [
            "online_text_entry",
            "online_url",
        ]


# ---------------------------------------------------------------------------
# Discussion
# ---------------------------------------------------------------------------


class TestDiscussion:
    def test_create_defaults(self, mock_api: MagicMock) -> None:
        mock_api.post.return_value = {"id": 70, "title": "Class Discussion"}
        discussion = Discussion(title="Class Discussion")
        result = discussion.create(mock_api, COURSE_ID)
        assert result["id"] == 70
        mock_api.post.assert_called_once()
        path, payload = mock_api.post.call_args[0]
        assert path == f"courses/{COURSE_ID}/discussion_topics"
        assert payload["title"] == "Class Discussion"
        assert payload["discussion_type"] == "side_comment"
        assert payload["published"] is False

    def test_create_threaded(self, mock_api: MagicMock) -> None:
        mock_api.post.return_value = {"id": 71}
        discussion = Discussion(title="Threaded", discussion_type="threaded")
        discussion.create(mock_api, COURSE_ID)
        payload = mock_api.post.call_args[0][1]
        assert payload["discussion_type"] == "threaded"

    def test_create_with_message(self, mock_api: MagicMock) -> None:
        mock_api.post.return_value = {"id": 72}
        discussion = Discussion(title="Topic", message="<p>Discuss!</p>")
        discussion.create(mock_api, COURSE_ID)
        payload = mock_api.post.call_args[0][1]
        assert payload["message"] == "<p>Discuss!</p>"


# ---------------------------------------------------------------------------
# Page
# ---------------------------------------------------------------------------


class TestPage:
    def test_create_defaults(self, mock_api: MagicMock) -> None:
        mock_api.post.return_value = {"url": "syllabus", "title": "Syllabus"}
        page = Page(title="Syllabus")
        result = page.create(mock_api, COURSE_ID)
        assert result["title"] == "Syllabus"
        mock_api.post.assert_called_once()
        path, payload = mock_api.post.call_args[0]
        assert path == f"courses/{COURSE_ID}/pages"
        assert payload["wiki_page"]["title"] == "Syllabus"
        assert payload["wiki_page"]["editing_roles"] == "teachers"
        assert payload["wiki_page"]["published"] is False

    def test_create_with_body(self, mock_api: MagicMock) -> None:
        mock_api.post.return_value = {"url": "intro"}
        page = Page(title="Intro", body="<h1>Welcome</h1>")
        page.create(mock_api, COURSE_ID)
        payload = mock_api.post.call_args[0][1]
        assert payload["wiki_page"]["body"] == "<h1>Welcome</h1>"

    def test_create_student_editable(self, mock_api: MagicMock) -> None:
        mock_api.post.return_value = {"url": "notes"}
        page = Page(title="Notes", editing_roles="students")
        page.create(mock_api, COURSE_ID)
        payload = mock_api.post.call_args[0][1]
        assert payload["wiki_page"]["editing_roles"] == "students"

    def test_create_published(self, mock_api: MagicMock) -> None:
        mock_api.post.return_value = {"url": "pub-page"}
        page = Page(title="Published Page", published=True)
        page.create(mock_api, COURSE_ID)
        payload = mock_api.post.call_args[0][1]
        assert payload["wiki_page"]["published"] is True
