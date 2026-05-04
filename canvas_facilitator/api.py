"""Canvas LMS REST API client."""

import requests


class CanvasAPIError(Exception):
    """Raised when the Canvas LMS API returns an error response."""

    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        super().__init__(f"Canvas API error {status_code}: {message}")


class CanvasAPI:
    """Lightweight wrapper around the Canvas LMS REST API.

    Parameters
    ----------
    base_url:
        Root URL of your Canvas instance, e.g. ``https://canvas.example.com``.
    api_token:
        A Canvas *access token* (generated in Account → Settings → New Access Token).
    """

    def __init__(self, base_url: str, api_token: str) -> None:
        self.base_url = base_url.rstrip("/")
        self._session = requests.Session()
        self._session.headers.update(
            {
                "Authorization": f"Bearer {api_token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _url(self, path: str) -> str:
        return f"{self.base_url}/api/v1/{path.lstrip('/')}"

    def _raise_for_status(self, response: requests.Response) -> None:
        if not response.ok:
            try:
                detail = response.json()
            except Exception:
                detail = response.text
            raise CanvasAPIError(response.status_code, str(detail))

    def get(self, path: str, **params) -> dict | list:
        """Send a GET request and return parsed JSON."""
        response = self._session.get(self._url(path), params=params)
        self._raise_for_status(response)
        return response.json()

    def post(self, path: str, payload: dict) -> dict:
        """Send a POST request and return parsed JSON."""
        response = self._session.post(self._url(path), json=payload)
        self._raise_for_status(response)
        return response.json()

    def put(self, path: str, payload: dict) -> dict:
        """Send a PUT request and return parsed JSON."""
        response = self._session.put(self._url(path), json=payload)
        self._raise_for_status(response)
        return response.json()

    def delete(self, path: str) -> dict:
        """Send a DELETE request and return parsed JSON."""
        response = self._session.delete(self._url(path))
        self._raise_for_status(response)
        return response.json()

    # ------------------------------------------------------------------
    # Course helpers
    # ------------------------------------------------------------------

    def list_courses(self) -> list:
        """Return the list of courses the authenticated user can access."""
        return self.get("courses")

    def get_course(self, course_id: int) -> dict:
        """Return a single course by *course_id*."""
        return self.get(f"courses/{course_id}")
