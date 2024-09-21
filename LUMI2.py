import pandas as pd
from datetime import datetime, timedelta
import google.generativeai as genai

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
            print("No existing habits data found. Starting with an empty dataset.")
            self.habits_data = pd.DataFrame(columns=['habit', 'frequency', 'completion_rate', 'last_completed'])
        
        try:
            self.analysis_data = pd.read_csv('analysis.csv')
            self.analysis_data['date'] = pd.to_datetime(self.analysis_data['date'])
        except FileNotFoundError:
            print("No existing analysis data found. Starting with an empty dataset.")
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
