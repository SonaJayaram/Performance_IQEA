import configparser
import os
from configparser import RawConfigParser

config = RawConfigParser()
config_path = os.path.join(os.path.dirname(__file__), 'framework.ini')
config.read(config_path)

def framework_source():
    xpath_file_path = config.get('GENERAL', 'xpath_file_path')
    page_folder_path = config.get('GENERAL', 'page_folder_path')
    workflow_doc_path = config.get('GENERAL', 'workflow_doc_path')
    feature_file_path = config.get('GENERAL', 'feature_file_path')
    return xpath_file_path, page_folder_path, workflow_doc_path, feature_file_path

def git_details():
    git_file_path = config.get('GENERAL', 'git_file_path')
    git_repo_name = config.get('GENERAL', 'git_repo_name')
    git_branch_name = config.get('GENERAL', 'git_branch_name')
    return git_file_path, git_repo_name, git_branch_name

def get_source():
    source_type = config.get('Source', 'source_type').split('#')[0].strip()
    return source_type
