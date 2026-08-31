import os
import json
import pandas as pd
import base64
import shutil
import Utils.self_healing_framework_utilities as healing_framework_utils
import gitlab
from dotenv import load_dotenv
load_dotenv()
# ---------------------------
# GitLab helper
# ---------------------------
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
    print(f"✅ Updated GitLab file: {file_path}")

# ---------------------------
# Update invalid XPaths
# ---------------------------
def replace_invalid_xpaths(
    excel_path,
    target_file=None,
    page_folder=None,
    git_repo_url=None,
    git_branch_name=None,
    git_file_path=None
):
    df = pd.read_excel(excel_path)
    invalids = df[df['Status'].str.lower() == 'invalid'][['Xpath', 'Alternative Xpath']].dropna()
    replacements = [(str(r['Xpath']).strip(), str(r['Alternative Xpath']).strip()) for _, r in invalids.iterrows()]

    if not replacements:
        print("ℹ️ No invalid XPaths found in Excel.")
        return

    token = os.getenv("GITLAB_ACCESS_TOKEN")
    project = get_gitlab_project(git_repo_url, token) if git_repo_url else None

    # ---------------------------
    # Local file processing
    # ---------------------------
    def process_local_file(file_path):
        ext = os.path.splitext(file_path)[1].lower()
        if ext not in [".py", ".txt", ".properties", ".java", ".xlsx"]:
            return
        updated = False
        if ext == ".xlsx":
            tdf = pd.read_excel(file_path)
            for old, new in replacements:
                if tdf.isin([old]).any().any():
                    tdf = tdf.replace(old, new)
                    updated = True
            if updated:
                tdf.to_excel(file_path, index=False)
        else:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            for old, new in replacements:
                if old in content:
                    content = content.replace(old, new)
                    updated = True
            if updated:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
        if updated:
            print(f"✅ Updated local file: {file_path}")

    # ---------------------------
    # GitLab file processing
    # ---------------------------
    def process_gitlab_file(file_path):
        content = get_gitlab_file_content(project, file_path, git_branch_name)
        updated = False
        for old, new in replacements:
            if old in content:
                content = content.replace(old, new)
                updated = True
        if updated:
            update_gitlab_file(project, file_path, git_branch_name, content, f"Auto-replaced XPaths in {file_path}")

    # ---------------------------
    # Execution routing
    # ---------------------------
    if target_file and os.path.exists(target_file):
        process_local_file(target_file)
    elif page_folder and os.path.exists(page_folder):
        for root, _, files in os.walk(page_folder):
            for file in files:
                if file.endswith((".py", ".txt", ".properties", ".java", ".xlsx")):
                    process_local_file(os.path.join(root, file))
    elif git_repo_url and git_branch_name and git_file_path:
        # list files in git_file_path folder
        files = project.repository_tree(path=git_file_path, ref=git_branch_name, recursive=True)
        for file in files:
            if file["type"] == "blob" and file["path"].endswith(".py"):  # only files
                process_gitlab_file(file["path"])
    else:
        print("❌ Provide either local file/folder OR GitLab repo details.")

# ---------------------------
# Generate xpath_details.json
# ---------------------------
def generate_xpath_doc(
    xpath_file_path=None,
    page_folder_path=None,
    git_repo_url=None,
    git_branch_name=None,
    git_or_file=None,
    git_page_folder=None
):
    output_folder = "generated_xpath_details"
    os.makedirs(output_folder, exist_ok=True)
    json_file_path = os.path.join(output_folder, "xpath_details.json")

    or_dict = ""
    result = {}
    no_page_details = []

    token = os.getenv("GITLAB_ACCESS_TOKEN")
    project = get_gitlab_project(git_repo_url, token) if git_repo_url else None

    # ---------------------------
    # OR file
    # ---------------------------
    if git_repo_url and git_branch_name and git_or_file:
        xpath_file_path = git_or_file
        content = get_gitlab_file_content(project, git_or_file, git_branch_name)
    elif xpath_file_path and os.path.exists(xpath_file_path):
        with open(xpath_file_path, "r", encoding="utf-8") as f:
            content = f.read()
    else:
        content = None

    if content:
        or_dict = healing_framework_utils.collect_xpath_from_external_file(content)
        json_obj = json.loads(or_dict)
        with open(json_file_path, "w", encoding="utf-8") as f:
            json.dump(json_obj, f, indent=4, ensure_ascii=False)
        print(f"✅ XPath JSON created from OR file: {json_file_path}")

    # ---------------------------
    # Page folder
    # ---------------------------
    if git_repo_url and git_branch_name and git_page_folder:
        files = project.repository_tree(path=git_page_folder, ref=git_branch_name, recursive=True)
        for file in files:
            if file["type"] == "blob" and file["path"].endswith(".py"):
                content = get_gitlab_file_content(project, file["path"], git_branch_name)
                xpath_page_file = healing_framework_utils.collect_xpath_from_page_file(content)
                if not xpath_page_file.strip():
                    continue
                page_name = os.path.splitext(os.path.basename(file["path"]))[0]
                page_xpath = healing_framework_utils.generate_page_wise_xpath(page_name, xpath_page_file, or_dict)
                result[page_name] = page_xpath.splitlines()
    elif page_folder_path and os.path.exists(page_folder_path):
        for filename in os.listdir(page_folder_path):
            if filename.endswith(".py"):
                full_path = os.path.join(page_folder_path, filename)
                with open(full_path, "r", encoding="utf-8") as f:
                    content = f.read()
                xpath_page_file = healing_framework_utils.collect_xpath_from_page_file(content)
                if not xpath_page_file.strip():
                    continue
                page_name = os.path.splitext(filename)[0]
                page_xpath = healing_framework_utils.generate_page_wise_xpath(page_name, xpath_page_file, or_dict)
                print(page_xpath)
                # page_lines = [line.strip() for line in page_xpath.splitlines() if line.strip()]

                # # If AI returns "no_page:", add these XPaths under "No Page Details"
                # if page_lines and "no_page:" in page_lines[0]:
                #     page_lines = page_lines[1:]  # remove the label but keep XPaths
                #     if "No Page Details" not in result:
                #         result["No Page Details"] = []
                #     result["No Page Details"].extend(page_lines)
                # else:
                #     result[page_name] = page_lines


                result[page_name] = page_xpath.splitlines()
                print(result)
    # ---------------------------
    # Write final JSON
    # ---------------------------
    output_data = {page: [xp.strip() for xp in xps] for page, xps in result.items()}
    if no_page_details:
        output_data["No Page Details"] = [xp.strip() for xp in no_page_details]
    with open(json_file_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=4, ensure_ascii=False)
    print(f"✅ Final XPath JSON generated: {json_file_path}")
