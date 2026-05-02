"""
Dashboard authentication helpers for Acron by S7 Corp.
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


def _inject_login_css():
    st.markdown(
        """
        <style>
        html, body, [data-testid="stAppViewContainer"] {
            background: #f4f6f9;
            color: #111827;
        }
        .block-container {
            max-width: 1120px;
            padding-top: 4rem;
        }
        [data-testid="stHeader"] {
            background: rgba(244, 246, 249, .82);
        }
        h1, h2, h3 {
            color: #111827;
            letter-spacing: 0;
        }
        .login-brand {
            background: #111827;
            border: 1px solid #263241;
            border-right: 1px solid #263241;
            border-radius: 8px;
            color: #f8fafc;
            min-height: 558px;
            padding: 34px;
        }
        .login-mark {
            align-items: center;
            background: #f8fafc;
            border-radius: 8px;
            color: #111827;
            display: flex;
            font-size: 1rem;
            font-weight: 900;
            height: 48px;
            justify-content: center;
            margin-bottom: 28px;
            width: 48px;
        }
        .login-title {
            color: #ffffff;
            font-size: 2.1rem;
            font-weight: 850;
            line-height: 1.05;
            margin-bottom: 10px;
        }
        .login-copy {
            color: #b7c2d2;
            font-size: .98rem;
            line-height: 1.55;
            max-width: 420px;
        }
        .login-proof {
            border-top: 1px solid #263241;
            display: grid;
            gap: 14px;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            margin-top: 34px;
            padding-top: 24px;
        }
        .proof-value {
            color: #ffffff;
            font-size: 1.35rem;
            font-weight: 850;
        }
        .proof-label {
            color: #9aa8bb;
            font-size: .78rem;
            margin-top: 2px;
        }
        .login-panel {
            background: #ffffff;
            border: 1px solid #d7dee8;
            border-radius: 8px;
            box-shadow: 0 18px 48px rgba(17, 24, 39, .10);
            min-height: 558px;
            padding: 34px;
        }
        .login-panel [data-testid="stForm"] {
            border: 0;
            padding: 0;
        }
        div[data-testid="stButton"] > button,
        div[data-testid="stFormSubmitButton"] > button {
            border-radius: 8px;
            font-weight: 750;
            min-height: 42px;
        }
        .demo-note {
            background: #f8fafc;
            border: 1px solid #d7dee8;
            border-radius: 8px;
            color: #5b6678;
            font-size: .84rem;
            line-height: 1.45;
            margin-top: 14px;
            padding: 12px;
        }
        @media (max-width: 860px) {
            .block-container {padding-top: 1.2rem;}
            .login-brand {min-height: auto;}
            .login-panel {min-height: auto;}
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_login_page():
    """Render login and demo entry points."""
    _inject_login_css()

    brand_col, form_col = st.columns([0.95, 1.05], gap="large")

    with brand_col:
        st.markdown(
            """
            <div class="login-brand">
                <div class="login-mark">⬡</div>
                <div class="login-title">Acron</div>
                <div class="login-copy">
                    Intelligence meets reality. An industrial IoT intelligence platform from S7 Corp
                    for live OEE, predictive maintenance, downtime capture, and AI-powered insights.
                </div>
                <div class="login-proof">
                    <div><div class="proof-value">30+</div><div class="proof-label">demo assets</div></div>
                    <div><div class="proof-value">5</div><div class="proof-label">factory roles</div></div>
                    <div><div class="proof-value">4</div><div class="proof-label">connector paths</div></div>
                    <div><div class="proof-value">24/7</div><div class="proof-label">health checks</div></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with form_col:
        st.markdown('<div class="login-panel">', unsafe_allow_html=True)
        st.subheader("Sign in")
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Sign in", width="stretch")
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

        st.divider()
        st.subheader("Demo role")
        role = st.selectbox(
            "Open demo as",
            ["operator", "supervisor", "maintenance", "manager", "admin"],
            help="Each role opens the same live demo with role-specific actions and access.",
        )
        if st.button("Launch demo", width="stretch"):
            token_data = demo_login(role)
            if token_data:
                _complete_login(token_data)

        st.markdown(
            '<div class="demo-note">Local admin password login: admin / admin123.</div></div>',
            unsafe_allow_html=True,
        )

