"""
Single-file Streamlit demo for Login + MFA (OTP + Push) + automation-friendly API

How to run:
1. pip install streamlit pyotp flask requests
2. streamlit run streamlit_mfa_demo.py

What it provides:
- Streamlit UI with Login -> MFA -> Dashboard
- Embedded Flask API (runs on port 8001) exposing endpoints used by automation:
    POST /api/get_otp    -> {"username": "..."}  returns {"otp": "123456"}
    POST /api/push_send  -> {"username": "..."}  returns {"push_id": "..."}
    POST /api/push_approve -> {"push_id": "..."} returns {"status": "approved"}
    GET  /api/push_status?id=... -> {"status": "pending"|"approved"}

Automation demo snippet (use requests):
    resp = requests.post('http://localhost:8001/api/get_otp', json={'username':'admin'})
    otp = resp.json()['otp']
    # then send otp to the UI input by automation tool (Selenium / Playwright)

Notes:
- This is a demo: secrets are stored in-memory and OTP generation uses pyotp TOTP.
- For safety, do NOT use these secrets in production.
"""

import streamlit as st
import pyotp
import threading
import time
import secrets
import string
from flask import Flask, request, jsonify
import requests

# -------------------------
# Demo user store (in-memory)
# -------------------------
USERS = {
    "admin": {
        "password": "admin123",
        # base32 secret for pyotp
        "mfa_secret": pyotp.random_base32()
    },
    "demo": {
        "password": "demo123",
        "mfa_secret": pyotp.random_base32()
    }
}

# For push notifications simulation
PUSH_STORE = {}  # push_id -> {username, status}

# -------------------------
# Embedded Flask API
# -------------------------
api_app = Flask(__name__)

@api_app.route('/api/get_otp', methods=['POST'])
def api_get_otp():
    data = request.get_json(force=True)
    username = data.get('username')
    if not username or username not in USERS:
        return jsonify({"error": "unknown user"}), 400
    secret = USERS[username]['mfa_secret']
    totp = pyotp.TOTP(secret)
    otp = totp.now()
    return jsonify({"otp": otp})

@api_app.route('/api/push_send', methods=['POST'])
def api_push_send():
    data = request.get_json(force=True)
    username = data.get('username')
    if not username or username not in USERS:
        return jsonify({"error": "unknown user"}), 400
    # create push id
    push_id = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))
    PUSH_STORE[push_id] = {"username": username, "status": "pending", "created_at": time.time()}
    return jsonify({"push_id": push_id})

@api_app.route('/api/push_approve', methods=['POST'])
def api_push_approve():
    data = request.get_json(force=True)
    push_id = data.get('push_id')
    if not push_id or push_id not in PUSH_STORE:
        return jsonify({"error": "unknown push_id"}), 400
    PUSH_STORE[push_id]['status'] = 'approved'
    return jsonify({"status": "approved"})

@api_app.route('/api/push_status', methods=['GET'])
def api_push_status():
    push_id = request.args.get('id')
    if not push_id or push_id not in PUSH_STORE:
        return jsonify({"error": "unknown push_id"}), 400
    return jsonify({"status": PUSH_STORE[push_id]['status']})


def run_api():
    # Run flask in a background thread. In production use a proper ASGI/Wsgi server.
    api_app.run(host='0.0.0.0', port=8001, debug=False, use_reloader=False)


# Start API thread
api_thread = threading.Thread(target=run_api, daemon=True)
api_thread.start()

# -------------------------
# Streamlit UI
# -------------------------
st.set_page_config(page_title="MFA Demo", layout="centered")

if 'page' not in st.session_state:
    st.session_state.page = 'login'

if 'username' not in st.session_state:
    st.session_state.username = None

st.title("🔒 Streamlit Login + MFA Demo")

# --- Login Page ---
if st.session_state.page == 'login':
    st.header("Login")
    with st.form('login_form'):
        username = st.text_input('Username')
        password = st.text_input('Password', type='password')
        submitted = st.form_submit_button('Login')
    if submitted:
        user = USERS.get(username)
        if user and user['password'] == password:
            st.success('Credentials valid — proceeding to MFA')
            st.session_state.username = username
            st.session_state.page = 'mfa'
            st.rerun()
        else:
            st.error('Invalid username or password')

