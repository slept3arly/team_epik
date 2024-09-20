import streamlit as st
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from datetime import datetime, timedelta
import random
import json
import google.generativeai as genai
import requests

class AdvancedLumi:
    def __init__(self, gemini_api_key):
        self.habits_data = pd.DataFrame(columns=['habit', 'frequency', 'completion_rate', 'last_completed'])
        self.suggestions = pd.DataFrame(columns=['text', 'difficulty', 'category'])
        self.user_progress = pd.DataFrame(columns=['date', 'progress_level'])
        self.load_data()
        
        # Initialize Gemini API
        genai.configure(api_key=gemini_api_key)
        self.model = genai.GenerativeModel('gemini-pro')

    def load_data(self):
        try:
            self.habits_data = pd.read_csv('habits.csv')
            self.habits_data['last_completed'] = pd.to_datetime(self.habits_data['last_completed'])
            self.suggestions = pd.read_csv('suggestions.csv')
            self.user_progress = pd.read_csv('progress.csv')
            self.user_progress['date'] = pd.to_datetime(self.user_progress['date'])
        except FileNotFoundError:
            st.warning("No existing data found. Starting with empty datasets.")

    def save_data(self):
        self.habits_data.to_csv('habits.csv', index=False)
        self.suggestions.to_csv('suggestions.csv', index=False)
        self.user_progress.to_csv('progress.csv', index=False)

    def add_habit(self, habit, frequency):
        new_habit = pd.DataFrame({
            'habit': [habit],
            'frequency': [frequency],
            'completion_rate': [0],
            'last_completed': [datetime.now() - timedelta(days=1)]
        })
        self.habits_data = pd.concat([self.habits_data, new_habit], ignore_index=True)
        st.success(f"Habit '{habit}' added successfully!")

    def update_habit_completion(self, habit, completed):
        habit_row = self.habits_data.loc[self.habits_data['habit'] == habit]
        if not habit_row.empty:
            index = habit_row.index[0]
            if completed:
                self.habits_data.at[index, 'completion_rate'] = (habit_row['completion_rate'].values[0] * 9 + 100) / 10
                self.habits_data.at[index, 'last_completed'] = datetime.now()
            else:
                self.habits_data.at[index, 'completion_rate'] = (habit_row['completion_rate'].values[0] * 9) / 10
            self.save_data()

    def get_personalized_suggestion(self):
        if self.habits_data.empty:
            return self.get_gemini_suggestion("Suggest a good habit to start with for someone new to habit tracking.")

        if len(self.habits_data) < 3:
            target_habit = self.habits_data.sample(1).iloc[0]
        else:
            features = self.habits_data[['frequency', 'completion_rate']].copy()
            scaler = StandardScaler()
            features_scaled = scaler.fit_transform(features)

            kmeans = KMeans(n_clusters=min(3, len(self.habits_data)), random_state=42)
            clusters = kmeans.fit_predict(features_scaled)

            cluster_completion_rates = self.habits_data.groupby(clusters)['completion_rate'].mean()
            target_cluster = cluster_completion_rates.idxmin()

            target_habits = self.habits_data[clusters == target_cluster]
            target_habit = target_habits.sample(1).iloc[0]

        prompt = f"Suggest a specific, actionable way to improve the habit of {target_habit['habit']}. " \
                 f"The user's current completion rate for this habit is {target_habit['completion_rate']:.2f}%. " \
                 f"Make the suggestion encouraging and motivating."

        return self.get_gemini_suggestion(prompt)

    def get_gemini_suggestion(self, prompt):
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            st.error(f"Error generating suggestion from Gemini: {e}")
            return "I'm having trouble coming up with a suggestion right now. Let's focus on one of your existing habits!"

    def update_progress(self, completed_suggestion):
        today = datetime.now().date()
        if self.user_progress.empty or self.user_progress['date'].max().date() < today:
            new_progress = pd.DataFrame({'date': [today], 'progress_level': [0]})
            self.user_progress = pd.concat([self.user_progress, new_progress], ignore_index=True)

        last_index = self.user_progress.index[-1]
        current_progress = self.user_progress.at[last_index, 'progress_level']
        
        if completed_suggestion:
            self.user_progress.at[last_index, 'progress_level'] = min(current_progress + 1, 10)
        else:
            self.user_progress.at[last_index, 'progress_level'] = max(current_progress - 1, 0)
        
        self.save_data()

    def analyze_progress(self):
        if len(self.user_progress) < 7:
            return self.get_gemini_suggestion("Provide an encouraging message for someone who just started tracking their habits and doesn't have enough data for a trend analysis yet.")

        last_week = self.user_progress.tail(7)
        trend = np.polyfit(range(7), last_week['progress_level'], 1)[0]

        if trend > 0.1:
            prompt = "Generate an encouraging message for someone whose habit progress is trending upwards over the last week. Include a tip to maintain this positive trend."
        elif trend < -0.1:
            prompt = "Create a motivational message for someone whose habit progress has been declining over the last week. Include a practical tip to help them get back on track."
        else:
            prompt = "Compose a message for someone whose habit progress has been steady over the last week. Suggest a way they could challenge themselves to improve further."

        return self.get_gemini_suggestion(prompt)

