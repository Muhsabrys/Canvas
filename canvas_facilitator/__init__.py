"""Canvas LMS activity facilitator package."""

from .api import CanvasAPI
from .activities import Quiz, Assignment, Discussion, Page

__all__ = ["CanvasAPI", "Quiz", "Assignment", "Discussion", "Page"]
__version__ = "0.1.0"
