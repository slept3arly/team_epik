# Lumi

Lumi is a prototype Flask and SQLite web application for tracking habits, routines, goals, productivity, stress, nutrition, sleep, and community updates in one dashboard. It includes optional Gemini-powered routine analysis with a local fallback when the API is unavailable.

## Features

- User sign-up and login with session-based authentication
- Habit tracking with completion logging and frequency summaries
- Routine analysis with brief and detailed feedback modes
- Goal tracking with category, date range, and progress updates
- Productivity task tracking with priority and due dates
- Stress logging with trend charts and meditation suggestions
- Nutrition and sleep logging with visual summaries
- Lightweight community feed for posting updates and reading recent entries
- Dashboard and overview pages with embedded charts rendered as PNG images

## Tech Stack

- Python
- Flask
- SQLite
- Jinja2 templates
- Bootstrap 4
- Matplotlib
- Seaborn
- Google GenAI API via `google-genai` for optional routine analysis

## Project Structure

- `flask_app.py` Flask application, routes, authentication, and request handling
- `services/` domain logic, SQLite persistence, validation, and chart generation
- `templates/` shared layout and page templates
- `static/css/` application styling
- `static/js/` client-side login and sign-up behavior
- `instance/` runtime SQLite database created locally
- `Lumi_v6.0.py` and `advance_lumi.py` compatibility shims for the service layer

## How to Run Locally

1. Create and activate a Python virtual environment.
2. Install dependencies:

```bash
pip install flask matplotlib seaborn google-genai werkzeug
```

3. Copy the example environment file:

```bash
cp .env.example .env
```

4. Set the required values in `.env`:

```bash
FLASK_SECRET_KEY=your-random-secret
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-3-flash-preview
```

5. Start the application:

```bash
python3 flask_app.py
```

6. Open `http://127.0.0.1:5000`.

If you do not provide a Gemini API key, routine analysis still works through the built-in fallback logic.

## Key Technical Concepts

- Session-based auth with password hashing via Werkzeug
- CSRF protection for form submissions
- Input validation and normalization before database writes
- SQLite schema initialization at startup
- Optional AI integration with retry and deterministic fallback
- Server-generated charts encoded directly into templates

## Limitations

- This is a prototype, not a production-ready product.
- Data is stored locally in SQLite with no migration layer.
- There is no password reset, email verification, or role-based access control.
- Community posts are lightweight and not moderated.
- Meditation links are placeholder URLs rather than production media.
- The app currently supports create/update flows, but not full edit/delete management for every data type.

## Future Improvements

- Add edit and delete actions across all tracked entities
- Introduce database migrations and a production-ready deployment path
- Add moderation, search, and filtering for community content
- Replace placeholder meditation resources with maintained content
- Add export/reporting features for personal tracking data
