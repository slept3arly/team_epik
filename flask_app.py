from __future__ import annotations

import os
import sqlite3
import secrets
from pathlib import Path
from typing import Any

from flask import Flask, abort, flash, g, jsonify, redirect, render_template, request, session, url_for

from services import LumiService
from services.charts import bar_chart, line_chart, scatter_chart
from services.validation import clamp_float, clamp_int, parse_bool, parse_choice, parse_date, require_text


def load_dotenv_file(path: str = ".env") -> None:
    env_path = Path(path)
    if not env_path.exists():
        return

    quote_chars = "\"'“”‘’"
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.lstrip("\ufeff").strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip(quote_chars)
        if key:
            # Prefer the repo-local .env file over inherited shell values.
            os.environ[key] = value


load_dotenv_file()

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = os.getenv("FLASK_SECRET_KEY") or secrets.token_hex(32)
app.config["MAX_CONTENT_LENGTH"] = 1 * 1024 * 1024

service = LumiService()

NAV_ITEMS = [
    ("Dashboard", "index", "/"),
    ("Habit Tracking", "habit_tracking", "/habit_tracking"),
    ("Routine Analysis", "routine_analysis", "/routine_analysis"),
    ("Goals", "goals", "/goals"),
    ("Overview", "overview", "/overview"),
    ("Stress Management", "stress_management", "/stress_management"),
    ("Productivity", "productivity", "/productivity"),
    ("Health & Wellness", "health_wellness", "/health_wellness"),
    ("Community", "community", "/community"),
]

GOAL_CATEGORIES = ("health", "fitness", "productivity", "personal", "other")
TASK_PRIORITIES = ("high", "medium", "low")
POST_CATEGORIES = ("habits", "productivity", "wellness", "motivation", "other")


def current_user_id() -> int:
    return int(session.get("user_id") or service.get_guest_user_id())


def current_user() -> dict[str, Any]:
    user = getattr(g, "current_user", None)
    if user:
        return user
    guest = service.get_user_by_id(service.get_guest_user_id())
    return guest or {"id": service.get_guest_user_id(), "username": "guest"}


def render_page(template_name: str, *, active_page: str, **context):
    return render_template(
        template_name,
        active_page=active_page,
        nav_items=NAV_ITEMS,
        current_user=current_user(),
        is_authenticated=session.get("user_id") not in (None, service.get_guest_user_id()),
        **context,
    )


