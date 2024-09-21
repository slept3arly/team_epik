from flask import Flask, render_template, request, redirect, url_for, flash
from advance_lumi import AdvancedLumi
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Replace with a real secret key
lumi = AdvancedLumi()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/habit_tracking', methods=['GET', 'POST'])
def habit_tracking():
    if request.method == 'POST':
        if 'add_habit' in request.form:
            habit = request.form['habit']
            frequency = int(request.form['frequency'])
            result = lumi.add_habit(habit, frequency)
            flash(result)
        elif 'update_habit' in request.form:
            habit = request.form['habit']
            completed = 'completed' in request.form
            result = lumi.update_habit_completion(habit, completed)
            flash(result)
    
    habits = lumi.get_habits()
    return render_template('habit_tracking.html', habits=habits)

@app.route('/routine_analysis', methods=['GET', 'POST'])
def routine_analysis():
    brief_analysis = ""
    detailed_analysis = ""
    if request.method == 'POST':
        routine = request.form['routine']
        if 'analyze_routine' in request.form:
            brief_analysis = lumi.get_brief_routine_analysis(routine)
        elif 'detailed_analysis' in request.form:
            detailed_analysis = lumi.get_detailed_routine_analysis(routine)
    
    return render_template('routine_analysis.html', brief_analysis=brief_analysis, detailed_analysis=detailed_analysis)

@app.route('/goals', methods=['GET', 'POST'])
def goals():
    if request.method == 'POST':
        if 'add_goal' in request.form:
            title = request.form['title']
            description = request.form['description']
            category = request.form['category']
            start_date = request.form['start_date']
            end_date = request.form['end_date']
            result = lumi.add_goal(title, description, category, start_date, end_date)
            flash(result)
        elif 'update_progress' in request.form:
            goal_id = int(request.form['goal_id'])
            progress = float(request.form['progress'])
            result = lumi.update_goal_progress(goal_id, progress)
            flash(result)
    
    goals = lumi.get_goals()
    return render_template('goals.html', goals=goals)

@app.route('/overview')
def overview():
    habit_chart = create_habit_frequency_chart()
    routine_chart = create_routine_rating_chart()
    return render_template('overview.html', habit_chart=habit_chart, routine_chart=routine_chart)

@app.route('/stress_management', methods=['GET', 'POST'])
def stress_management():
    user_id = 1  # For simplicity, we're using a fixed user ID. In a real app, you'd get this from the logged-in user.
    if request.method == 'POST':
        stress_level = int(request.form['stress_level'])
        result = lumi.log_stress_level(user_id, stress_level)
        flash(result)
    
    stress_levels = lumi.get_stress_levels(user_id)
    meditation = lumi.get_meditation_recommendation()
    
    stress_chart = create_stress_chart(stress_levels)
    return render_template('stress_management.html', stress_levels=stress_levels, meditation=meditation, stress_chart=stress_chart)

@app.route('/productivity', methods=['GET', 'POST'])
def productivity():
    user_id = 1  # For simplicity, we're using a fixed user ID. In a real app, you'd get this from the logged-in user.
    if request.method == 'POST':
        if 'add_task' in request.form:
            title = request.form['title']
            description = request.form['description']
            priority = request.form['priority']
            due_date = request.form['due_date']
            result = lumi.add_task(user_id, title, description, priority, due_date)
            flash(result)
        elif 'update_task' in request.form:
            task_id = int(request.form['task_id'])
            completed = 'completed' in request.form
            result = lumi.update_task(task_id, completed)
            flash(result)
    
    tasks = lumi.get_tasks(user_id)
    return render_template('productivity.html', tasks=tasks)

