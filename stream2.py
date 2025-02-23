import streamlit as st
import pandas as pd
from pathlib import Path
import json
import os

# Import your existing functions
from main import generate_and_store_study_plan, suggest_resource, generate_summary, Ask_Summary

# Initialize session state for login management
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if 'current_page' not in st.session_state:
    st.session_state.current_page = 'login'

if 'summaries' not in st.session_state:
    st.session_state.summaries = {}

# Function to save user credentials
def save_credentials(username, password):
    if not os.path.exists('users.json'):
        with open('users.json', 'w') as f:
            json.dump({}, f)

    with open('users.json', 'r') as f:
        users = json.load(f)

    users[username] = password

    with open('users.json', 'w') as f:
        json.dump(users, f)

# Function to verify credentials
def verify_credentials(username, password):
    if not os.path.exists('users.json'):
        return False

    with open('users.json', 'r') as f:
        users = json.load(f)

    return username in users and users[username] == password

def login_page():
    st.title("JEE Learning Platform - Login")

    tab1, tab2 = st.tabs(["Login", "Sign Up"])

    with tab1:
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")

        if st.button("Login", key="login_button"):
            if verify_credentials(username, password):
                st.session_state.logged_in = True
                st.session_state.current_page = 'home'
                st.success("Successfully logged in!")
                st.rerun()
            else:
                st.error("Invalid credentials")

    with tab2:
        new_username = st.text_input("New Username", key="signup_username")
        new_password = st.text_input("New Password", type="password", key="signup_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="signup_confirm")

        if st.button("Sign Up", key="signup_button"):
            if new_password != confirm_password:
                st.error("Passwords don't match!")
            else:
                save_credentials(new_username, new_password)
                st.success("Account created successfully! Please login.")

def display_roadmap(topic, roadmap, context="view"):
    st.subheader(f"Roadmap for {topic}")

    # Display roadmap in a nice format
    for i, item in enumerate(roadmap):
        with st.expander(f"📚 {item['subtopic']}", key=f"roadmap_item_{context}_{topic}_r{i}"):
            st.write("**Description:**", item['description'])
            st.write("**Time Required:**", item['time_to_be_given'])

    # Show resources
    st.subheader("Recommended Resources")
    with st.spinner("Fetching resources..."):
        try:
            resources = suggest_resource(topic)
            for i, resource in enumerate(resources):
                if isinstance(resource, dict):
                    with st.expander(f"📖 {resource.get('resource', 'Resource')}",
                                   key=f"resource_{context}_{topic}_e{i}"):
                        st.write("**Topic:**", resource.get('topic', 'N/A'))
                        st.write("**Link:**", resource.get('resource_link', 'N/A'))
        except Exception as e:
            st.error(f"Error fetching resources: {str(e)}")

    # Button to go to summary page
    # In the display_roadmap function, modify the button line to include a unique key:
    if st.button("Go to Summary Page", key=f"summary_button_{context}_{topic}"):
        st.session_state.current_page = 'summary'
        st.rerun()

def home_page():
    st.title("JEE Learning Platform - Home")

    # Sidebar for navigation
    with st.sidebar:
        st.title("Navigation")
        if st.button("Logout", key="sidebar_logout"):
            st.session_state.logged_in = False
            st.session_state.current_page = 'login'
            st.rerun()

    tab1, tab2 = st.tabs(["Generate New Roadmap", "View Existing Roadmaps"])

    with tab1:
        st.header("Generate New Roadmap")
        topic = st.text_input("Enter topic:", key="new_topic_input")
        duration = st.selectbox("Select duration:",
                              ["1 week", "2 weeks", "3 weeks", "1 month"],
                              key="duration_select")

        if st.button("Generate Roadmap", key="generate_roadmap_button"):
            with st.spinner("Generating roadmap..."):
                try:
                    roadmap = generate_and_store_study_plan(topic, duration)
                    st.session_state[f'roadmap_{topic}'] = roadmap
                    st.success("Roadmap generated successfully!")
                    display_roadmap(topic, roadmap, context="generate")
                except Exception as e:
                    st.error(f"Error generating roadmap: {str(e)}")

    with tab2:
        st.header("Existing Roadmaps")
        roadmaps = [key.replace('roadmap_', '') for key in st.session_state.keys()
                   if key.startswith('roadmap_')]

        if roadmaps:
            selected_roadmap = st.selectbox("Select a roadmap:", roadmaps, key="existing_roadmap_select")
            if selected_roadmap:
                display_roadmap(selected_roadmap, st.session_state[f'roadmap_{selected_roadmap}'], context="view")
        else:
            st.info("No roadmaps generated yet. Create a new roadmap above!")

def summary_page():
    st.title("Summary Generator and Q&A")

    # Sidebar for navigation
    with st.sidebar:
        st.title("Navigation")
        if st.button("Back to Home", key="summary_back_home"):
            st.session_state.current_page = 'home'
            st.rerun()
        if st.button("Logout", key="summary_logout"):
            st.session_state.logged_in = False
            st.session_state.current_page = 'login'
            st.rerun()

    # File upload section
    uploaded_file = st.file_uploader("Upload PDF for Summary", type="pdf", key="pdf_uploader")

    if uploaded_file:
        # Save the uploaded file temporarily
        with open("temp.pdf", "wb") as f:
            f.write(uploaded_file.getvalue())

        if st.button("Generate Summary", key="generate_summary_button"):
            with st.spinner("Generating summary..."):
                try:
                    summary = generate_summary("temp.pdf")
                    st.session_state.summaries[uploaded_file.name] = summary
                    st.success("Summary generated successfully!")
                except Exception as e:
                    st.error(f"Error generating summary: {str(e)}")

    # Display summaries and Q&A section
    if st.session_state.summaries:
        selected_summary = st.selectbox(
            "Select a summary:",
            list(st.session_state.summaries.keys()),
            key="summary_select"
        )

        if selected_summary:
            st.subheader("Summary")
            st.write(st.session_state.summaries[selected_summary])

            st.subheader("Ask a Question")
            question = st.text_input("Enter your question:", key="qa_question_input")

            if st.button("Get Answer", key="get_answer_button"):
                with st.spinner("Finding answer..."):
                    try:
                        answer_dict = Ask_Summary(
                            st.session_state.summaries[selected_summary],
                            question
                        )
                        st.success("Answer found!")
                        st.write("**Answer:**", answer_dict["answer"])
                    except Exception as e:
                        st.error(f"Error finding answer: {str(e)}")

def main():
    if not st.session_state.logged_in:
        login_page()
    else:
        if st.session_state.current_page == 'home':
            home_page()
        elif st.session_state.current_page == 'summary':
            summary_page()

if __name__ == "__main__":
    st.set_page_config(
        page_title="JEE Learning Platform",
        page_icon="📚",
        layout="wide"
    )
    main()
