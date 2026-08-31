import openai
import os
from dotenv import load_dotenv

load_dotenv()
# api_key = os.getenv("AZURE_OPENAI_API_KEY")
# endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
# connect_string=os.getenv("AZURE_QUEUE_CONN_STRING")
os.environ["OPENAI_API_KEY"] = os.getenv("AZURE_OPENAI_API_KEY")
os.environ["OPENAI_API_BASE"] = os.getenv("AZURE_OPENAI_ENDPOINT")
print(os.environ["OPENAI_API_KEY"] )
print(os.environ["OPENAI_API_BASE"])
client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"],
                       base_url=os.environ["OPENAI_API_BASE"])

def get_queries_from_ai_updated(formatted_summary):
   print("going inside get_queries_from_ai_updated")
   model = "gpt-5-mini"
   try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": formatted_summary}],
            max_completion_tokens=25000,
            timeout=600
        )
        print(response)
        return response.choices[0].message.content
   except Exception as e:
        print(f"[ERROR] LLM call failed: {e}")
        return None
formatted_summary="""YOU ARE A SENIOR SDET. FROM ONE RECORDED USER SESSION, GENERATE A COMPLETE PYTEST AUTOMATION SCRIPT COVERING MULTIPLE TEST SCENARIOS.

=== TARGET LANGUAGE / FRAMEWORK ===
Python-Selenium

=== RECORDED USER ACTIONS ===
Each step includes exact element metadata captured at recording time.
Fields: Locator (ready-to-use Selenium locator), tag, inputType, NAV_LINK href, URL.
Step 1: [CLICK] | Element: user-name | Locator: By.ID='user-name' | tag=input | inputType=text | URL: https://www.saucedemo.com/
Step 2: [SKIP_KEY_TAB] (keyboard nav — not needed in automation)
Step 3: [TYPE 'standard_user'] |
going inside get_queries_from_ai_updated
[ERROR] LLM call failed: Error code: 404 - {'error': {'code': '404', 'message': 'Resource not found'}}
xpath_allowed_tags ['input', 'button', 'a', 'select', 'textarea', 'div', 'span', 'i', 'li', 'All', 'p']
********************source**********
file
-------------file- prompttemplate--------------
***** Record & Playback — multi-scenario prompt *****
YOU ARE A SENIOR SDET. FROM ONE RECORDED USER SESSION, GENERATE A COMPLETE PYTEST AUTOMATION SCRIPT COVERING MULTIPLE TEST SCENARIOS.

=== TARGET LANGUAGE / FRAMEWORK ===
Python-Selenium

=== RECORDED USER ACTIONS ===
Each step includes exact element metadata captured at recording time.
Fields: Locator (ready-to-use Selenium locator), tag, inputType, NAV_LINK href, URL.
Step 1: [CLICK] | Element: user-name | Locator: By.ID='user-name' | tag=input | inputType=text | URL: https://www.saucedemo.com/
Step 2: [SKIP_KEY_TAB] (keyboard nav — not needed in automation)
Step 3: [TYPE 'standard_user'] |
going inside get_queries_from_ai_updated
[ERROR] LLM call failed: Error code: 404 - {'error': {'code': '404', 'message': 'Resource not found'}}
xpath_allowed_tags ['input', 'button', 'a', 'select', 'textarea', 'div', 'span', 'i', 'li', 'All', 'p']
********************source**********
file
-------------file- prompttemplate--------------
***** Record & Playback — multi-scenario prompt *****
YOU ARE A SENIOR SDET. FROM ONE RECORDED USER SESSION, GENERATE A COMPLETE PYTEST AUTOMATION SCRIPT COVERING MULTIPLE TEST SCENARIOS.

=== TARGET LANGUAGE / FRAMEWORK ===
Python-Selenium

=== RECORDED USER ACTIONS ===
Each step includes exact element metadata captured at recording time.
Fields: Locator (ready-to-use Selenium locator), tag, inputType, NAV_LINK href, URL.
Step 1: [CLICK] | Element: user-name | Locator: By.ID='user-name' | tag=input | inputType=text | URL: https://www.saucedemo.com/
Step 2: [SKIP_KEY_TAB] (keyboard nav — not needed in automation)
Step 3: [TYPE 'standard_user'] |
going inside get_queries_from_ai_updated
[ERROR] LLM call failed: Error code: 404 - {'error': {'code': '404', 'message': 'Resource not found'}}
xpath_allowed_tags ['input', 'button', 'a', 'select', 'textarea', 'div', 'span', 'i', 'li', 'All', 'p']
********************source**********
file
-------------file- prompttemplate--------------
***** Record & Playback — multi-scenario prompt *****
YOU ARE A SENIOR SDET. FROM ONE RECORDED USER SESSION, GENERATE A COMPLETE PYTEST AUTOMATION SCRIPT COVERING MULTIPLE TEST SCENARIOS.

=== TARGET LANGUAGE / FRAMEWORK ===
Python-Selenium

=== RECORDED USER ACTIONS ===
Each step includes exact element metadata captured at recording time.
Fields: Locator (ready-to-use Selenium locator), tag, inputType, NAV_LINK href, URL.
Step 1: [CLICK] | Element: user-name | Locator: By.ID='user-name' | tag=input | inputType=text | URL: https://www.saucedemo.com/
Step 2: [SKIP_KEY_TAB] (keyboard nav — not needed in automation)
Step 3: [TYPE 'standard_user'] |"""
get_queries_from_ai_updated(formatted_summary)