"""
Dashboard authentication helpers for GE Pulse.
"""
import os
import time

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("API_URL", "http://localhost:8000").rstrip("/")
SESSION_TIMEOUT_SECONDS = int(os.getenv("SESSION_TIMEOUT_SECONDS", "1800"))


def login(username, password):
    """Authenticate user with the API."""
    try:
        response = requests.post(
            f"{API_URL}/token",
            data={"username": username, "password": password},
            timeout=5,
        )
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as exc:
        st.error(f"Connection error: {exc}")
        return None


def demo_login(role):
    """Start a passwordless demo session for a selected role."""
    try:
        response = requests.post(
            f"{API_URL}/api/v1/auth/demo-login",
            json={"role": role},
            timeout=5,
        )
        if response.status_code == 200:
            return response.json()
        st.error(response.json().get("detail", "Demo login is unavailable"))
        return None
    except Exception as exc:
        st.error(f"Connection error: {exc}")
        return None


def _ensure_session_defaults():
    if "token" not in st.session_state:
        st.session_state.token = None
        st.session_state.user = None
        st.session_state.authenticated = False
        st.session_state.login_at = None
        st.session_state.expires_in = SESSION_TIMEOUT_SECONDS


def check_auth():
    """Check whether the current Streamlit session is authenticated and fresh."""
    _ensure_session_defaults()
    if st.session_state.authenticated and st.session_state.login_at:
        if time.time() - st.session_state.login_at > st.session_state.expires_in:
            st.warning("Your session expired. Please sign in again.")
            logout()
    return st.session_state.authenticated


def logout():
    """Clear dashboard session state."""
    st.session_state.token = None
    st.session_state.user = None
    st.session_state.authenticated = False
    st.session_state.login_at = None
    st.rerun()


def get_user_profile(token):
    """Get the current user's profile from the API."""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{API_URL}/users/me", headers=headers, timeout=5)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception:
        return None


def _complete_login(token_data):
    st.session_state.token = token_data["access_token"]
    user_profile = get_user_profile(token_data["access_token"])
    st.session_state.user = user_profile or {
        "username": token_data.get("role", "demo"),
        "role": token_data.get("role", "operator"),
    }
    st.session_state.authenticated = True
    st.session_state.login_at = time.time()
    st.session_state.expires_in = token_data.get("expires_in", SESSION_TIMEOUT_SECONDS)
    st.rerun()


def render_login_page():
    """Render login and demo entry points."""
    st.title("GE Pulse")
    st.caption("Factory rhythm, clear. A shop-floor intelligence demo from S7 Inc.")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("### Sign in")
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
                            _complete_login(token_data)
                        else:
                            st.error("Invalid username or password")

        st.markdown("### Demo mode")
        demo_role = st.selectbox(
            "Open demo as",
            ["operator", "supervisor", "maintenance", "manager", "admin"],
        )
        if st.button("Launch Demo", use_container_width=True):
            token_data = demo_login(demo_role)
            if token_data:
                _complete_login(token_data)

        st.info("Local admin password login: admin / admin123.")
