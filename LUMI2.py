import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import google.generativeai as genai
import seaborn as sns

# Store the API key directly in the code
GEMINI_API_KEY = "AIzaSyBnQi3e0zl453OoH5s67luF00DwaN5tzv8"  # Replace with your actual Gemini API key

class AdvancedLumi:
    def __init__(self):
        self.habits_data = pd.DataFrame(columns=['habit', 'frequency', 'completion_rate', 'last_completed'])
        self.analysis_data = pd.DataFrame(columns=['date', 'routine', 'brief_analysis', 'rating'])
        self.load_data()
        
        # Initialize Gemini API
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-pro')

    def load_data(self):
        try:
            self.habits_data = pd.read_csv('habits.csv')
            self.habits_data['last_completed'] = pd.to_datetime(self.habits_data['last_completed'])
        except FileNotFoundError:
            st.warning("No existing habits data found. Starting with an empty dataset.")
            self.habits_data = pd.DataFrame(columns=['habit', 'frequency', 'completion_rate', 'last_completed'])
        
        try:
            self.analysis_data = pd.read_csv('analysis.csv')
            self.analysis_data['date'] = pd.to_datetime(self.analysis_data['date'])
        except FileNotFoundError:
            st.warning("No existing analysis data found. Starting with an empty dataset.")
            self.analysis_data = pd.DataFrame(columns=['date', 'routine', 'brief_analysis', 'rating'])

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
            
            # Extract rating from the analysis
            rating_line = [line for line in analysis.split('\n') if line.startswith('Rating:')]
            rating = float(rating_line[0].split(':')[1].strip()) if rating_line else 5.0  # Default to 5 if not found
            
            # Save the analysis to the DataFrame
            new_analysis = pd.DataFrame({
                'date': [datetime.now()],
                'routine': [routine],
                'brief_analysis': [analysis],
                'rating': [rating]
            })
            self.analysis_data = pd.concat([self.analysis_data, new_analysis], ignore_index=True)
            self.save_data()
            
            return analysis
        except Exception as e:
            return f"Error generating brief analysis: {e}"

    def get_detailed_routine_analysis(self, routine):
        prompt = f"Hey there, AI! I've got a daily routine I'd like you to analyze in detail. Can you provide a point-by-point breakdown of my routine, highlighting any potential areas for improvement or optimization?:\n\n{routine}"
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error generating detailed analysis: {e}"

    def get_rag_insights(self):
        # Get data from the last 7 days
        seven_days_ago = datetime.now() - timedelta(days=7)
        recent_habits = self.habits_data[self.habits_data['last_completed'] >= seven_days_ago]
        recent_analyses = self.analysis_data[self.analysis_data['date'] >= seven_days_ago]

        # Prepare the context for the RAG AI
        context = f"Habit data for the last 7 days:\n{recent_habits.to_string()}\n\n"
        context += f"Routine analyses for the last 7 days:\n{recent_analyses.to_string()}\n\n"

        prompt = f"""Based on the following data from the last 7 days, provide:
        1. A brief overview of the user's habits and routines
        2. A summary of their progress and consistency
        3. Three specific suggestions for improvement

        Context:
        {context}

        Please format your response with clear headings for each section."""

        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error generating RAG insights: {e}"

def create_habit_frequency_chart(habits_data):
    # Count the number of times each habit was completed in the last 7 days
    seven_days_ago = datetime.now() - timedelta(days=7)
    recent_habits = habits_data[habits_data['last_completed'] >= seven_days_ago]
    habit_counts = recent_habits['habit'].value_counts()

    plt.figure(figsize=(10, 6))
    sns.barplot(x=habit_counts.index, y=habit_counts.values)
    plt.title('Habit Frequency (Last 7 Days)')
    plt.xlabel('Habits')
    plt.ylabel('Frequency')
    plt.xticks(rotation=45, ha='right')
    return plt

def create_routine_rating_chart(analysis_data):
    # Get the ratings for the last 7 days
    seven_days_ago = datetime.now() - timedelta(days=7)
    recent_analyses = analysis_data[analysis_data['date'] >= seven_days_ago]
    
    if recent_analyses.empty or 'rating' not in recent_analyses.columns:
        st.warning("Not enough data to create the routine rating chart.")
        return None

    plt.figure(figsize=(10, 6))
    sns.lineplot(x='date', y='rating', data=recent_analyses)
    plt.title('Routine Ratings (Last 7 Days)')
    plt.xlabel('Date')
    plt.ylabel('Rating (out of 10)')
    plt.ylim(0, 10)
    plt.xticks(rotation=45, ha='right')
    return plt
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
    tab1, tab2, tab3 = st.tabs(["Habit Tracking", "Daily Routine Analysis", "Overview"])

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

    with tab2:
        st.header("Daily Routine Analysis")
        
        with st.form("routine_analysis_form"):
            daily_routine = st.text_area("Enter your daily routine:")
            analyze_routine_submitted = st.form_submit_button("Analyze My Routine")
            show_detailed_analysis = st.form_submit_button("Propose a Better Plan")
        
        if analyze_routine_submitted and daily_routine:
            st.session_state.daily_routine = daily_routine
            st.session_state.brief_analysis = st.session_state.lumi.get_brief_routine_analysis(daily_routine)
            st.session_state.detailed_analysis = ""  # Reset detailed analysis
            st.subheader("Brief Analysis")
            st.write(st.session_state.brief_analysis)

        if show_detailed_analysis:
            if not st.session_state.detailed_analysis:
                st.session_state.detailed_analysis = st.session_state.lumi.get_detailed_routine_analysis(st.session_state.daily_routine)
            st.subheader("Better Plan")
            st.write(st.session_state.detailed_analysis)

    with tab3:
        st.header("Overview")
        # Generate and display RAG insights
        st.subheader("Summary")
        rag_insights = st.session_state.lumi.get_rag_insights()
        st.write(rag_insights)

        # Create and display habit frequency chart
        st.subheader("Habit Frequency (Last 7 Days)")
        habit_chart = create_habit_frequency_chart(st.session_state.lumi.habits_data)
        st.pyplot(habit_chart)

        # Create and display routine rating chart
        st.subheader("Routine Ratings (Last 7 Days)")
        routine_chart = create_routine_rating_chart(st.session_state.lumi.analysis_data)
        if routine_chart:
            st.pyplot(routine_chart)

if __name__ == "__main__":
    main()
