from session import DesktopSession
from recorder import DesktopRecorder
from script_generator import  *
import utilities.Utilities_Xpath as utils
import subprocess
prompt_data_path=os.getcwd()
def load_prompt_from_file(prompt_type):
    print("********************source**********")

    prompt_file = ""

    if prompt_type == "script_prompt":
        prompt_file = os.path.join(prompt_data_path, "script_prompt.txt")

    if not os.path.exists(prompt_file):
        raise FileNotFoundError(f"Prompt file not found at: {prompt_file}")

    with open(prompt_file, "r", encoding="utf-8") as file:
        prompt_template = file.read()
    print("-------------file- prompttemplate--------------")
    return prompt_template
# Start Notepad
session = DesktopSession("notepad.exe")
app = session.start()

# Start recorder
recorder = DesktopRecorder()
recorder.start_recording()

input("Press Enter to stop recording...")

recorder.stop_recording()
recorder.save_file("recorded_actions.txt")
load_prompt_for_llm = load_prompt_from_file("script_prompt")
print("-------------file- prompttemplate--------------",load_prompt_for_llm)
task="notepad"
full_path=os.path.join(prompt_data_path, "recorded_actions.txt")
file_name="recorded_actions.txt"
file_contents = {}
with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
    file_contents[file_name] = f.read()
final_prompt = load_prompt_for_llm.format(application_name=task,recorded_actions=file_contents)
print(final_prompt)
response_script=utils.get_queries_from_ai_updated(final_prompt)
print(response_script)
utils.create_test_file(prompt_data_path,"execute_script","python",response_script)
SCRIPT_PATH_execution=os.path.join(prompt_data_path, "execute_script.py")
subprocess.run(['python', SCRIPT_PATH_execution], check=True)