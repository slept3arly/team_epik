import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import google.generativeai as genai

# Store the API key directly in the code
GEMINI_API_KEY = "AIzaSyBnQi3e0zl453OoH5s67luF00DwaN5tzv8"  # Replace with your actual Gemini API key

class AdvancedLumi:
    def __init__(self):
        self.habits_data = pd.DataFrame(columns=['habit', 'frequency', 'completion_rate', 'last_completed'])
        self.analysis_data = pd.DataFrame(columns=['date', 'routine', 'brief_analysis'])
        self.load_data()
        
        # Initialize Gemini API
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-pro')

    def load_data(self):
        try:
            loaded_data = pd.read_csv('habits.csv')
            loaded_data['last_completed'] = pd.to_datetime(loaded_data['last_completed'])
            self.habits_data = loaded_data
        except FileNotFoundError:
            st.warning("No existing habits data found. Starting with an empty dataset.")
            self.habits_data = pd.DataFrame(columns=['habit', 'frequency', 'completion_rate', 'last_completed'])
        
        try:
            self.analysis_data = pd.read_csv('analysis.csv')
            self.analysis_data['date'] = pd.to_datetime(self.analysis_data['date'])
        except FileNotFoundError:
            st.warning("No existing analysis data found. Starting with an empty dataset.")
            self.analysis_data = pd.DataFrame(columns=['date', 'routine', 'brief_analysis'])

    def save_data(self):
        self.habits_data.to_csv('habits.csv', index=False)
        self.analysis_data.to_csv('analysis.csv', index=False)

    def add_habit(self, habit, frequency):
        new_habit = pd.DataFrame({
            'habit': [habit],
            'frequency': [frequency],
            'completion_rate': [0],
            'last_completed': [datetime.now() - timedelta(days=1)]
        })
        self.habits_data = pd.concat([self.habits_data, new_habit], ignore_index=True)
        self.save_data()
        return f"Habit '{habit}' added successfully!"

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
            return "Habit updated successfully!"
        return "Habit not found."

    def get_brief_routine_analysis(self, routine):
        prompt = f"Provide a brief, one-sentence analysis of the following daily routine:\n\n{routine}"
        try:
            response = self.model.generate_content(prompt)
            analysis = response.text
            self.save_analysis(routine, analysis)
            return analysis
        except Exception as e:
            return f"Error generating brief analysis: {e}"

    def get_detailed_routine_analysis(self, routine):
        prompt = f"Analyze the following daily routine and provide detailed insights on productivity, time management, and energy levels. Also, give specific recommendations for improvement:\n\n{routine}"
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error generating detailed analysis: {e}"

    def save_analysis(self, routine, analysis):
        new_analysis = pd.DataFrame({
            'date': [datetime.now()],
            'routine': [routine],
            'brief_analysis': [analysis]
        })
        self.analysis_data = pd.concat([self.analysis_data, new_analysis], ignore_index=True)
        self.save_data()

def main():
    st.title("Lumi: Habit Tracker and Daily Routine Analyzer")

    # Initialize session state
    if 'lumi' not in st.session_state:
        st.session_state.lumi = AdvancedLumi()
    if 'daily_routine' not in st.session_state:
        st.session_state.daily_routine = ""
    if 'brief_analysis' not in st.session_state:
        st.session_state.brief_analysis = ""
    if 'detailed_analysis' not in st.session_state:
        st.session_state.detailed_analysis = ""

    # Create tabs
    tab1, tab2 = st.tabs(["Habit Tracking", "Daily Routine Analysis"])

    with tab1:
        st.header("Habit Tracking")
        
        # Add new habit
        with st.form("add_habit_form"):
            new_habit = st.text_input("Enter a new habit:")
            new_habit_frequency = st.number_input("Enter the daily frequency:", min_value=1, value=1)
            add_habit_submitted = st.form_submit_button("Add Habit")

        if add_habit_submitted and new_habit:
            result = st.session_state.lumi.add_habit(new_habit, new_habit_frequency)
            st.success(result)

        # Update existing habit
        with st.form("update_habit_form"):
            existing_habits = st.session_state.lumi.habits_data['habit'].tolist()
            update_habit = st.selectbox("Select a habit to update:", [''] + existing_habits)
            completed_habit = st.checkbox("Did you complete this habit today?")
            update_habit_submitted = st.form_submit_button("Update Habit")

        if update_habit_submitted and update_habit:
            result = st.session_state.lumi.update_habit_completion(update_habit, completed_habit)
            st.success(result)

        # Display habits
        st.subheader("Your Habits")
        st.dataframe(st.session_state.lumi.habits_data)

    with tab2:
        st.header("Daily Routine Analysis")
        
        with st.form("routine_analysis_form"):
            daily_routine = st.text_area("Enter your daily routine:", value=st.session_state.daily_routine)
            analyze_routine_submitted = st.form_submit_button("Analyze Routine")
            show_detailed_analysis = st.form_submit_button("Show Detailed Analysis")

        if analyze_routine_submitted and daily_routine:
            st.session_state.daily_routine = daily_routine
            st.session_state.brief_analysis = st.session_state.lumi.get_brief_routine_analysis(daily_routine)

        if st.session_state.brief_analysis:
            st.subheader("Brief Analysis")
            st.write(st.session_state.brief_analysis)

        if show_detailed_analysis:
            if not st.session_state.detailed_analysis:
                st.session_state.detailed_analysis = st.session_state.lumi.get_detailed_routine_analysis(st.session_state.daily_routine)
            st.subheader("Detailed Analysis")
            st.write(st.session_state.detailed_analysis)

        # Display saved analyses
        st.subheader("Previous Analyses")
        st.dataframe(st.session_state.lumi.analysis_data)

if __name__ == "__main__":
    main()
