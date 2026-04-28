from __future__ import annotations

import os
import random
import re
import sqlite3
import logging
from contextlib import contextmanager
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Iterable

from werkzeug.security import check_password_hash, generate_password_hash

from .validation import today_iso

logger = logging.getLogger(__name__)

try:
    from google import genai  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    genai = None


class LumiService:
    def __init__(self, db_path: str | os.PathLike[str] = "instance/lumi_data.db", api_key: str | None = None):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.api_key_source = None
        self.api_key = api_key or self._pick_api_key()
        model_env = os.getenv("GEMINI_MODEL", "").strip()
        self.model_candidates = [model_env] if model_env else ["gemini-3-flash-preview", "gemini-2.5-flash"]
        self.client = self._build_client()
        self._ensure_schema()
        self._ensure_guest_user()

        if self.api_key_source:
            logger.info("Using %s for Gemini authentication.", self.api_key_source)
            if os.getenv("GEMINI_API_KEY", "").strip() and os.getenv("GOOGLE_API_KEY", "").strip():
                logger.warning("Both GEMINI_API_KEY and GOOGLE_API_KEY are set. GEMINI_API_KEY takes priority.")

    @contextmanager
    def _connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
        finally:
            conn.close()

    def _build_client(self):
        if not genai or not self.api_key:
            return None

        try:
            return genai.Client(api_key=self.api_key)
        except Exception:
            return None

    def _pick_api_key(self) -> str:
        candidates = [
            ("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY", "").strip()),
            ("GOOGLE_API_KEY", os.getenv("GOOGLE_API_KEY", "").strip()),
            ("GOOGLE_GENAI_API_KEY", os.getenv("GOOGLE_GENAI_API_KEY", "").strip()),
        ]

        for name, value in candidates:
            if value:
                self.api_key_source = name
                return value

        return ""

    def _ensure_schema(self):
        with self._connection() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS habits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    habit TEXT NOT NULL,
                    frequency INTEGER NOT NULL,
                    completion_rate REAL NOT NULL DEFAULT 0,
                    last_completed TEXT,
                    created_at TEXT NOT NULL,
                    UNIQUE(user_id, habit),
                    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS habit_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    habit TEXT NOT NULL,
                    completed INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS analyses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    analysis_kind TEXT NOT NULL,
                    routine TEXT NOT NULL,
                    analysis_text TEXT NOT NULL,
                    rating REAL NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS goals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    category TEXT NOT NULL,
                    start_date TEXT NOT NULL,
                    end_date TEXT NOT NULL,
                    progress REAL NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    UNIQUE(user_id, title),
                    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS stress_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    stress_level INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL DEFAULT '',
                    priority TEXT NOT NULL,
                    due_date TEXT NOT NULL,
                    completed INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS nutrition_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    meal TEXT NOT NULL,
                    calories INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS sleep_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    sleep_duration REAL NOT NULL,
                    sleep_quality INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS community_posts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    category TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
                );
                """
            )
            conn.commit()

    def _ensure_guest_user(self):
        with self._connection() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO users (id, username, email, password_hash, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (1, "guest", "guest@lumi.local", "", datetime.utcnow().isoformat(timespec="seconds")),
            )
            conn.commit()

    def _fetchall(self, query: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
        with self._connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [dict(row) for row in rows]

    def _fetchone(self, query: str, params: tuple[Any, ...] = ()) -> dict[str, Any] | None:
        with self._connection() as conn:
            row = conn.execute(query, params).fetchone()
            return dict(row) if row else None

    def _execute(self, query: str, params: tuple[Any, ...] = ()) -> int:
        with self._connection() as conn:
            cursor = conn.execute(query, params)
            conn.commit()
            return cursor.lastrowid

    def get_guest_user_id(self) -> int:
        return 1

    def create_user(self, username: str, email: str, password: str) -> dict[str, Any]:
        password_hash = generate_password_hash(password)
        user_id = self._execute(
            """
            INSERT INTO users (username, email, password_hash, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (username, email, password_hash, datetime.utcnow().isoformat(timespec="seconds")),
        )
        return self.get_user_by_id(user_id)

    def get_user_by_id(self, user_id: int) -> dict[str, Any] | None:
        return self._fetchone("SELECT id, username, email, created_at FROM users WHERE id = ?", (user_id,))

    def get_user_by_identity(self, identity: str) -> dict[str, Any] | None:
        return self._fetchone(
            "SELECT id, username, email, password_hash, created_at FROM users WHERE username = ? OR email = ?",
            (identity, identity),
        )

    def authenticate_user(self, identity: str, password: str) -> dict[str, Any] | None:
        user = self.get_user_by_identity(identity)
        if not user:
            return None

        full_user = self._fetchone(
            "SELECT id, username, email, password_hash, created_at FROM users WHERE id = ?",
            (user["id"],),
        )
        if not full_user or not full_user.get("password_hash"):
            return None
        if not check_password_hash(full_user["password_hash"], password):
            return None
        return self.get_user_by_id(full_user["id"])

    def create_habit(self, user_id: int, habit: str, frequency: int) -> str:
        try:
            self._execute(
                """
                INSERT INTO habits (user_id, habit, frequency, completion_rate, last_completed, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (user_id, habit, frequency, 0, None, datetime.utcnow().isoformat(timespec="seconds")),
            )
            return f"Habit '{habit}' added successfully."
        except sqlite3.IntegrityError:
            return f"Habit '{habit}' already exists."

    def list_habits(self, user_id: int) -> list[dict[str, Any]]:
        return self._fetchall(
            """
            SELECT id, habit, frequency, completion_rate, last_completed
            FROM habits
            WHERE user_id = ?
            ORDER BY habit ASC
            """,
            (user_id,),
        )

    def record_habit_completion(self, user_id: int, habit: str, completed: bool) -> str:
        current = self._fetchone(
            "SELECT id, completion_rate FROM habits WHERE user_id = ? AND habit = ?",
            (user_id, habit),
        )
        if not current:
            return "Habit not found."

        new_rate = current["completion_rate"] * 0.8 + (20 if completed else 0)
        new_rate = max(0.0, min(100.0, round(new_rate, 1)))
        updates = [new_rate]
        query = "UPDATE habits SET completion_rate = ?"

        if completed:
            query += ", last_completed = ?"
            updates.append(today_iso())

        query += " WHERE user_id = ? AND habit = ?"
        updates.extend([user_id, habit])
        self._execute(query, tuple(updates))

        self._execute(
            """
            INSERT INTO habit_events (user_id, habit, completed, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (user_id, habit, int(completed), datetime.utcnow().isoformat(timespec="seconds")),
        )
        return "Habit updated successfully."

    def get_habit_frequency(self, user_id: int, days: int = 7) -> list[dict[str, Any]]:
        threshold = (date.today() - timedelta(days=days)).isoformat()
        return self._fetchall(
            """
            SELECT habit, COUNT(*) AS frequency
            FROM habit_events
            WHERE user_id = ? AND completed = 1 AND created_at >= ?
            GROUP BY habit
            ORDER BY frequency DESC, habit ASC
            """,
            (user_id, threshold),
        )

    def save_analysis(self, user_id: int, kind: str, routine: str, analysis_text: str, rating: float) -> None:
        self._execute(
            """
            INSERT INTO analyses (user_id, analysis_kind, routine, analysis_text, rating, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, kind, routine, analysis_text, rating, datetime.utcnow().isoformat(timespec="seconds")),
        )

    def get_recent_analyses(self, user_id: int, limit: int = 5) -> list[dict[str, Any]]:
        return self._fetchall(
            """
            SELECT id, analysis_kind, routine, analysis_text, rating, created_at
            FROM analyses
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (user_id, limit),
        )

    def get_routine_ratings(self, user_id: int, days: int = 7) -> list[dict[str, Any]]:
        threshold = (date.today() - timedelta(days=days)).isoformat()
        return self._fetchall(
            """
            SELECT created_at, rating
            FROM analyses
            WHERE user_id = ? AND analysis_kind = 'brief' AND created_at >= ?
            ORDER BY created_at ASC
            """,
            (user_id, threshold),
        )

    def analyze_routine(self, routine: str, *, detailed: bool = False) -> tuple[str, float]:
        cleaned_routine = routine.strip()
        prompt = self._build_prompt(cleaned_routine, detailed=detailed)
        analysis_text = self._generate_analysis(prompt, cleaned_routine, detailed=detailed)
        rating = self._extract_rating(analysis_text) if not detailed else 0.0
        return analysis_text, rating

    def _build_prompt(self, routine: str, *, detailed: bool) -> str:
        if detailed:
            return (
                "Review this routine and provide a practical, point-by-point improvement plan. "
                "Focus on pacing, recovery, focus, and sustainability.\n\n"
                f"Routine:\n{routine}"
            )

        return (
            "Analyze this daily routine and respond with exactly these sections:\n"
            "Summary: two short sentences.\n"
            "Suggestions: three concise improvement ideas.\n"
            "Rating: a single number from 1 to 10.\n\n"
            f"Routine:\n{routine}"
        )

    def _generate_analysis(self, prompt: str, routine: str, *, detailed: bool) -> str:
        if self.client is not None:
            last_error = None
            for model_name in self.model_candidates:
                if not model_name:
                    continue
                try:
                    response = self.client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                    )
                    text = (response.text or "").strip()
                    if text:
                        return text
                except Exception as exc:
                    last_error = exc
                    logger.warning("Gemini request failed for model %s: %s", model_name, exc)

            if last_error is not None:
                logger.warning("Gemini analysis fell back to local output after API failure.")

        return self._fallback_analysis(routine, detailed=detailed)

    def _fallback_analysis(self, routine: str, *, detailed: bool) -> str:
        words = re.findall(r"\w+", routine.lower())
        score = 8 if len(words) >= 80 else 6 if len(words) >= 40 else 5
        if detailed:
            return (
                "1. Keep the strongest parts of your routine consistent.\n"
                "2. Group low-value tasks together and protect focus blocks.\n"
                "3. Add a buffer for recovery, meals, and transitions.\n"
                "4. Review what drains energy most and reduce it first."
            )

        return (
            "Summary: Your routine has a clear structure, but it can be tightened for better energy management and focus.\n"
            "Suggestions: Reduce context switching, protect a deep-work block, and add a short recovery break after demanding tasks.\n"
            f"Rating: {score}"
        )

    def _extract_rating(self, analysis_text: str) -> float:
        match = re.search(r"Rating:\s*([0-9]+(?:\.[0-9]+)?)", analysis_text)
        if match:
            return max(1.0, min(10.0, float(match.group(1))))
        return 5.0

    def create_goal(self, user_id: int, title: str, description: str, category: str, start_date: str, end_date: str) -> str:
        try:
            self._execute(
                """
                INSERT INTO goals (user_id, title, description, category, start_date, end_date, progress, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (user_id, title, description, category, start_date, end_date, 0, datetime.utcnow().isoformat(timespec="seconds")),
            )
            return f"Goal '{title}' added successfully."
        except sqlite3.IntegrityError:
            return f"Goal '{title}' already exists."

    def update_goal_progress(self, user_id: int, goal_id: int, progress: float) -> str:
        self._execute(
            "UPDATE goals SET progress = ? WHERE id = ? AND user_id = ?",
            (progress, goal_id, user_id),
        )
        return "Goal progress updated successfully."

    def list_goals(self, user_id: int) -> list[dict[str, Any]]:
        return self._fetchall(
            """
            SELECT id, title, description, category, start_date, end_date, progress
            FROM goals
            WHERE user_id = ?
            ORDER BY end_date ASC, created_at DESC
            """,
            (user_id,),
        )

    def log_stress_level(self, user_id: int, stress_level: int) -> str:
        self._execute(
            """
            INSERT INTO stress_logs (user_id, stress_level, created_at)
            VALUES (?, ?, ?)
            """,
            (user_id, stress_level, datetime.utcnow().isoformat(timespec="seconds")),
        )
        return "Stress level logged successfully."

    def get_stress_levels(self, user_id: int, days: int = 7) -> list[dict[str, Any]]:
        threshold = (date.today() - timedelta(days=days)).isoformat()
        return self._fetchall(
            """
            SELECT created_at, stress_level
            FROM stress_logs
            WHERE user_id = ? AND created_at >= ?
            ORDER BY created_at ASC
            """,
            (user_id, threshold),
        )

    def get_meditation_recommendation(self) -> dict[str, str]:
        meditations = [
            {"title": "Mindful Breathing", "duration": "5 minutes", "audio": "https://example.com/mindful-breathing.mp3"},
            {"title": "Body Scan Relaxation", "duration": "10 minutes", "audio": "https://example.com/body-scan.mp3"},
            {"title": "Loving-Kindness Meditation", "duration": "15 minutes", "audio": "https://example.com/loving-kindness.mp3"},
        ]
        return random.choice(meditations)

    def create_task(self, user_id: int, title: str, description: str, priority: str, due_date: str) -> str:
        self._execute(
            """
            INSERT INTO tasks (user_id, title, description, priority, due_date, completed, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, title, description, priority, due_date, 0, datetime.utcnow().isoformat(timespec="seconds")),
        )
        return "Task added successfully."

    def list_tasks(self, user_id: int) -> list[dict[str, Any]]:
        return self._fetchall(
            """
            SELECT id, title, description, priority, due_date, completed
            FROM tasks
            WHERE user_id = ?
            ORDER BY completed ASC, due_date ASC
            """,
            (user_id,),
        )

    def update_task(self, user_id: int, task_id: int, completed: bool) -> str:
        self._execute(
            "UPDATE tasks SET completed = ? WHERE id = ? AND user_id = ?",
            (int(completed), task_id, user_id),
        )
        return "Task updated successfully."

    def log_nutrition(self, user_id: int, meal: str, calories: int) -> str:
        self._execute(
            """
            INSERT INTO nutrition_logs (user_id, meal, calories, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (user_id, meal, calories, datetime.utcnow().isoformat(timespec="seconds")),
        )
        return "Nutrition logged successfully."

    def get_nutrition_logs(self, user_id: int, days: int = 7) -> list[dict[str, Any]]:
        threshold = (date.today() - timedelta(days=days)).isoformat()
        return self._fetchall(
            """
            SELECT substr(created_at, 1, 10) AS created_on, SUM(calories) AS total_calories
            FROM nutrition_logs
            WHERE user_id = ? AND created_at >= ?
            GROUP BY substr(created_at, 1, 10)
            ORDER BY created_on ASC
            """,
            (user_id, threshold),
        )

    def log_sleep(self, user_id: int, sleep_duration: float, sleep_quality: int) -> str:
        self._execute(
            """
            INSERT INTO sleep_logs (user_id, sleep_duration, sleep_quality, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (user_id, sleep_duration, sleep_quality, datetime.utcnow().isoformat(timespec="seconds")),
        )
        return "Sleep logged successfully."

    def get_sleep_logs(self, user_id: int, days: int = 7) -> list[dict[str, Any]]:
        threshold = (date.today() - timedelta(days=days)).isoformat()
        return self._fetchall(
            """
            SELECT substr(created_at, 1, 10) AS created_on, sleep_duration, sleep_quality
            FROM sleep_logs
            WHERE user_id = ? AND created_at >= ?
            ORDER BY created_on ASC
            """,
            (user_id, threshold),
        )

    def create_post(self, user_id: int, title: str, content: str, category: str) -> str:
        self._execute(
            """
            INSERT INTO community_posts (user_id, title, content, category, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, title, content, category, datetime.utcnow().isoformat(timespec="seconds")),
        )
        return "Community post added successfully."

    def list_posts(self, limit: int = 10) -> list[dict[str, Any]]:
        return self._fetchall(
            """
            SELECT community_posts.id, community_posts.title, community_posts.content, community_posts.category,
                   community_posts.created_at, users.username AS author
            FROM community_posts
            JOIN users ON users.id = community_posts.user_id
            ORDER BY community_posts.created_at DESC
            LIMIT ?
            """,
            (limit,),
        )

    def build_overview_summary(self, user_id: int) -> list[str]:
        habits = self._fetchone("SELECT COUNT(*) AS count FROM habits WHERE user_id = ?", (user_id,))
        goals = self._fetchone("SELECT COUNT(*) AS count FROM goals WHERE user_id = ?", (user_id,))
        tasks = self._fetchone("SELECT COUNT(*) AS count FROM tasks WHERE user_id = ? AND completed = 0", (user_id,))
        stress = self._fetchone("SELECT AVG(stress_level) AS average FROM stress_logs WHERE user_id = ?", (user_id,))
        recent = self.get_recent_analyses(user_id, limit=1)

        summary = [
            f"Tracked habits: {habits['count'] if habits else 0}",
            f"Active goals: {goals['count'] if goals else 0}",
            f"Open tasks: {tasks['count'] if tasks else 0}",
        ]
        if stress and stress.get("average") is not None:
            summary.append(f"Average stress level: {round(float(stress['average']), 1)} / 10")
        if recent:
            summary.append(f"Latest routine rating: {recent[0]['rating']} / 10")
        return summary
