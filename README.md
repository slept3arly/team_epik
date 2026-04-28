# Lumi

Lumi is a Flask + SQLite habit and routine tracker with dashboard views for habits, goals, productivity, stress, nutrition, sleep, and a small community feed.

## What this refactor changed

- Replaced the duplicated root-level HTML with a shared `templates/` layout.
- Moved styling into `static/css/main.css`.
- Moved login UI behavior into `static/js/main.js`.
- Replaced the monolithic backend with a thin Flask route layer plus reusable service modules.
- Added input validation, CSRF protection, password hashing, session-based login, and optional Gemini-backed routine analysis with a fallback when the API is unavailable.

## Run It

1. Install dependencies:

```bash
pip install flask matplotlib seaborn google-genai werkzeug
```

2. Create a `.env` file from the example:

```bash
cp .env.example .env
```

3. Put your values into `.env`:

```bash
FLASK_SECRET_KEY=your-random-secret
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-3-flash-preview
```

Use plain ASCII quotes only if you quote values. Do not paste curly quotes.
If you prefer, you can also use `GOOGLE_API_KEY` or `GOOGLE_GENAI_API_KEY` instead of `GEMINI_API_KEY`.

4. Start the app:

```bash
python3 flask_app.py
```

Open `http://127.0.0.1:5000`.

## Folder Structure

- `flask_app.py` Flask routes, CSRF, login/signup, and page orchestration
- `services/` validation, charts, and database/domain logic
- `templates/` shared base layout and page templates
- `static/css/` global styles
- `static/js/` login/signup behavior
- `instance/` local SQLite database created at runtime

## Notes

- `advance_lumi.py` and `Lumi_v6.0.py` are compatibility shims that point to the new service layer.
- If `GEMINI_API_KEY` is not set, routine analysis falls back to a deterministic local summary so the app still works.
- The Gemini integration now uses the supported `google-genai` package instead of the deprecated `google-generativeai` package.
- If you get a 400 from Gemini, try `GEMINI_MODEL=gemini-3-flash-preview` in `.env`; the app also retries that model automatically before falling back.
- If the service still says the key is missing, check for curly quotes in `.env` and restart the server after editing the file.
- The local `.env` file overrides inherited shell variables on startup.
- Passwords are stored as hashes, not plain text.
- The app loads `.env` automatically if it exists in the project root.
