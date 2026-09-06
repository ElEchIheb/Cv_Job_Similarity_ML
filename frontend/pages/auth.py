import streamlit as st
import requests
from src.config import settings
from frontend.styles.theme import ICONS

# Determine the API base URL (assuming backend runs on localhost:8000 for local dev)
API_BASE_URL = "http://localhost:8000/api/v1"


def _auth_brand(title: str, subtitle: str):
    st.markdown(f"""
        <div style="text-align:center;margin:1.5rem 0 1.75rem;">
          <div style="display:inline-flex;align-items:center;gap:11px;margin-bottom:1.5rem;">
            <div class="nh-brand-icon" style="width:44px;height:44px;border-radius:12px;">{ICONS['zap']}</div>
            <div style="font-family:'Space Grotesk',sans-serif;font-size:1.5rem;font-weight:700;
                        letter-spacing:-0.03em;color:var(--text-primary);">Neural<span class="accent"
                        style="background:var(--grad-brand);-webkit-background-clip:text;
                        -webkit-text-fill-color:transparent;background-clip:text;">Hire</span></div>
          </div>
          <h1 style="font-family:'Space Grotesk',sans-serif;font-size:2.1rem;font-weight:700;
                     letter-spacing:-0.03em;margin-bottom:0.4rem;color:var(--text-primary);">{title}</h1>
          <p style="color:var(--text-secondary);font-size:1rem;">{subtitle}</p>
        </div>
    """, unsafe_allow_html=True)


def login_page():
    _auth_brand("Welcome back", "Sign in to your NeuralHire account")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            email = st.text_input("Email", placeholder="name@company.com")
            password = st.text_input("Password", type="password", placeholder="••••••••")
            submit = st.form_submit_button("Sign In", type="primary", width="stretch")
            
            if submit:
                if not email or not password:
                    st.error("Please fill in all fields.")
                else:
                    try:
                        response = requests.post(
                            f"{API_BASE_URL}/auth/login",
                            data={"username": email, "password": password}
                        )
                        if response.status_code == 200:
                            data = response.json()
                            st.session_state.access_token = data["access_token"]
                            st.session_state.just_logged_in = data["access_token"]
                            st.rerun()
                        else:
                            st.error(f"Login failed: {response.json().get('detail', 'Unknown error')}")
                    except Exception as e:
                        st.error("Unable to connect to the server.")
                        
        st.markdown("<div style='text-align: center; margin-top: 1rem;'>Don't have an account?</div>", unsafe_allow_html=True)
        if st.button("Create an account", width="stretch"):
            st.session_state.auth_view = "register"
            st.rerun()


def register_page():
    _auth_brand("Create an account", "Join NeuralHire to evaluate candidates with AI")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("register_form"):
            full_name = st.text_input("Full Name", placeholder="Jane Doe")
            email = st.text_input("Email", placeholder="name@company.com")
            password = st.text_input("Password", type="password", placeholder="••••••••")
            confirm_password = st.text_input("Confirm Password", type="password", placeholder="••••••••")
            submit = st.form_submit_button("Sign Up", type="primary", width="stretch")
            
            if submit:
                if not full_name or not email or not password:
                    st.error("Please fill in all fields.")
                elif password != confirm_password:
                    st.error("Passwords do not match.")
                else:
                    try:
                        response = requests.post(
                            f"{API_BASE_URL}/auth/register",
                            json={"email": email, "password": password, "full_name": full_name}
                        )
                        if response.status_code == 200:
                            st.success("Account created successfully! Please sign in.")
                            st.session_state.auth_view = "login"
                        else:
                            st.error(f"Registration failed: {response.json().get('detail', 'Unknown error')}")
                    except Exception as e:
                        st.error("Unable to connect to the server.")
                        
        st.markdown("<div style='text-align: center; margin-top: 1rem;'>Already have an account?</div>", unsafe_allow_html=True)
        if st.button("Sign in", width="stretch"):
            st.session_state.auth_view = "login"
            st.rerun()


def render():
    if "auth_view" not in st.session_state:
        st.session_state.auth_view = "login"
        
    if st.session_state.auth_view == "login":
        login_page()
    else:
        register_page()
