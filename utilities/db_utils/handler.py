from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from io import BytesIO
import csv
import zipfile
from utilities.db_utils.models import *
from config.settings_reader import get_db_url
import os
import io
import pandas as pd
import streamlit as st
import tempfile
from datetime import datetime
from urllib.parse import urlparse
import re
from sqlalchemy.exc import SQLAlchemyError

engine = create_engine(get_db_url())
Session = sessionmaker(bind=engine)
session = Session()

def bulk_add_prompts(prompt_data_list, created_by):
    """
    prompt_data_list: List of dicts with keys - prompt_name, prompt_text, description (optional)
    """
    added = []
    skipped = []

    for data in prompt_data_list:
        prompt_name = data.get("prompt_name")
        existing = session.query(Prompt).filter_by(prompt_name=prompt_name).first()

        if existing:
            skipped.append(prompt_name)
            continue

        new_prompt = Prompt(
            prompt_name=prompt_name,
            prompt_text=data.get("prompt_text"),
            description=data.get("description"),
            created_by=created_by,
            updated_by=created_by,
            created_on=datetime.utcnow(),
            updated_on=datetime.utcnow()
        )
        session.add(new_prompt)
        added.append(prompt_name)

    session.commit()
    print(f"✅ Added prompts: {added}")
    if skipped:
        print(f"⚠️ Skipped existing prompts: {skipped}")

def add_prompt(prompt_name, prompt_text, created_by, description=None):
    existing = session.query(Prompt).filter_by(prompt_name=prompt_name).first()
    if existing:
        print(f"⚠️ Prompt '{prompt_name}' already exists.")
        return

    new_prompt = Prompt(
        prompt_name=prompt_name,
        prompt_text=prompt_text,
        description=description,
        created_by=created_by,
        updated_by=created_by,
        created_on=datetime.utcnow(),
        updated_on=datetime.utcnow()
    )
    session.add(new_prompt)
    session.commit()
    print(f"✅ Prompt '{prompt_name}' added.")

def get_prompt_by_name(prompt_name):
    prompt = session.query(Prompt).filter_by(prompt_name=prompt_name).first()
    if prompt:
        return prompt.prompt_text
    else:
        print(f"⚠️ Prompt '{prompt_name}' not found.")
        return None
    
def save_action_to_db(action_name, content, created_by):
    if isinstance(content, list):
        content = "\n".join(content)

    file_binary = content.encode("utf-8")

    action = Action(
        action_name=f"{action_name}.txt",
        file_data=file_binary,
        created_by=created_by
    )

    session.add(action)
    session.commit()
    return action.id

def save_testfile_to_db(test_name, content, created_by, language):
    if language in ["Java-Selenium", "Java-Playwright"]:
        language = "java"
    elif language in ["Python-Selenium", "Python-Playwright"]:
        language = "python"
    ext = "java" if language == "java" else "py"
    file_name = f"{test_name}.{ext}"

    if isinstance(content, list):
        content = "\n".join(content)

    file_binary = content.encode("utf-8")

    testfile = Testfile(
        testfile_name=file_name,
        file_data=file_binary,
        created_by=created_by
    )

    session.add(testfile)
    session.commit()
    st.write("✅ Test file script generated and saved in DB")
    return testfile.id

def save_pagefile_to_db(page_name, content, created_by, language):
    if language in ["Java-Selenium", "Java-Playwright"]:
        file_extension = "java"
    elif language in ["Python-Selenium", "Python-Playwright"]:
        file_extension = "python"
    ext = "java" if language == "java" else "py"
    file_name = f"{page_name}.{ext}"

    if isinstance(content, list):
        content = "\n".join(content)

    file_binary = content.encode("utf-8")

    pagefile = Pagefile(
        pagefile_name=file_name,
        file_data=file_binary,
        created_by=created_by
    )

    session.add(pagefile)
    session.commit()
    return pagefile.id


def save_featurefile_to_db(page_name, content, created_by):
    file_name = f"{page_name}.feature"

    if isinstance(content, list):
        content = "\n".join(content)

    file_binary = content.encode("utf-8")

    featurefile = Fetaurefile(
        featurefile_name=file_name,
        file_data=file_binary,
        created_by=created_by
    )

    session.add(featurefile)
    session.commit()
    return featurefile.id


