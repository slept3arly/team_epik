from flask import Flask, render_template, request, redirect, url_for, flash
from lumi_6 import AdvancedLumi
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64
from datetime import datetime, timedelta

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
    
    habits = lumi.habits_data['habit'].tolist()
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

@app.route('/overview')
def overview():
    rag_insights = lumi.get_rag_insights()
    habit_chart = create_habit_frequency_chart()
    routine_chart = create_routine_rating_chart()
    return render_template('overview.html', rag_insights=rag_insights, habit_chart=habit_chart, routine_chart=routine_chart)

def create_habit_frequency_chart():
    seven_days_ago = datetime.now() - timedelta(days=7)
    recent_habits = lumi.habits_data[lumi.habits_data['last_completed'] >= seven_days_ago]
    habit_counts = recent_habits['habit'].value_counts()

    plt.figure(figsize=(10, 6))
    sns.barplot(x=habit_counts.index, y=habit_counts.values)
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
    seven_days_ago = datetime.now() - timedelta(days=7)
    recent_analyses = lumi.analysis_data[lumi.analysis_data['date'] >= seven_days_ago]
    
    if recent_analyses.empty or 'rating' not in recent_analyses.columns:
        return None

    plt.figure(figsize=(10, 6))
    sns.lineplot(x='date', y='rating', data=recent_analyses)
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

if __name__ == '__main__':
    app.run(debug=True)