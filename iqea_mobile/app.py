import streamlit as st
from device_manager import get_connected_devices
from recorder import start_session, stop_session
from action_logger import save_actions
from script_generator import generate_python_appium_script

st.title("📱 IQEA Mobile Automation")

# 🔹 Device Selection
st.header("Device Selection")

devices = get_connected_devices()

device = st.selectbox("Select Device", devices)

mode = st.radio("Execution Mode", ["Real Device (USB)", "Emulator", "BrowserStack"])

# 🔹 App / Browser Selection
st.header("Automation Type")

automation_type = st.radio("Choose Type", ["Native App", "Mobile Browser"])

app_package = None
app_activity = None
url = None

if automation_type == "Native App":
    app_package = st.text_input("App Package")
    app_activity = st.text_input("App Activity")
else:
    url = st.text_input("Enter URL")

# 🔹 Start Recording
st.header("Recording")

if st.button("Start Recording"):
    start_session(
        device_id=device,
        app_package=app_package,
        app_activity=app_activity,
        browser=(automation_type == "Mobile Browser")
    )
    st.success("Session Started")

if st.button("Stop Recording"):
    stop_session()
    save_actions()
    st.success("Actions Saved")

# 🔹 Script Generation
st.header("Script Generation")

lang = st.selectbox("Select Language", ["Python + Appium"])

if st.button("Generate Script"):
    script = generate_python_appium_script()
    st.code(script, language="python")