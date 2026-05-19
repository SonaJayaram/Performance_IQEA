with st.expander("⚙️ Source Code 📡 Automation Bridge"):
    pytest_files = utils.select_and_read_text_files_xpath("pom_file", utils.Test_file_generator)
    pom_files = utils.select_and_read_text_files_xpath("test_file", utils.Page_file_generator)
    repo_pom_name = st.text_input("Enter folder name in repo:", value="test_web/src/pom/pages")
    repo_pytest_name = st.text_input("Enter folder name in repo:", value="test_web/tests/test_cases")

    if st.button("Push to Repo"):

        token = os.getenv("GITLAB_ACCESS_TOKEN")

        if token:
            try:
                g = Gitlab("https://git.tigeranalytics.com/", private_token=token, ssl_verify=False)
                g.auth()
                print("✅ Authentication successful!")
            except Exception as e:
                print("❌ Auth failed:", e)
        else:
            print("❌ Token not found in environment.")
        repo = g.projects.get(os.getenv("GITLAB_REPO_NAME"))
        print(repo)
        branch = os.getenv("GITLAB_BRANCH_NAME", "main")

        if repo_pom_name and repo_pytest_name:
            if source == "file":
                # Push all POM files
                for file_name, content in pom_files.items():
                    pom_dest_path = f"{repo_pom_name.strip('/')}/{file_name}"
                    utils.push_file_to_gitlab(pom_dest_path, content, repo, branch)

                # Push all pytest files
                for file_name, content in pytest_files.items():
                    pytest_dest_path = f"{repo_pytest_name.strip('/')}/{file_name}"
                    utils.push_file_to_gitlab(pytest_dest_path, content, repo, branch)

                # Push all selected test files
                if temp_dir_test and os.path.isdir(temp_dir_test):
                    for file_name in os.listdir(temp_dir_test):
                        file_path = os.path.join(temp_dir_test, file_name)
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()
                        pytest_dest_path = f"{repo_pytest_name.strip('/')}/{file_name}"
                        utils.push_file_to_gitlab(pytest_dest_path, content, repo, branch)

                # Clean up the temp directories
                shutil.rmtree(temp_dir_page, ignore_errors=True)
                shutil.rmtree(temp_dir_test, ignore_errors=True)

                st.success("✅ Selected database files pushed to GitHub and temp files deleted.")
        else:
            st.warning("⚠️ Please enter both folder names in the repo.")