def save_testcases_to_db(testcase_name, dataframe: pd.DataFrame, created_by):
    try:
        # Convert DataFrame to real Excel binary
        buffer = io.BytesIO()
        dataframe.to_excel(buffer, index=False)
        buffer.seek(0)
        file_binary = buffer.read()

        testcase = Testcasefile(
            testcase_name=testcase_name,
            file_data=file_binary,
            created_by=created_by
        )

        session.add(testcase)
        session.commit()
        return testcase.id

    except SQLAlchemyError as e:
        session.rollback()
        print(f"❌ Database error: {e}")
        raise

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        raise

def save_testcases_to_db_old(testcase_name, content, created_by):
    try:
        # Case 1: content is a list of dictionaries (structured like a CSV)
        if isinstance(content, list) and content and isinstance(content[0], dict):
            buffer = io.StringIO()
            writer = csv.DictWriter(buffer, fieldnames=content[0].keys())
            writer.writeheader()
            writer.writerows(content)
            file_binary = buffer.getvalue().encode("utf-8")

        # Case 2: fallback for plain text or other formats
        else:
            file_binary = str(content).encode("utf-8")

        # Create the database object
        testcase = Testcasefile(
            testcase_name=testcase_name,
            file_data=file_binary,
            created_by=created_by
        )

        session.add(testcase)
        session.commit()
        return testcase.id

    except SQLAlchemyError as e:
        session.rollback()
        print(f"❌ Database error: {e}")
        raise

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        raise
def get_action_file_by_name(action_name):
    # action = session.query(Action).filter_by(action_name=action_name).first()
    action = session.query(Action).filter(Action.action_name.ilike(f"%{action_name}%")).first()
    if action:
        # Save the binary file data as a temp file
        temp_file_path = f"temp_files/{action_name}"  # store in a temp folder
        os.makedirs("temp_files", exist_ok=True)  # ensure the folder exists

        with open(temp_file_path, "wb") as f:
            f.write(action.file_data)

        return temp_file_path
    else:
        raise FileNotFoundError(f"No file found in DB with name: {action_name}")

def get_all_screenshot_names():
  # adjust if your model is named differently
    return [action.page_name for action in session.query(Screenshot).all()]
def get_all_action_names():
  # adjust if your model is named differently
    return [action.action_name for action in session.query(Action).all()]
def get_all_pagefile_names():
  # adjust if your model is named differently
    return [action.pagefile_name for action in session.query(Pagefile).all()]
def get_all_testfile_names():
  # adjust if your model is named differently
    return [action.testfile_name for action in session.query(Testfile).all()]
def get_all_testcasefile_names():
  # adjust if your model is named differently
    return [action.testcase_name for action in session.query(Testcasefile).all()]


def get_action_content_by_name(action_name: str, type: str) -> str:
    """
    Fetches the content of the action file from the database by action_name.
    Supports .txt, .py, .java (as text), and .xlsx (as parsed table).
    """
    if type == "page":
        action = session.query(Pagefile).filter(Pagefile.pagefile_name.ilike(f"%{action_name}%")).first()
    elif type == "testcase":
        action = session.query(Testcasefile).filter(Testcasefile.testcase_name.ilike(f"%{action_name}%")).first()
    elif type == "test":
        action = session.query(Testfile).filter(Testfile.testfile_name.ilike(f"%{action_name}%")).first()
    elif type == "action":
        action = session.query(Action).filter(Action.action_name.ilike(f"%{action_name}%")).first()

    else:
        return f"[Error: Unknown type '{type}']"

    if not action or not action.file_data:
        return None

    # Determine file extension
    _, ext = os.path.splitext(action_name.lower())

    try:
        if ext in [".txt", ".py", ".java"]:
            return action.file_data.decode("utf-8", errors="ignore")

        elif ext == ".xlsx":
            # Read Excel binary using pandas
            excel_buffer = io.BytesIO(action.file_data)
            df = pd.read_excel(excel_buffer)
            return df.to_string(index=False)

        else:
            return f"[Unsupported file type: {ext}]"

    except Exception as e:
        return f"[Error reading file: {str(e)}]"
    

