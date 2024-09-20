import streamlit as st

def welcome_page():
    st.title("Lumi: Habit Tracker and Daily Routine Analyzer")
    st.header("Welcome to Lumi!")
    st.write("Lumi is a habit tracker and daily routine analyzer that helps you stay on top of your goals and improve your productivity.")
    st.write("With Lumi, you can:")
    st.write("* Track your daily habits and routines")
    st.write("* Get personalized insights and recommendations to improve your productivity")
    st.write("* Analyze your daily routine and identify areas for improvement")
    st.write("* Set goals and track your progress towards achieving them")
    st.write("")
    st.write("Get started today and take control of your habits and routines!")
    st.button("Login/Sign Up")

def main():
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        welcome_page()
    else:
        # TO DO: implement main app logic
        st.write("You are logged in!")

if __name__ == "__main__":
    main()