@app.route('/health_wellness', methods=['GET', 'POST'])
def health_wellness():
    user_id = 1  # For simplicity, we're using a fixed user ID. In a real app, you'd get this from the logged-in user.
    if request.method == 'POST':
        if 'log_nutrition' in request.form:
            meal = request.form['meal']
            calories = int(request.form['calories'])
            result = lumi.log_nutrition(user_id, meal, calories)
            flash(result)
        elif 'log_sleep' in request.form:
            sleep_duration = float(request.form['sleep_duration'])
            sleep_quality = int(request.form['sleep_quality'])
            result = lumi.log_sleep(user_id, sleep_duration, sleep_quality)
            flash(result)
    
    nutrition_logs = lumi.get_nutrition_logs(user_id)
    sleep_logs = lumi.get_sleep_logs(user_id)
    
    nutrition_chart = create_nutrition_chart(nutrition_logs)
    sleep_chart = create_sleep_chart(sleep_logs)
    
    return render_template('health_wellness.html', nutrition_logs=nutrition_logs, sleep_logs=sleep_logs, nutrition_chart=nutrition_chart, sleep_chart=sleep_chart)

@app.route('/community', methods=['GET', 'POST'])
def community():
    user_id = 1  # For simplicity, we're using a fixed user ID. In a real app, you'd get this from the logged-in user.
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        category = request.form['category']
        result = lumi.add_community_post(user_id, title, content, category)
        flash(result)
    
    posts = lumi.get_community_posts()
    return render_template('community.html', posts=posts)

def create_habit_frequency_chart():
    habit_counts = lumi.get_habit_frequency()
    if not habit_counts:
        return None

    plt.figure(figsize=(10, 6))
    sns.barplot(x=[h[0] for h in habit_counts], y=[h[1] for h in habit_counts])
    plt.title('Habit Frequency (Last 7 Days)')
    plt.xlabel('Habits')
    plt.ylabel('Frequency')
    plt.xticks(rotation=45, ha='right')
    
    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight')
    img.seek(0)
    plt.close()
    return base64.b64encode(img.getvalue()).decode()

def create_routine_rating_chart():
    recent_analyses = lumi.get_routine_ratings()
    
    if not recent_analyses:
        return None

    plt.figure(figsize=(10, 6))
    sns.lineplot(x=[datetime.strptime(str(r[0]), '%Y-%m-%d') for r in recent_analyses], y=[r[1] for r in recent_analyses])
    plt.title('Routine Ratings (Last 7 Days)')
    plt.xlabel('Date')
    plt.ylabel('Rating (out of 10)')
    plt.ylim(0, 10)
    plt.xticks(rotation=45, ha='right')
    
    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight')
    img.seek(0)
    plt.close()
    return base64.b64encode(img.getvalue()).decode()

def create_stress_chart(stress_levels):
    if not stress_levels:
        return None

    plt.figure(figsize=(10, 6))
    sns.lineplot(x=[datetime.strptime(str(s[0]), '%Y-%m-%d') for s in stress_levels], y=[s[1] for s in stress_levels])
    plt.title('Stress Levels (Last 7 Days)')
    plt.xlabel('Date')
    plt.ylabel('Stress Level (1-10)')
    plt.ylim(0, 10)
    plt.xticks(rotation=45, ha='right')
    
    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight')
    img.seek(0)
    plt.close()
    return base64.b64encode(img.getvalue()).decode()

def create_nutrition_chart(nutrition_logs):
    if not nutrition_logs:
        return None

    plt.figure(figsize=(10, 6))
    sns.barplot(x=[n[0] for n in nutrition_logs], y=[n[1] for n in nutrition_logs])
    plt.title('Daily Calorie Intake (Last 7 Days)')
    plt.xlabel('Date')
    plt.ylabel('Calories')
    plt.xticks(rotation=45, ha='right')
    
    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight')
    img.seek(0)
    plt.close()
    return base64.b64encode(img.getvalue()).decode()

def create_sleep_chart(sleep_logs):
    if not sleep_logs:
        return None

    plt.figure(figsize=(10, 6))
    sns.scatterplot(x=[s[0] for s in sleep_logs], y=[s[1] for s in sleep_logs], hue=[s[2] for s in sleep_logs], palette='viridis', size=[s[2] for s in sleep_logs], sizes=(20, 200))
    plt.title('Sleep Duration and Quality (Last 7 Days)')
    plt.xlabel('Date')
    plt.ylabel('Sleep Duration (hours)')
    plt.xticks(rotation=45, ha='right')
    
    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight')
    img.seek(0)
    plt.close()
    return base64.b64encode(img.getvalue()).decode()

if __name__ == '__main__':
    app.run(debug=True)