def prepare_selected_files_for_github(selected_file_names):
    """
    1. Takes list of selected file names from UI (either .java or .py)
    2. Creates physical files in a temp directory using DB content
    3. Returns temp folder path containing those files for pushing to GitHub
    4. You are expected to delete temp folder after GitHub push
    """
     # Create a temporary directory
    temp_dir = tempfile.mkdtemp(prefix="push_github_")

    for file_name in selected_file_names:
        file_ext = os.path.splitext(file_name)[1].lower()

        # Determine model type based on file name or extension
        file_record = None
        if file_ext == ".py" or file_ext == ".java":
            file_record = (
                session.query(Pagefile).filter_by(pagefile_name=file_name).first()
                or session.query(Testfile).filter_by(testfile_name=file_name).first()
            )

        if not file_record:
            st.warning(f"⚠️ No record found for file: {file_name}")
            continue

        # Write binary content to actual file
        temp_file_path = os.path.join(temp_dir, file_name)
        with open(temp_file_path, "wb") as f:
            f.write(file_record.file_data)

        st.success(f"✅ Prepared {file_name} for GitHub upload")

    return temp_dir  # You'll use this path to push to GitHub

def get_screenshots_from_db(page_name: str = None):
    query = session.query(Screenshot)
    if page_name:
        query = query.filter(Screenshot.page_name == page_name)
    return query.order_by(Screenshot.created_on.desc()).all()

def get_all_screenshots():
    print(session.query(Screenshot).order_by(Screenshot.created_on.desc()).all())
    return session.query(Screenshot).order_by(Screenshot.created_on.desc()).all()

def take_screenshot_db(driver,created_by="system"):
    url = driver.current_url
    parsed_url = urlparse(url)
    page_name = re.sub(r'[\\/*?:"<>|]', "_", parsed_url.path.strip("/") or None)

    screenshot_bytes = driver.get_screenshot_as_png()

    screenshot_record = Screenshot(
        page_name=page_name,
        url=url,
        image_data=screenshot_bytes,
        created_by=created_by
    )
    session.add(screenshot_record)
    session.commit()

    return f"DB_Record_ID: {screenshot_record.id}"

def download_files_from_database(file_names: list, file_type: str) -> bytes:
    """
    Given a list of filenames and file type, fetch content from DB and return zipped bytes
    """
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
        for name in file_names:
            # 🔁 Fetch content from the DB
            content = get_file_content_by_type(name, file_type)  # You need to implement this dispatcher
            if content:
                print(f"[DEBUG] Writing {name}, type={type(content)}")
                zipf.writestr(name, content)

    zip_buffer.seek(0)
    return zip_buffer.read()

def get_file_content_by_type(name: str, file_type: str):
    return get_file_content_by_name(name,file_type)

def get_file_content_by_name(action_name: str, type: str) -> str:
    """
    Fetches the content of the specified file type from the database using action_name.
    Supports:
    - .txt, .py, .java as UTF-8 text
    - .xlsx as parsed table using pandas
    - .png/.jpg/.jpeg/.bmp as image bytes (base64 encoded for web display)
    """
    model_map = {
        "Page_file": (Pagefile, "pagefile_name"),
        "Testcase_file": (Testcasefile, "testcase_name"),
        "Test_file": (Testfile, "testfile_name"),
        "Recorded_Action_file": (Action, "action_name")

    }

    if type not in model_map:
        return f"[Error: Unknown type '{type}']"

    model, name_field = model_map[type]
    action = session.query(model).filter(getattr(model, name_field).ilike(f"%{action_name}%")).first()

    if not action or not getattr(action, "file_data", None):
        return f"[No file data found for: {action_name}]"

    # Determine file extension
    _, ext = os.path.splitext(action_name.lower())

    try:
        if ext in [".txt", ".py", ".java"]:
            return action.file_data.decode("utf-8", errors="ignore")


        elif ext == ".xlsx":
            return action.file_data

        elif ext in [".png", ".jpg", ".jpeg", ".bmp",".html"]:
            # 👇 Return base64-encoded image string (for rendering or download)
            import base64
            encoded = base64.b64encode(action.file_data).decode('utf-8')
            return f"data:image/{ext[1:]};base64,{encoded}"

        else:
            return f"[Unsupported file type: {ext}]"

    except Exception as e:
        return f"[Error reading file: {str(e)}]"