def main():
    st.title("Lumi: Habit Tracker and Daily Routine Analyzer")

    # Initialize session state
    if 'lumi' not in st.session_state:
        gemini_api_key = st.text_input("Please enter your Gemini API key:", type="password")
        if gemini_api_key:
            st.session_state.lumi = AdvancedLumi(gemini_api_key)
        else:
            st.warning("Please enter your Gemini API key to continue.")
            return

    lumi = st.session_state.lumi

    # Sidebar for habit tracking
    st.sidebar.header("Habit Tracker")
    habit_choice = st.sidebar.radio("Choose an action:", ["Add Habit", "Update Habit", "View Habits", "Get Suggestion", "Analyze Progress"])

    if habit_choice == "Add Habit":
        habit = st.sidebar.text_input("Enter the habit name:")
        frequency = st.sidebar.number_input("Enter the daily frequency:", min_value=1, value=1)
        if st.sidebar.button("Add Habit"):
            lumi.add_habit(habit, frequency)

    elif habit_choice == "Update Habit":
        habit = st.sidebar.selectbox("Select a habit to update:", lumi.habits_data['habit'].tolist())
        completed = st.sidebar.checkbox("Did you complete this habit today?")
        if st.sidebar.button("Update Habit"):
            lumi.update_habit_completion(habit, completed)
            st.sidebar.success("Habit updated successfully!")

    elif habit_choice == "View Habits":
        st.sidebar.write(lumi.habits_data)

    elif habit_choice == "Get Suggestion":
        suggestion = lumi.get_personalized_suggestion()
        st.sidebar.write("Lumi suggests:", suggestion)
        completed = st.sidebar.checkbox("Did you act on this suggestion?")
        if st.sidebar.button("Submit"):
            lumi.update_progress(completed)
            st.sidebar.success("Progress updated!")

    elif habit_choice == "Analyze Progress":
        analysis = lumi.analyze_progress()
        st.sidebar.write("Progress Analysis:", analysis)

    # Main content for daily routine analysis
    st.header("Daily Routine Analysis")
    routine = st.text_area("Enter your daily routine (e.g., 'Wake up at 7am, exercise, breakfast, work, lunch, etc.')")

    if st.button("Analyze Routine"):
        # Call Gemini API to analyze the daily routine
        api_url = "https://api.gemini.com/v1/analysis"
        api_key = "AIzaSyBnQi3e0zl453OoH5s67luF00DwaN5tzv8"
        headers = {"Authorization": f"Bearer {api_key}"}
        data = {"text": routine}
        response = requests.post(api_url, headers=headers, json=data)

        if response.status_code == 200:
            analysis = response.json()
            st.write("Analysis Results:")
            st.write(f"*Productivity Score:* {analysis['productivity_score']}")
            st.write(f"*Time Management:* {analysis['time_management']}")
            st.write(f"*Energy Levels:* {analysis['energy_levels']}")
            st.write(f"*Recommendations:* {analysis['recommendations']}")
        else:
            st.error("Error analyzing daily routine. Please try again.")

if __name__ == "__main__":
    main()