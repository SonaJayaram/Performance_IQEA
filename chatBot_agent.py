import streamlit as st
import utilities.Utilities_Xpath as utils
import utilities.utils_action as action_utils
import utilities.db_utils.handler as db_handler

# ---------------------------
# Streamlit Chatbot Setup
# ---------------------------

st.set_page_config(page_title="AI QE Chatbot", layout="centered")
st.title("🤖 AI QE Chatbot Assistant")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "flow_step" not in st.session_state:
    st.session_state.flow_step = "start"
if "context" not in st.session_state:
    st.session_state.context = {
        "option": None,
        "url": None,
        "req_docs_text": None,
        "additional_info": None,
        "generated_output": None
    }

# Function to show chat messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


# ---------------------------
# Helper to send chatbot reply
# ---------------------------
def bot_reply(message):
    st.session_state.messages.append({"role": "assistant", "content": message})
    st.chat_message("assistant").markdown(message)


# ---------------------------
# Chat Flow Logic
# ---------------------------
def handle_user_input(user_msg):
    ctx = st.session_state.context
    step = st.session_state.flow_step

    # Save user message
    st.session_state.messages.append({"role": "user", "content": user_msg})

    # ---- Start ----
    if step == "start":
        bot_reply("Hello 👋! What would you like to do today?\n\nOptions: Test Case Generation, Test Script Generation, or Report Comparison?")
        st.session_state.flow_step = "select_option"

    # ---- Option Selection ----
    elif step == "select_option":
        ctx["option"] = user_msg.strip()
        bot_reply("Got it! Do you have a URL to include? (Yes/No)")
        st.session_state.flow_step = "ask_url"

    # ---- Ask for URL ----
    elif step == "ask_url":
        if user_msg.lower() == "yes":
            bot_reply("Please enter the URL:")
            st.session_state.flow_step = "get_url"
        else:
            ctx["url"] = ""
            bot_reply("Do you have any requirement documents to upload? (Yes/No)")
            st.session_state.flow_step = "ask_req_docs"

    elif step == "get_url":
        ctx["url"] = user_msg.strip()
        bot_reply("Do you have any requirement documents to upload? (Yes/No)")
        st.session_state.flow_step = "ask_req_docs"

    # ---- Ask for Requirement Documents ----
    elif step == "ask_req_docs":
        if user_msg.lower() == "yes":
            bot_reply("Please upload your documents (.pdf, .docx, .txt, .png, .jpg):")
            st.session_state.flow_step = "upload_docs"
        else:
            ctx["req_docs_text"] = ""
            bot_reply("Do you have any additional details? (Yes/No)")
            st.session_state.flow_step = "ask_additional"

    # ---- Ask for Additional Info ----
    elif step == "ask_additional":
        if user_msg.lower() == "yes":
            bot_reply("Please enter the additional information:")
            st.session_state.flow_step = "get_additional"
        else:
            ctx["additional_info"] = ""
            bot_reply(f"Shall we generate {ctx['option']} now? (Yes/No)")
            st.session_state.flow_step = "generate"

    elif step == "get_additional":
        ctx["additional_info"] = user_msg.strip()
        bot_reply(f"Shall we generate {ctx['option']} now? (Yes/No)")
        st.session_state.flow_step = "generate"

    # ---- Generate Output ----
    elif step == "generate":
        if user_msg.lower() == "yes":
            with st.spinner("Generating... please wait"):
                # 🔹 Replace this with your actual AI/test generation logic
                st.session_state.context["generated_output"] = f"""
**Generated {ctx['option']}:**

URL: {ctx['url'] or 'N/A'}
Additional Info: {ctx['additional_info'] or 'N/A'}
Extracted Document Content (Preview):
{ctx['req_docs_text'][:300] if ctx['req_docs_text'] else 'N/A'}...
"""
            bot_reply("✅ Generation complete!")
            bot_reply(st.session_state.context["generated_output"])
            bot_reply("Do you want to upload this to your Test Management Tool? (Yes/No)")
            st.session_state.flow_step = "ask_upload_tool"
        else:
            bot_reply("Okay, skipping generation. Do you want to upload to a Test Management Tool? (Yes/No)")
            st.session_state.flow_step = "ask_upload_tool"

    # ---- Upload to Test Management Tool ----
    elif step == "ask_upload_tool":
        if user_msg.lower() == "yes":
            bot_reply("Please provide the API Endpoint, API Key, and Project ID in the sidebar. Then type 'Done' once configured.")
            st.session_state.flow_step = "confirm_upload"
        else:
            bot_reply("🎉 Workflow complete! Type 'Restart' to start again.")
            st.session_state.flow_step = "done"

    elif step == "confirm_upload":
        if user_msg.lower() == "done":
            # 🔹 Replace this with your upload logic
            bot_reply("✅ Successfully uploaded to Test Management Tool!")
            bot_reply("🎉 Workflow complete. Type 'Restart' to start over.")
            st.session_state.flow_step = "done"

    elif step == "done":
        if user_msg.lower() == "restart":
            st.session_state.flow_step = "start"
            st.session_state.context = {
                "option": None,
                "url": None,
                "req_docs_text": None,
                "additional_info": None,
                "generated_output": None
            }
            bot_reply("Restarting... What would you like to do? (Test Case Generation / Test Script Generation / Report Comparison)")
            st.session_state.flow_step = "select_option"


# ---------------------------
# Document Upload Section (Dynamic)
# ---------------------------
if st.session_state.flow_step == "upload_docs":
    uploaded_files = st.file_uploader(
        "Upload your requirement documents:",
        type=["pdf", "docx", "txt", "png", "jpg", "jpeg"],
        accept_multiple_files=True
    )
    if uploaded_files:
        extracted_text = utils.extract_text_from_document(uploaded_files, uploaded_files[0].name)
        st.session_state.context["req_docs_text"] = extracted_text
        bot_reply("✅ Documents processed successfully.")
        bot_reply("Do you have any additional details? (Yes/No)")
        st.session_state.flow_step = "ask_additional"

# ---------------------------
# Sidebar Configuration for Upload
# ---------------------------
# with st.sidebar:
#     st.subheader("🔧 Test Management Config")
#     st.text_input("API Endpoint:")
#     st.text_input("API Key:", type="password")
#     st.text_input("Project ID:")

# ---------------------------
# Chat Input
# ---------------------------
if user_input := st.chat_input("Type your response..."):
    handle_user_input(user_input)
    st.rerun()
