import os
import json
import pandas as pd
import base64
import streamlit as st
import Utils.self_healing_framework_utilities as healing_framework_utils
import gitlab
from dotenv import load_dotenv
load_dotenv()


# ─── GitLab helpers ───────────────────────────────────────────────────────────
def get_gitlab_project(git_repo_url, token):
    gl = gitlab.Gitlab("https://git.tigeranalytics.com", private_token=token, ssl_verify=False)
    gl.auth()
    project_path = git_repo_url.replace("https://git.tigeranalytics.com/", "")
    return gl.projects.get(project_path)


def get_gitlab_file_content(project, file_path, branch):
    f = project.files.get(file_path=file_path, ref=branch)
    return base64.b64decode(f.content).decode("utf-8")


def update_gitlab_file(project, file_path, branch, new_content, commit_message):
    f = project.files.get(file_path=file_path, ref=branch)
    f.content = new_content
    f.save(branch=branch, commit_message=commit_message)
    st.write(f"✅ Updated GitLab file: {file_path}")


# ─── Replace invalid XPaths in GitLab ────────────────────────────────────────
def replace_invalid_xpaths(excel_path, git_repo_url=None, git_branch_name=None,
                             git_file_path=None, approved_xpaths=None):
    """
    Replace invalid XPaths in GitLab page files.

    approved_xpaths: optional set/list of old XPath strings approved by user.
                     If None, all invalid rows are replaced.
    """
    df = pd.read_excel(excel_path)
    invalids = df[df['Status'].str.lower() == 'invalid'][['Xpath', 'Alternative Xpath']].dropna()

    replacements = [
        (str(r['Xpath']).strip(), str(r['Alternative Xpath']).strip())
        for _, r in invalids.iterrows()
        if approved_xpaths is None or str(r['Xpath']).strip() in approved_xpaths
    ]

    if not replacements:
        st.info("ℹ️ No approved replacements to apply.")
        return

    token   = os.getenv("GITLAB_ACCESS_TOKEN")
    project = get_gitlab_project(git_repo_url, token) if git_repo_url else None

    def process_gitlab_file(file_path):
        st.write(f"🔄 Processing: {file_path}")
        content = get_gitlab_file_content(project, file_path, git_branch_name)
        updated = False
        for old, new in replacements:
            if old in content:
                content = content.replace(old, new)
                updated = True
        if updated:
            update_gitlab_file(project, file_path, git_branch_name, content,
                               f"Self-healing: auto-replaced XPaths in {file_path}")

    if git_repo_url and git_branch_name and git_file_path:
        files = project.repository_tree(path=git_file_path, ref=git_branch_name, recursive=True)
        for file in files:
            if file["type"] == "blob" and file["path"].endswith(".py"):
                process_gitlab_file(file["path"])
    else:
        st.error("❌ Provide GitLab repo details (URL, branch, path).")


# ─── Generate xpath_details.json from GitLab page files ───────────────────────
def generate_xpath_doc(git_repo_url=None, git_branch_name=None,
                        git_or_file=None, git_page_folder=None):
    output_folder = "generated_xpath_details"
    os.makedirs(output_folder, exist_ok=True)
    json_file_path = os.path.join(output_folder, "xpath_details.json")

    or_dict = ""
    result  = {}

    token   = os.getenv("GITLAB_ACCESS_TOKEN")
    project = get_gitlab_project(git_repo_url, token) if git_repo_url else None

    st.write(f"✅ Scanning GitLab: {git_repo_url}/{git_branch_name}/{git_page_folder}")

    # OR file
    if git_repo_url and git_branch_name and git_or_file:
        content = get_gitlab_file_content(project, git_or_file, git_branch_name)
        if content:
            or_dict = healing_framework_utils.collect_xpath_from_external_file(content)
            json_obj = json.loads(or_dict)
            with open(json_file_path, "w", encoding="utf-8") as f:
                json.dump(json_obj, f, indent=4, ensure_ascii=False)

    # Page files
    if git_repo_url and git_branch_name and git_page_folder:
        files = project.repository_tree(path=git_page_folder, ref=git_branch_name, recursive=True)
        for file in files:
            if file["type"] == "blob" and file["path"].endswith(".py"):
                content = get_gitlab_file_content(project, file["path"], git_branch_name)
                xpath_page_file = healing_framework_utils.collect_xpath_from_page_file(content)
                if not xpath_page_file.strip():
                    continue
                page_name  = os.path.splitext(os.path.basename(file["path"]))[0]
                page_xpath = healing_framework_utils.generate_page_wise_xpath(
                    page_name, xpath_page_file, or_dict)
                result[page_name] = [x.strip() for x in page_xpath.splitlines()]

    output_data = {page: xpaths for page, xpaths in result.items()}
    with open(json_file_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=4, ensure_ascii=False)
    st.write(f"✅ XPath JSON generated: {json_file_path}")
