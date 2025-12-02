"""
Dashboard Authentication Module
Handles user login and session management via API
"""
import streamlit as st
import requests
import os
from dotenv import load_dotenv
load_dotenv()
API_URL = os.getenv("API_URL", "http://localhost:8000")
def login(username, password):
    """Authenticate user with API"""
    try:
        response = requests.post(
            f"{API_URL}/token",
            data={"username": username, "password": password}
        )
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Connection error: {e}")
        return None
def check_auth():
    """Check if user is authenticated"""
    if 'token' not in st.session_state:
        st.session_state.token = None
        st.session_state.user = None
        st.session_state.authenticated = False
    return st.session_state.authenticated
def logout():
    """Clear session state"""
    st.session_state.token = None
    st.session_state.user = None
    st.session_state.authenticated = False
    st.rerun()
def get_user_profile(token):
    """Get user profile from API"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{API_URL}/users/me", headers=headers)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception:
        return None
def render_login_page():
    """Render login form"""
    st.title("🔐 Production Control System")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("### Login")
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Sign In", use_container_width=True)
            if submit:
                if not username or not password:
                    st.warning("Please enter username and password")
                else:
                    with st.spinner("Authenticating..."):
                        token_data = login(username, password)
                        if token_data:
                            st.session_state.token = token_data['access_token']
                            user_profile = get_user_profile(token_data['access_token'])
                            if user_profile:
                                st.session_state.user = user_profile
                                st.session_state.authenticated = True
                                st.success("Login successful!")
                                st.rerun()
                            else:
                                st.error("Failed to load user profile")
                        else:
                            st.error("Invalid username or password")
