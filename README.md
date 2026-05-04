# Canvas Facilitator

A Python tool that **facilitates creating Canvas LMS activities** — quizzes, assignments, discussions, and pages — via the [Canvas REST API](https://canvas.instructure.com/doc/api/).

## Features

- Thin, well-tested wrapper around the Canvas REST API (`CanvasAPI`)
- Dataclass-based activity builders: **Quiz**, **Assignment**, **Discussion**, **Page**
- Add multiple-choice / true-false / short-answer questions to quizzes from Python or a JSON file
- Command-line interface (`canvas-facilitator`) for quick, scriptable activity creation

## Installation

```bash
pip install -e .
```

## Configuration

Export your Canvas credentials as environment variables:

```bash
export CANVAS_BASE_URL="https://canvas.example.com"
export CANVAS_API_TOKEN="your_access_token_here"
```

You can generate an access token in Canvas under **Account → Settings → New Access Token**.

## CLI Usage

### List accessible courses

```bash
canvas-facilitator list-courses
```

### Create a quiz

```bash
canvas-facilitator create-quiz 12345 \
  --title "Week 1 Quiz" \
  --quiz-type practice_quiz \
  --time-limit 20 \
  --shuffle-answers \
  --questions-json questions.json
```

Example `questions.json`:

```json
[
  {
    "question_text": "What is the capital of France?",
    "question_type": "multiple_choice_question",
    "points_possible": 1.0,
    "answers": [
      {"text": "Paris",  "weight": 100},
      {"text": "London", "weight": 0},
      {"text": "Berlin", "weight": 0}
    ]
  }
]
```

### Create an assignment

```bash
canvas-facilitator create-assignment 12345 \
  --title "Essay Assignment" \
  --points 50 \
  --submission-types online_text_entry \
  --due-at "2024-12-01T23:59:00Z" \
  --published
```

### Create a discussion topic

```bash
canvas-facilitator create-discussion 12345 \
  --title "Week 1 Discussion" \
  --message "<p>Share your thoughts on the reading.</p>" \
  --discussion-type threaded
```

### Create a wiki page

```bash
canvas-facilitator create-page 12345 \
  --title "Course Syllabus" \
  --body "<h1>Welcome</h1><p>This course covers...</p>" \
  --published
```

## Python API Usage

```python
from canvas_facilitator import CanvasAPI, Quiz, QuizQuestion, Assignment, Discussion, Page

api = CanvasAPI("https://canvas.example.com", "your_token")
course_id = 12345

# Create a quiz with questions
quiz = Quiz(
    title="Chapter 1 Quiz",
    quiz_type="assignment",
    time_limit=30,
    questions=[
        QuizQuestion(
            question_text="Is Python interpreted?",
            question_type="true_false_question",
            points_possible=2.0,
            answers=[
                {"text": "True",  "weight": 100},
                {"text": "False", "weight": 0},
            ],
        )
    ],
)
result = quiz.create(api, course_id)
print(f"Quiz created with ID {result['id']}")

# Create an assignment
assignment = Assignment(
    title="Final Project",
    points_possible=100,
    submission_types=["online_upload"],
    due_at="2024-12-15T23:59:00Z",
    published=True,
)
result = assignment.create(api, course_id)

# Create a discussion
discussion = Discussion(title="Intro Discussion", discussion_type="threaded")
result = discussion.create(api, course_id)

# Create a page
page = Page(title="Resources", body="<ul><li>Link 1</li></ul>")
result = page.create(api, course_id)
```

## Development

Install dependencies and run the tests:

```bash
pip install -e .
pip install pytest
pytest
```
