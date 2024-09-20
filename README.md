Lumi: Web-Based Assistant for Habit Tracking and Routine Analysis
Overview
Lumi is a Streamlit-based web application that acts as a lifestyle assistant to help you track habits and analyze daily routines. Lumi uses Google's Gemini API for generating insights and analysis, offering both brief and detailed analyses of your routines to help you improve productivity, time management, and overall energy levels. The app also enables you to track your daily habits, monitor completion rates, and save progress over time.

Features
Habit Tracking:

Add new habits with daily frequency targets.
Update the completion status of existing habits.
Track habit completion rates over time.
Automatically save and load habit data from CSV files.
Daily Routine Analysis:

Input your daily routine to get a brief, AI-generated analysis.
Get a detailed routine analysis with suggestions for improvement in time management, productivity, and energy levels.
View previously saved analyses and track your progress over time.
Technologies Used
Streamlit: For building the web-based user interface.
Pandas: For managing and storing data related to habits and routine analysis.
Google Gemini API: For generating AI-based insights on daily routines.
CSV: Data is saved and loaded from CSV files to ensure persistence.
How to Use
1. Install Dependencies
Make sure you have Python installed. You will also need to install the following Python packages:

pip install streamlit pandas google-generativeai

2. Set Up Google Gemini API
You will need to have access to Google's Gemini API. Replace the GEMINI_API_KEY in the script with your own key:

GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"

3. Run the Application
To run the Lumi application, use the following command in your terminal:

streamlit run app.py

This will open the Lumi web application in your default browser.

4. Habit Tracking Tab
Add a New Habit: Enter the habit you wish to track along with the desired daily frequency. Lumi will track how often the habit is completed.
Update a Habit: Select a habit and mark it as completed or incomplete for the day. Lumi will update the completion rate accordingly.
View Habits: See all your tracked habits and their completion rates in the form of a table.
5. Daily Routine Analysis Tab
Brief Routine Analysis: Input your daily routine as text. Lumi will use the Gemini API to generate a brief analysis based on the routine you provided.
Detailed Routine Analysis: Optionally, Lumi can provide a more detailed analysis of your routine, offering insights into productivity, time management, and energy levels, along with recommendations.
Previous Analyses: View a table of previous routine analyses, including dates and insights for each.
File Storage
habits.csv: Stores all your tracked habits, including their completion rates and last completed date.
analysis.csv: Stores your daily routine analyses, including the date, routine details, and AI-generated insights.
Troubleshooting
Ensure you have set up the Google Gemini API key correctly. If the key is invalid or missing, you may encounter errors when trying to generate routine analyses.
CSV files must be in the same directory as the application for loading and saving habit and analysis data.
Future Enhancements
Reminder System: Add notifications or reminders to help users stay on track with their habits.
Advanced Insights: Offer additional types of analyses based on the user's preferences or goals.
Visualizations: Add graphs and charts to represent habit completion and routine improvements over time.
License
This project is licensed under the MIT License.

Enjoy improving your habits and routines with Lumi!
