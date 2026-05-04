"""Unit tests for canvas_facilitator.api."""

from unittest.mock import MagicMock, patch

import pytest

from canvas_facilitator.api import CanvasAPI, CanvasAPIError


BASE_URL = "https://canvas.example.com"
TOKEN = "test_token_abc123"


@pytest.fixture()
def api() -> CanvasAPI:
    return CanvasAPI(BASE_URL, TOKEN)


class TestCanvasAPIInit:
    def test_base_url_trailing_slash_stripped(self) -> None:
        client = CanvasAPI("https://canvas.example.com/", TOKEN)
        assert client.base_url == "https://canvas.example.com"

    def test_authorization_header(self, api: CanvasAPI) -> None:
        assert api._session.headers["Authorization"] == f"Bearer {TOKEN}"

    def test_content_type_header(self, api: CanvasAPI) -> None:
        assert api._session.headers["Content-Type"] == "application/json"


class TestCanvasAPIUrl:
    def test_url_leading_slash(self, api: CanvasAPI) -> None:
        assert api._url("/courses") == f"{BASE_URL}/api/v1/courses"

    def test_url_no_slash(self, api: CanvasAPI) -> None:
        assert api._url("courses/123") == f"{BASE_URL}/api/v1/courses/123"


class TestRaiseForStatus:
    def test_ok_response_does_not_raise(self, api: CanvasAPI) -> None:
        mock_response = MagicMock()
        mock_response.ok = True
        api._raise_for_status(mock_response)  # should not raise

    def test_error_response_raises_canvas_api_error(self, api: CanvasAPI) -> None:
        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status_code = 401
        mock_response.json.return_value = {"message": "Invalid token"}
        with pytest.raises(CanvasAPIError) as exc_info:
            api._raise_for_status(mock_response)
        assert "401" in str(exc_info.value)

    def test_error_response_falls_back_to_text(self, api: CanvasAPI) -> None:
        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status_code = 500
        mock_response.json.side_effect = ValueError("no json")
        mock_response.text = "Internal Server Error"
        with pytest.raises(CanvasAPIError) as exc_info:
            api._raise_for_status(mock_response)
        assert "500" in str(exc_info.value)


class TestGet:
    def test_get_calls_session_and_returns_json(self, api: CanvasAPI) -> None:
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = [{"id": 1, "name": "Course A"}]
        with patch.object(api._session, "get", return_value=mock_response) as mock_get:
            result = api.get("courses")
        mock_get.assert_called_once_with(f"{BASE_URL}/api/v1/courses", params={})
        assert result == [{"id": 1, "name": "Course A"}]

    def test_get_raises_on_error(self, api: CanvasAPI) -> None:
        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status_code = 404
        mock_response.json.return_value = {"message": "Not found"}
        with patch.object(api._session, "get", return_value=mock_response):
            with pytest.raises(CanvasAPIError):
                api.get("courses/9999")


class TestPost:
    def test_post_sends_payload_and_returns_json(self, api: CanvasAPI) -> None:
        payload = {"quiz": {"title": "Test Quiz"}}
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {"id": 42, "title": "Test Quiz"}
        with patch.object(api._session, "post", return_value=mock_response) as mock_post:
            result = api.post("courses/1/quizzes", payload)
        mock_post.assert_called_once_with(
            f"{BASE_URL}/api/v1/courses/1/quizzes", json=payload
        )
        assert result["id"] == 42


class TestPut:
    def test_put_sends_payload_and_returns_json(self, api: CanvasAPI) -> None:
        payload = {"assignment": {"name": "Updated"}}
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {"id": 7, "name": "Updated"}
        with patch.object(api._session, "put", return_value=mock_response) as mock_put:
            result = api.put("courses/1/assignments/7", payload)
        mock_put.assert_called_once_with(
            f"{BASE_URL}/api/v1/courses/1/assignments/7", json=payload
        )
        assert result["name"] == "Updated"


class TestDelete:
    def test_delete_returns_json(self, api: CanvasAPI) -> None:
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {"deleted": True}
        with patch.object(api._session, "delete", return_value=mock_response) as mock_del:
            result = api.delete("courses/1/quizzes/42")
        mock_del.assert_called_once_with(f"{BASE_URL}/api/v1/courses/1/quizzes/42")
        assert result == {"deleted": True}


class TestCourseHelpers:
    def test_list_courses_calls_get(self, api: CanvasAPI) -> None:
        with patch.object(api, "get", return_value=[]) as mock_get:
            api.list_courses()
        mock_get.assert_called_once_with("courses")

    def test_get_course_calls_get_with_id(self, api: CanvasAPI) -> None:
        with patch.object(api, "get", return_value={"id": 5}) as mock_get:
            api.get_course(5)
        mock_get.assert_called_once_with("courses/5")
