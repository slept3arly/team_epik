import streamlit as st
import hashlib
import pandas as pd

# Create a dictionary to store user credentials
users = {}

def make_hashes(password):
    """Make hashes of password"""
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    """Check hashed password"""
    if make_hashes(password) == hashed_text:
        return True
    return False

def login_page():
    st.title("Login to Lumi")
    st.write("Welcome back to Lumi! Please login to access your habit tracker and daily routine analyzer.")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    login_button = st.button("Login")

    if login_button:
        if username in users:
            hashed_password = users[username]["password"]
            if check_hashes(password, hashed_password):
                st.session_state.logged_in = True
                st.write("Login successful!")
            else:
                st.write("Incorrect password")
        else:
            st.write("Username not found")

def signup_page():
    st.title("Sign up for Lumi")
    st.write("Create an account to start tracking your habits and daily routine.")
    username = st.text_input("Username")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")
    signup_button = st.button("Sign up")

    if signup_button:
        if password == confirm_password:
            hashed_password = make_hashes(password)
            users[username] = {"password": hashed_password, "email": email}
            st.write("Sign up successful! You can now login.")
        else:
            st.write("Passwords do not match")

def main():
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        login_or_signup = st.selectbox("Login or Sign up", ["Login", "Sign up"])
        if login_or_signup == "Login":
            login_page()
        else:
            signup_page()
    else:
        # TO DO: implement main app logic
        st.write("You are logged in!")

if __name__ == "__main__":
    main()
