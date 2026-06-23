# workspace folder paths
code_path = "src/"
inputs_path = "inputs/"
results_path = "results/"
logo_path = "src/tiger_analytics_nobg.png"

# important labels and constants
logo_title = "Quality Engineering - Agentic AI for Autonomous Testing"
chat_exe_keyword = "begin"

# workspace file locations
browser_cookies_file = "cookies.json"
temporary_task = inputs_path + "browser_use_task.txt"
summary_prompt = inputs_path + "summarize_prompt.txt"
testcases_prompt = inputs_path + "testcase_gen_prompt.txt"
tc_from_image_prompt = inputs_path + "testcase_imagen_prompt.txt"
tc_to_feature_prompt = inputs_path + "testcase_feature_prompt.txt"
execution_prompt = inputs_path + "mcp_execute_prompt.txt"
report_gen_prompt = inputs_path + "mcp_report_prompt.txt"
each_scenario_prompt = inputs_path + "mcp_scenario_prompt.txt"

# results file locations
step0_path = results_path + "0_requirements/"
step1_path = results_path + "1_testcases/"
step2_path = results_path + "2_execution/"
step3_path = results_path + "3_reporting/"
testcases_generated_file = "ai_testcases.xlsx"
testcase_feature_file = "ai_scenarios.feature"
execution_report_file = "ai_report.html"
info_log_file = step2_path + "mcp_use_info.log"
debug_log_file = step2_path + "mcp_use_debug.log"

# load constants
allowed_extensions = ['pdf', 'docx', 'xlsx', 'jpg', 'jpeg', 'png']

# server configuration
MCP_SERVER_PORT = 8931
MCP_SERVER_URL = f"http://localhost:{MCP_SERVER_PORT}"
MCP_AGENT_ID = "playwright-bdd-agent"