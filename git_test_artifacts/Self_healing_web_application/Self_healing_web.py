import os
import re
import docx2txt
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import HumanMessage
from src.mcp_use_client import *
import json
import asyncio
import os
import subprocess
import difflib
import pandas as pd
import os
from src.mcp_use_client import start_mcp_client, execute_mcp_use, close_mcp_client
import Utils.Self_healing_utilities as healing_utils
import Utils.self_healing_framework_utilities as healing_framework_utils
from config.config_reader import framework_source

### capture xpath from framework####
xpath_file_path,page_folder_path,workflow_doc_path,feature_file_path=framework_source()
# #========== 🔽 EXECUTION ==========##
# healing_framework_utils.generate_xpath_doc(xpath_file_path, page_folder_path)
# workflow_content = healing_framework_utils.read_workflow_document(workflow_doc_path)
# # Generate feature file from workflow (whole flow as one)
# feature_content = healing_framework_utils.workflow_feature_file(workflow_content)
# healing_framework_utils.write_feature_file("full_workflow", feature_content)


# #####MCP - Rweady feature , generate JS file
# asyncio.run(healing_utils.main())
# ##### Subprocess to run genearted JS file to get DOM#############
# subprocess.run(['node', healing_utils.SCRIPT_PATH_execution], check=True)
# print(f"✅ Page wise dom file generated. Output saved to: {healing_utils.dom_file_path}")
# #### Process Xpath details and page wise dom and validate the xpath #######
xpath_file_path =r"D:\Self_healing_web_application\generated_xpath_details\xpath_details.json"
dom_file_path =r"D:\Self_healing_web_application\output\sauce_demo\output\sauce_demo\all_page_dom_details.json"
with open(xpath_file_path, 'r', encoding='utf-8') as f:
    xpath_content = f.read()

xpath_content_all=healing_utils.read_json_file(healing_utils.xpath_file_path)
dom_content_all=healing_utils.read_json_file(healing_utils.dom_file_path)
xpath_content_dict = healing_utils.normalize_content(xpath_content_all, details_key="xpath_details")
dom_content_dict = healing_utils.normalize_content(dom_content_all, details_key="dom_details")

print("DEBUG - XPATH dict keys:", xpath_content_dict.keys())
print("DEBUG - DOM dict keys:", dom_content_dict.keys())
#page_mapping = match_xpath_and_dom(xpath_content_all, dom_content_all)
response =[]
for xpath_page, xpath_details in xpath_content_dict.items():
    found_match = False
    for dom_page, dom_details in dom_content_dict.items():
    # Partial match check
        if healing_utils.has_partial_word_match(xpath_page, dom_page):
            response.append(healing_utils.compare_xpathdetails_dom(xpath_details, dom_details))
            found_match = True
            break   # stop once match is found

    if not found_match:
        print(f"No DOM match found for {xpath_page}")

# for page_name, details in page_mapping.items():
#     xpath_details = details["xpath_details"]
#     dom_details_list = details["dom_details_list"]

#     if dom_details_list:
#         for dom_details in dom_details_list:
#             response.append(compare_xpathdetails_dom(xpath_details, dom_details))
#     else:
#         print(f"No DOM match found for {page_name}")

print(response)
#### Saving response into excel######
healing_utils.save_ai_response_to_excel(response)
##### updatre the Alternative xpath in source file #####
#excel_path=r"D:\Self_healing_web_application\output\validated_xpath\validated_xpath.xlsx"
# excel_path=os.path.join(healing_utils.output_xpath_validate, "validated_xpath.xlsx")
# page_folder=page_folder_path
# healing_utils.replace_invalid_xpaths(excel_path, target_file=None,page_folder=page_folder)
    