def csrf_token():
    token = session.get("_csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["_csrf_token"] = token
    return token


app.jinja_env.globals["csrf_token"] = csrf_token


@app.context_processor
def inject_globals():
    return {"csrf_token": csrf_token}


@app.before_request
def load_user_and_protect():
    session.setdefault("user_id", service.get_guest_user_id())
    user = service.get_user_by_id(int(session.get("user_id")))
    if user is None:
        session["user_id"] = service.get_guest_user_id()
        user = service.get_user_by_id(service.get_guest_user_id())
    g.current_user = user

    if request.method == "POST":
        expected = session.get("_csrf_token")
        provided = request.form.get("_csrf_token") or request.headers.get("X-CSRFToken")
        if not expected or not provided or provided != expected:
            abort(400)


@app.errorhandler(400)
def bad_request(_error):
    return render_page("index.html", active_page="index", overview_summary=["The request could not be processed."]), 400


def _handle_post_success(message: str, *, category: str = "success"):
    flash(message, category)


def _handle_post_error(exc: Exception):
    flash(str(exc), "danger")


@app.route("/")
def index():
    user_id = current_user_id()
    summary = service.build_overview_summary(user_id)
    recent_posts = service.list_posts(limit=3)
    recent_analyses = service.get_recent_analyses(user_id, limit=3)
    return render_page(
        "index.html",
        active_page="index",
        overview_summary=summary,
        recent_posts=recent_posts,
        recent_analyses=recent_analyses,
    )


@app.route("/welcome")
def welcome():
    return render_page("welcome_page.html", active_page="welcome")


@app.route("/habit_tracking", methods=["GET", "POST"])
def habit_tracking():
    user_id = current_user_id()

    if request.method == "POST":
        try:
            habit = require_text(request.form.get("habit"), "Habit name", max_length=80)
            frequency = clamp_int(request.form.get("frequency"), "Daily frequency", minimum=1, maximum=12)
            if "add_habit" in request.form:
                _handle_post_success(service.create_habit(user_id, habit, frequency))
            elif "update_habit" in request.form:
                completed = parse_bool(request.form.get("completed"))
                _handle_post_success(service.record_habit_completion(user_id, habit, completed))
            else:
                raise ValueError("Unknown habit action.")
        except Exception as exc:
            _handle_post_error(exc)
        return redirect(url_for("habit_tracking"))

    habits = service.list_habits(user_id)
    return render_page("habit_tracking.html", active_page="habit_tracking", habits=habits)


@app.route("/routine_analysis", methods=["GET", "POST"])
def routine_analysis():
    user_id = current_user_id()
    brief_analysis = None
    detailed_analysis = None

    if request.method == "POST":
        try:
            routine = require_text(
                request.form.get("routine"),
                "Routine",
                max_length=3000,
                allow_newlines=True,
            )
            if "analyze_routine" in request.form:
                brief_analysis, rating = service.analyze_routine(routine, detailed=False)
                service.save_analysis(user_id, "brief", routine, brief_analysis, rating)
            elif "detailed_analysis" in request.form:
                detailed_analysis, _ = service.analyze_routine(routine, detailed=True)
                service.save_analysis(user_id, "detailed", routine, detailed_analysis, 0.0)
            else:
                raise ValueError("Unknown analysis action.")
        except Exception as exc:
            _handle_post_error(exc)

    recent_analyses = service.get_recent_analyses(user_id, limit=5)
    return render_page(
        "routine_analysis.html",
        active_page="routine_analysis",
        brief_analysis=brief_analysis,
        detailed_analysis=detailed_analysis,
        recent_analyses=recent_analyses,
    )


@app.route("/goals", methods=["GET", "POST"])
def goals():
    user_id = current_user_id()

    if request.method == "POST":
        try:
            if "add_goal" in request.form:
                title = require_text(request.form.get("title"), "Goal title", max_length=120)
                description = require_text(request.form.get("description"), "Description", max_length=600, allow_newlines=True)
                category = parse_choice(request.form.get("category"), "Category", allowed=GOAL_CATEGORIES)
                start_date = parse_date(request.form.get("start_date"), "Start date")
                end_date = parse_date(request.form.get("end_date"), "End date")
                _handle_post_success(service.create_goal(user_id, title, description, category, start_date, end_date))
            elif "update_progress" in request.form:
                goal_id = clamp_int(request.form.get("goal_id"), "Goal ID", minimum=1, maximum=10**9)
                progress = clamp_float(request.form.get("progress"), "Progress", minimum=0, maximum=100)
                _handle_post_success(service.update_goal_progress(user_id, goal_id, progress))
            else:
                raise ValueError("Unknown goal action.")
        except Exception as exc:
            _handle_post_error(exc)
        return redirect(url_for("goals"))

    goal_rows = service.list_goals(user_id)
    return render_page("goals.html", active_page="goals", goals=goal_rows)


@app.route("/overview")
def overview():
    user_id = current_user_id()
    habit_data = service.get_habit_frequency(user_id)
    routine_data = service.get_routine_ratings(user_id)
    summary = service.build_overview_summary(user_id)

    habit_chart = bar_chart(
        [row["habit"] for row in habit_data],
        [row["frequency"] for row in habit_data],
        title="Habit Completions",
        xlabel="Habit",
        ylabel="Completions",
    )

    routine_chart = line_chart(
        [row["created_at"][:10] for row in routine_data],
        [row["rating"] for row in routine_data],
        title="Routine Ratings",
        xlabel="Date",
        ylabel="Rating",
        ymin=0,
        ymax=10,
    )

    return render_page(
        "overview.html",
        active_page="overview",
        habit_chart=habit_chart,
        routine_chart=routine_chart,
        overview_summary=summary,
        recent_analyses=service.get_recent_analyses(user_id, limit=3),
    )


@app.route("/stress_management", methods=["GET", "POST"])
def stress_management():
    user_id = current_user_id()

    if request.method == "POST":
        try:
            stress_level = clamp_int(request.form.get("stress_level"), "Stress level", minimum=1, maximum=10)
            _handle_post_success(service.log_stress_level(user_id, stress_level))
        except Exception as exc:
            _handle_post_error(exc)
        return redirect(url_for("stress_management"))

    stress_levels = service.get_stress_levels(user_id)
    stress_chart = line_chart(
        [row["created_at"][:10] for row in stress_levels],
        [row["stress_level"] for row in stress_levels],
        title="Stress Levels",
        xlabel="Date",
        ylabel="Stress",
        ymin=0,
        ymax=10,
    )
    meditation = service.get_meditation_recommendation()
    return render_page(
        "stress_management.html",
        active_page="stress_management",
        stress_levels=stress_levels,
        stress_chart=stress_chart,
        meditation=meditation,
    )


@app.route("/productivity", methods=["GET", "POST"])
def productivity():
    user_id = current_user_id()

    if request.method == "POST":
        try:
            if "add_task" in request.form:
                title = require_text(request.form.get("title"), "Task title", max_length=120)
                description = require_text(request.form.get("description"), "Description", max_length=600, allow_newlines=True)
                priority = parse_choice(request.form.get("priority"), "Priority", allowed=TASK_PRIORITIES)
                due_date = parse_date(request.form.get("due_date"), "Due date")
                _handle_post_success(service.create_task(user_id, title, description, priority, due_date))
            elif "update_task" in request.form:
                task_id = clamp_int(request.form.get("task_id"), "Task ID", minimum=1, maximum=10**9)
                completed = parse_bool(request.form.get("completed"))
                _handle_post_success(service.update_task(user_id, task_id, completed))
            else:
                raise ValueError("Unknown task action.")
        except Exception as exc:
            _handle_post_error(exc)
        return redirect(url_for("productivity"))

    tasks = service.list_tasks(user_id)
    return render_page("productivity.html", active_page="productivity", tasks=tasks)


@app.route("/health_wellness", methods=["GET", "POST"])
def health_wellness():
    user_id = current_user_id()

    if request.method == "POST":
        try:
            if "log_nutrition" in request.form:
                meal = require_text(request.form.get("meal"), "Meal", max_length=120)
                calories = clamp_int(request.form.get("calories"), "Calories", minimum=1, maximum=10000)
                _handle_post_success(service.log_nutrition(user_id, meal, calories))
            elif "log_sleep" in request.form:
                sleep_duration = clamp_float(request.form.get("sleep_duration"), "Sleep duration", minimum=0.1, maximum=24)
                sleep_quality = clamp_int(request.form.get("sleep_quality"), "Sleep quality", minimum=1, maximum=10)
                _handle_post_success(service.log_sleep(user_id, sleep_duration, sleep_quality))
            else:
                raise ValueError("Unknown wellness action.")
        except Exception as exc:
            _handle_post_error(exc)
        return redirect(url_for("health_wellness"))

    nutrition_logs = service.get_nutrition_logs(user_id)
    sleep_logs = service.get_sleep_logs(user_id)
    nutrition_chart = bar_chart(
        [row["created_on"] for row in nutrition_logs],
        [row["total_calories"] for row in nutrition_logs],
        title="Daily Calorie Intake",
        xlabel="Date",
        ylabel="Calories",
    )
    sleep_chart = scatter_chart(
        [row["created_on"] for row in sleep_logs],
        [row["sleep_duration"] for row in sleep_logs],
        [row["sleep_quality"] for row in sleep_logs],
        title="Sleep Duration and Quality",
        xlabel="Date",
        ylabel="Hours Slept",
    )
    return render_page(
        "health_wellness.html",
        active_page="health_wellness",
        nutrition_logs=nutrition_logs,
        sleep_logs=sleep_logs,
        nutrition_chart=nutrition_chart,
        sleep_chart=sleep_chart,
    )


@app.route("/community", methods=["GET", "POST"])
def community():
    user_id = current_user_id()

    if request.method == "POST":
        try:
            title = require_text(request.form.get("title"), "Title", max_length=120)
            content = require_text(request.form.get("content"), "Content", max_length=1200, allow_newlines=True)
            category = parse_choice(request.form.get("category"), "Category", allowed=POST_CATEGORIES)
            _handle_post_success(service.create_post(user_id, title, content, category))
        except Exception as exc:
            _handle_post_error(exc)
        return redirect(url_for("community"))

    posts = service.list_posts(limit=10)
    return render_page("community.html", active_page="community", posts=posts)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    try:
        payload = request.get_json(silent=True) or request.form
        identity = require_text(payload.get("identity") or payload.get("username"), "Username or email", max_length=120)
        password = require_text(payload.get("password"), "Password", max_length=256)
        user = service.authenticate_user(identity, password)
        if not user:
            return jsonify({"message": "Invalid credentials."}), 400

        session["user_id"] = user["id"]
        session["username"] = user["username"]
        return jsonify({"message": "Logged in successfully.", "user": {"id": user["id"], "username": user["username"]}})
    except ValueError as exc:
        return jsonify({"message": str(exc)}), 400
    except Exception:
        return jsonify({"message": "Could not log in."}), 400


@app.route("/signup", methods=["POST"])
def signup():
    try:
        payload = request.get_json(silent=True) or request.form
        username = require_text(payload.get("username"), "Username", max_length=40)
        email = require_text(payload.get("email"), "Email", max_length=120)
        password = require_text(payload.get("password"), "Password", max_length=256)

        if len(password) < 8:
            return jsonify({"message": "Password must be at least 8 characters long."}), 400

        user = service.create_user(username, email, password)
    except sqlite3.IntegrityError:
        return jsonify({"message": "Username or email already exists."}), 400
    except ValueError as exc:
        return jsonify({"message": str(exc)}), 400
    except Exception:
        return jsonify({"message": "Could not create account."}), 400

    session["user_id"] = user["id"]
    session["username"] = user["username"]
    return jsonify({"message": "Account created successfully.", "user": {"id": user["id"], "username": user["username"]}})


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("welcome"))


if __name__ == "__main__":
    app.run(debug=True)
