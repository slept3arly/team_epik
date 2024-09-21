import sqlite3
from datetime import datetime, timedelta
import google.generativeai as genai
import random

GEMINI_API_KEY = "AIzaSyBnQi3e0zl453OoH5s67luF00DwaN5tzv8"  # Replace with your actual Gemini API key
class AdvancedLumi:
    def __init__(self):
        self.conn = sqlite3.connect('lumi_data.db', check_same_thread=False)
        self.create_tables()
        
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-pro')

    def create_tables(self):
        with self.conn:
            self.conn.executescript('''
                CREATE TABLE IF NOT EXISTS habits (
                    id INTEGER PRIMARY KEY,
                    habit TEXT UNIQUE,
                    frequency INTEGER,
                    completion_rate REAL,
                    last_completed DATE
                );
                CREATE TABLE IF NOT EXISTS analyses (
                    id INTEGER PRIMARY KEY,
                    date DATE,
                    routine TEXT,
                    brief_analysis TEXT,
                    rating REAL
                );
                CREATE TABLE IF NOT EXISTS goals (
                    id INTEGER PRIMARY KEY,
                    title TEXT,
                    description TEXT,
                    category TEXT,
                    start_date DATE,
                    end_date DATE,
                    progress REAL
                );
                CREATE TABLE IF NOT EXISTS stress_logs (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER,
                    stress_level INTEGER,
                    date DATE
                );
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER,
                    title TEXT,
                    description TEXT,
                    priority TEXT,
                    due_date DATE,
                    completed BOOLEAN
                );
                CREATE TABLE IF NOT EXISTS nutrition_logs (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER,
                    meal TEXT,
                    calories INTEGER,
                    date DATE
                );
                CREATE TABLE IF NOT EXISTS sleep_logs (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER,
                    sleep_duration REAL,
                    sleep_quality INTEGER,
                    date DATE
                );
                CREATE TABLE IF NOT EXISTS community_posts (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER,
                    title TEXT,
                    content TEXT,
                    category TEXT,
                    date DATE
                );
            ''')

    def add_habit(self, habit, frequency):
        try:
            with self.conn:
                self.conn.execute('''
                    INSERT INTO habits (habit, frequency, completion_rate, last_completed)
                    VALUES (?, ?, ?, ?)
                ''', (habit, frequency, 0, datetime.now() - timedelta(days=1)))
            return f"Habit '{habit}' added successfully!"
        except sqlite3.IntegrityError:
            return f"Habit '{habit}' already exists!"

    def update_habit_completion(self, habit, completed):
        with self.conn:
            cursor = self.conn.execute('SELECT completion_rate FROM habits WHERE habit = ?', (habit,))
            result = cursor.fetchone()
            if result:
                current_rate = result[0]
                new_rate = (current_rate * 9 + 100) / 10 if completed else (current_rate * 9) / 10
                self.conn.execute('''
                    UPDATE habits
                    SET completion_rate = ?, last_completed = ?
                    WHERE habit = ?
                ''', (new_rate, datetime.now() if completed else None, habit))
                return "Habit updated successfully!"
            return "Habit not found."

    def get_habits(self):
        with self.conn:
            cursor = self.conn.execute('SELECT habit FROM habits')
            return [row[0] for row in cursor.fetchall()]

    def get_habit_frequency(self, days=7):
        seven_days_ago = datetime.now() - timedelta(days=days)
        with self.conn:
            cursor = self.conn.execute('''
                SELECT habit, COUNT(*) as frequency
                FROM habits
                WHERE last_completed >= ?
                GROUP BY habit
            ''', (seven_days_ago,))
            return cursor.fetchall()

    def get_routine_ratings(self, days=7):
        seven_days_ago = datetime.now() - timedelta(days=days)
        with self.conn:
            cursor = self.conn.execute('''
                SELECT date, rating
                FROM analyses
                WHERE date >= ?
                ORDER BY date
            ''', (seven_days_ago,))
            return cursor.fetchall()

    def get_brief_routine_analysis(self, routine):
        prompt = f"""Analyze this daily routine and provide:
        1. A brief, two-sentence summary with a few pointers
        2. Suggestions for improvement
        3. A rating out of 10 for the overall quality of the routine (provide only the number)

        Routine:
        {routine}

        Format your response as follows:
        Summary: [Your two-sentence summary]
        Suggestions: [Your suggestions]
        Rating: [Your rating out of 10, only the number]
        """
        try:
            response = self.model.generate_content(prompt)
            analysis = response.text
            
            rating_line = [line for line in analysis.split('\n') if line.startswith('Rating:')]
            rating = float(rating_line[0].split(':')[1].strip()) if rating_line else 5.0
            
            with self.conn:
                self.conn.execute('''
                    INSERT INTO analyses (date, routine, brief_analysis, rating)
                    VALUES (?, ?, ?, ?)
                ''', (datetime.now(), routine, analysis, rating))
            
            return analysis
        except Exception as e:
            return f"Error generating brief analysis: {str(e)}"

    def get_detailed_routine_analysis(self, routine):
        prompt = f"Provide a detailed, point-by-point analysis of this daily routine, highlighting potential areas for improvement or optimization:\n\n{routine}"
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error generating detailed analysis: {str(e)}"

    def add_goal(self, title, description, category, start_date, end_date):
        try:
            with self.conn:
                self.conn.execute('''
                    INSERT INTO goals (title, description, category, start_date, end_date, progress)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (title, description, category, start_date, end_date, 0))
            return f"Goal '{title}' added successfully!"
        except sqlite3.IntegrityError:
            return f"Goal '{title}' already exists!"

    def update_goal_progress(self, goal_id, progress):
        with self.conn:
            self.conn.execute('UPDATE goals SET progress = ? WHERE id = ?', (progress, goal_id))
        return f"Goal progress updated successfully!"

    def get_goals(self):
        with self.conn:
            cursor = self.conn.execute('SELECT * FROM goals')
            return cursor.fetchall()

    def log_stress_level(self, user_id, stress_level):
        with self.conn:
            self.conn.execute('''
                INSERT INTO stress_logs (user_id, stress_level, date)
                VALUES (?, ?, ?)
            ''', (user_id, stress_level, datetime.now().date()))
        return "Stress level logged successfully!"

    def get_stress_levels(self, user_id, days=7):
        seven_days_ago = datetime.now().date() - timedelta(days=days)
        with self.conn:
            cursor = self.conn.execute('''
                SELECT date, stress_level
                FROM stress_logs
                WHERE user_id = ? AND date >= ?
                ORDER BY date
            ''', (user_id, seven_days_ago))
            return cursor.fetchall()

    def get_meditation_recommendation(self):
        meditations = [
            {"title": "Mindful Breathing", "duration": "5 minutes", "audio": "mindful_breathing.mp3"},
            {"title": "Body Scan Relaxation", "duration": "10 minutes", "audio": "body_scan.mp3"},
            {"title": "Loving-Kindness Meditation", "duration": "15 minutes", "audio": "loving_kindness.mp3"},
        ]
        return random.choice(meditations)

    def add_task(self, user_id, title, description, priority, due_date):
        with self.conn:
            self.conn.execute('''
                INSERT INTO tasks (user_id, title, description, priority, due_date, completed)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, title, description, priority, due_date, False))
        return "Task added successfully!"

    def get_tasks(self, user_id):
        with self.conn:
            cursor = self.conn.execute('SELECT * FROM tasks WHERE user_id = ? ORDER BY due_date', (user_id,))
            return cursor.fetchall()

    def update_task(self, task_id, completed):
        with self.conn:
            self.conn.execute('UPDATE tasks SET completed = ? WHERE id = ?', (completed, task_id))
        return "Task updated successfully!"

    def log_nutrition(self, user_id, meal, calories):
        with self.conn:
            self.conn.execute('''
                INSERT INTO nutrition_logs (user_id, meal, calories, date)
                VALUES (?, ?, ?, ?)
            ''', (user_id, meal, calories, datetime.now().date()))
        return "Nutrition logged successfully!"

    def get_nutrition_logs(self, user_id, days=7):
        seven_days_ago = datetime.now().date() - timedelta(days=days)
        with self.conn:
            cursor = self.conn.execute('''
                SELECT date, SUM(calories) as total_calories
                FROM nutrition_logs
                WHERE user_id = ? AND date >= ?
                GROUP BY date
                ORDER BY date
            ''', (user_id, seven_days_ago))
            return cursor.fetchall()

    def log_sleep(self, user_id, sleep_duration, sleep_quality):
        with self.conn:
            self.conn.execute('''
                INSERT INTO sleep_logs (user_id, sleep_duration, sleep_quality, date)
                VALUES (?, ?, ?, ?)
            ''', (user_id, sleep_duration, sleep_quality, datetime.now().date()))
        return "Sleep logged successfully!"

    def get_sleep_logs(self, user_id, days=7):
        seven_days_ago = datetime.now().date() - timedelta(days=days)
        with self.conn:
            cursor = self.conn.execute('''
                SELECT date, sleep_duration, sleep_quality
                FROM sleep_logs
                WHERE user_id = ? AND date >= ?
                ORDER BY date
            ''', (user_id, seven_days_ago))
            return cursor.fetchall()

    def add_community_post(self, user_id, title, content, category):
        with self.conn:
            self.conn.execute('''
                INSERT INTO community_posts (user_id, title, content, category, date)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, title, content, category, datetime.now().date()))
        return "Community post added successfully!"

    def get_community_posts(self, category=None, limit=10):
        with self.conn:
            if category:
                cursor = self.conn.execute('''
                    SELECT * FROM community_posts
                    WHERE category = ?
                    ORDER BY date DESC
                    LIMIT ?
                ''', (category, limit))
            else:
                cursor = self.conn.execute('''
                    SELECT * FROM community_posts
                    ORDER BY date DESC
                    LIMIT ?
                ''', (limit,))
            return cursor.fetchall()