# --- MFA Page ---
elif st.session_state.page == 'mfa':
    if not st.session_state.username:
        st.error('No active session — please login')
        if st.button('Go to Login'):
            st.session_state.page = 'login'
            st.rerun()
    else:
        st.header('Multi-Factor Authentication')
        st.markdown(f"**User:** {st.session_state.username}")
        method = st.radio('Choose MFA method', ['OTP (TOTP)', 'Push Notification'])

        if method == 'OTP (TOTP)':
            st.info('This demo uses TOTP (pyotp). You can fetch the OTP via the local API for automation.')
            col1, col2 = st.columns([2,1])
            with col1:
                otp_input = st.text_input('Enter OTP')
            with col2:
                if st.button('Fetch OTP via API'):
                    try:
                        resp = requests.post('http://localhost:8001/api/get_otp', json={'username': st.session_state.username}, timeout=2)
                        if resp.status_code == 200:
                            otp_val = resp.json().get('otp')
                            st.session_state._fetched_otp = otp_val
                            st.success('OTP fetched via API (for automation)')
                        else:
                            st.error('API error: ' + str(resp.text))
                    except Exception as e:
                        st.error('Failed to reach API: ' + str(e))

            # show fetched otp for demo (only in demo mode!)
            if '_fetched_otp' in st.session_state:
                st.info('DEBUG: fetched OTP = ' + st.session_state._fetched_otp)

            if st.button('Verify OTP'):
                secret = USERS[st.session_state.username]['mfa_secret']
                totp = pyotp.TOTP(secret)
                to_verify = otp_input if otp_input else st.session_state.get('_fetched_otp')
                if not to_verify:
                    st.warning('No OTP provided — either enter manually or click "Fetch OTP via API"')
                else:
                    if totp.verify(to_verify):
                        st.success('MFA Verified — logged in')
                        st.session_state.page = 'dashboard'
                        st.rerun()
                    else:
                        st.error('Invalid OTP')

        else:  # Push Notification
            st.info('Push flow: automation can call /api/push_send then /api/push_approve to simulate approval')
            if st.button('Send Push'):
                try:
                    resp = requests.post('http://localhost:8001/api/push_send', json={'username': st.session_state.username}, timeout=2)
                    if resp.status_code == 200:
                        push_id = resp.json().get('push_id')
                        st.session_state.push_id = push_id
                        st.success(f'Push sent (id={push_id}). Polling for approval...')
                    else:
                        st.error('API error: ' + str(resp.text))
                except Exception as e:
                    st.error('Failed to reach API: ' + str(e))

            if 'push_id' in st.session_state:
                st.write('Push id:', st.session_state.push_id)
                if st.button('Check Push Status'):
                    try:
                        resp = requests.get('http://localhost:8001/api/push_status', params={'id': st.session_state.push_id}, timeout=2)
                        if resp.status_code == 200:
                            status = resp.json().get('status')
                            if status == 'approved':
                                st.success('Push approved — logged in')
                                st.session_state.page = 'dashboard'
                                st.rerun()
                            else:
                                st.info('Push status: ' + status)
                        else:
                            st.error('API error: ' + str(resp.text))
                    except Exception as e:
                        st.error('Failed to reach API: ' + str(e))

        st.divider()
        if st.button('Cancel and logout'):
            st.session_state.clear()
            st.rerun()

# --- Dashboard ---
elif st.session_state.page == 'dashboard':
    if not st.session_state.username:
        st.error('No active session — please login')
    else:
        st.header('Dashboard')
        st.success(f'Welcome, {st.session_state.username}! You are authenticated.')
        st.write('This is a simple demo dashboard. Use the API endpoints to show how automation can complete MFA:')
        st.markdown('''
        **Automation examples**
        - Fetch OTP: `POST http://localhost:8001/api/get_otp` with JSON `{ "username": "admin" }`
        - Send Push: `POST http://localhost:8001/api/push_send` with JSON `{ "username": "admin" }` returns `push_id`
        - Approve Push (automation): `POST http://localhost:8001/api/push_approve` with JSON `{ "push_id": "..." }`
        - Poll Push Status: `GET http://localhost:8001/api/push_status?id=...`
        ''')
        if st.button('Logout'):
            st.session_state.clear()
            st.rerun()

# -------------------------
# End of file
# -------------------------
