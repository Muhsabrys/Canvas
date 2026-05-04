"""Unit tests for canvas_facilitator.cli."""

import json
import os
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from canvas_facilitator.api import CanvasAPIError
from canvas_facilitator.cli import main


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CANVAS_BASE_URL", "https://canvas.example.com")
    monkeypatch.setenv("CANVAS_API_TOKEN", "fake_token")


# ---------------------------------------------------------------------------
# Guard: missing env vars
# ---------------------------------------------------------------------------


class TestMissingEnvVars:
    def test_exits_when_env_missing(self, runner: CliRunner) -> None:
        result = runner.invoke(
            main,
            ["list-courses"],
            env={"CANVAS_BASE_URL": "", "CANVAS_API_TOKEN": ""},
        )
        assert result.exit_code != 0
        assert "CANVAS_BASE_URL" in result.output or "CANVAS_API_TOKEN" in result.output


# ---------------------------------------------------------------------------
# list-courses
# ---------------------------------------------------------------------------


class TestListCourses:
    def test_prints_course_list(self, runner: CliRunner, env: None) -> None:
        courses = [{"id": 1, "name": "Math"}, {"id": 2, "name": "Science"}]
        with patch("canvas_facilitator.cli.CanvasAPI") as MockAPI:
            MockAPI.return_value.list_courses.return_value = courses
            result = runner.invoke(main, ["list-courses"])
        assert result.exit_code == 0
        assert "Math" in result.output
        assert "Science" in result.output

    def test_exits_on_api_error(self, runner: CliRunner, env: None) -> None:
        with patch("canvas_facilitator.cli.CanvasAPI") as MockAPI:
            MockAPI.return_value.list_courses.side_effect = CanvasAPIError(401, "Unauthorized")
            result = runner.invoke(main, ["list-courses"])
        assert result.exit_code != 0


# ---------------------------------------------------------------------------
# create-quiz
# ---------------------------------------------------------------------------


class TestCreateQuiz:
    def test_creates_quiz_and_prints_json(self, runner: CliRunner, env: None) -> None:
        quiz_resp = {"id": 42, "title": "Test Quiz"}
        with patch("canvas_facilitator.cli.CanvasAPI") as MockAPI:
            MockAPI.return_value.post.return_value = quiz_resp
            result = runner.invoke(
                main,
                ["create-quiz", "101", "--title", "Test Quiz"],
            )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["id"] == 42

    def test_loads_questions_from_json_file(
        self, runner: CliRunner, env: None
    ) -> None:
        questions = [
            {
                "question_text": "Q1?",
                "question_type": "true_false_question",
                "points_possible": 2.0,
                "answers": [{"text": "True", "weight": 100}],
            }
        ]
        quiz_resp = {"id": 55, "title": "Quiz with Q"}
        with runner.isolated_filesystem():
            with open("questions.json", "w") as fh:
                json.dump(questions, fh)
            with patch("canvas_facilitator.cli.CanvasAPI") as MockAPI:
                MockAPI.return_value.post.return_value = quiz_resp
                result = runner.invoke(
                    main,
                    [
                        "create-quiz",
                        "101",
                        "--title",
                        "Quiz with Q",
                        "--questions-json",
                        "questions.json",
                    ],
                )
        assert result.exit_code == 0

    def test_exits_on_api_error(self, runner: CliRunner, env: None) -> None:
        with patch("canvas_facilitator.cli.CanvasAPI") as MockAPI:
            MockAPI.return_value.post.side_effect = CanvasAPIError(403, "Forbidden")
            result = runner.invoke(
                main, ["create-quiz", "101", "--title", "Fail Quiz"]
            )
        assert result.exit_code != 0


# ---------------------------------------------------------------------------
# create-assignment
# ---------------------------------------------------------------------------


class TestCreateAssignment:
    def test_creates_assignment_and_prints_json(
        self, runner: CliRunner, env: None
    ) -> None:
        assign_resp = {"id": 77, "name": "Homework 1"}
        with patch("canvas_facilitator.cli.CanvasAPI") as MockAPI:
            MockAPI.return_value.post.return_value = assign_resp
            result = runner.invoke(
                main,
                ["create-assignment", "101", "--title", "Homework 1"],
            )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["id"] == 77

    def test_submission_types_split_by_comma(
        self, runner: CliRunner, env: None
    ) -> None:
        assign_resp = {"id": 78}
        with patch("canvas_facilitator.cli.CanvasAPI") as MockAPI:
            MockAPI.return_value.post.return_value = assign_resp
            result = runner.invoke(
                main,
                [
                    "create-assignment",
                    "101",
                    "--title",
                    "Multi",
                    "--submission-types",
                    "online_text_entry,online_url",
                ],
            )
        assert result.exit_code == 0


# ---------------------------------------------------------------------------
# create-discussion
# ---------------------------------------------------------------------------


class TestCreateDiscussion:
    def test_creates_discussion_and_prints_json(
        self, runner: CliRunner, env: None
    ) -> None:
        disc_resp = {"id": 90, "title": "Weekly Discussion"}
        with patch("canvas_facilitator.cli.CanvasAPI") as MockAPI:
            MockAPI.return_value.post.return_value = disc_resp
            result = runner.invoke(
                main,
                ["create-discussion", "101", "--title", "Weekly Discussion"],
            )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["id"] == 90


# ---------------------------------------------------------------------------
# create-page
# ---------------------------------------------------------------------------


class TestCreatePage:
    def test_creates_page_and_prints_json(
        self, runner: CliRunner, env: None
    ) -> None:
        page_resp = {"url": "syllabus", "title": "Syllabus"}
        with patch("canvas_facilitator.cli.CanvasAPI") as MockAPI:
            MockAPI.return_value.post.return_value = page_resp
            result = runner.invoke(
                main,
                ["create-page", "101", "--title", "Syllabus"],
            )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["title"] == "Syllabus"

    def test_exits_on_api_error(self, runner: CliRunner, env: None) -> None:
        with patch("canvas_facilitator.cli.CanvasAPI") as MockAPI:
            MockAPI.return_value.post.side_effect = CanvasAPIError(500, "Server Error")
            result = runner.invoke(
                main, ["create-page", "101", "--title", "Error Page"]
            )
        assert result.exit_code != 0
