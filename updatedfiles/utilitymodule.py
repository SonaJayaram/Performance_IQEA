from openai import AzureOpenAI
import xml.etree.ElementTree as ET
import json

api_key = "4fed2bedb59744a99b0424622f6d9d1b"
azure_endpoint = "https://qepracticekey.openai.azure.com/"
deployment_name = "qepracticekey"
api_version = "2023-05-15"

client = AzureOpenAI(
    api_key=api_key,
    azure_endpoint=azure_endpoint,
    api_version=api_version
)


def is_page_loaded(driver):
    return driver.execute_script("return document.readyState")


def get_output_from_ai(final_prompt):

    try:

        response = client.chat.completions.create(
            model=deployment_name,
            messages=[
                {
                    "role": "user",
                    "content": final_prompt
                }
            ],
            temperature=0.2
        )

        # Extract actual content
        ai_output = response.choices[0].message.content
        # Remove markdown code blocks if present
        ai_output = ai_output.replace("```xml", "")
        ai_output = ai_output.replace("```", "")

        # Trim spaces/new lines
        ai_output = ai_output.strip()

        # print("######## AI OUTPUT ########")
        # print(ai_output)

        # IMPORTANT
        return ai_output

    except Exception as e:

        print(f"[ERROR] LLM call failed: {e}")

        return None


def extract_ai_test_config(user_prompt, jmx_content):
    system_prompt = f"""
        You are a JMeter performance testing expert.
        
        Analyze the user instruction and return ONLY JSON.
        
        Required JSON format:
        {{
            "threads": int,
            "rampup": int,
            "loops": int,
            "duration": int
        }}
        
        Rules:
        - threads = concurrent users
        - rampup = seconds
        - loops = loop count
        - duration = scheduler duration in seconds
        - Return valid JSON only
        - No explanation
        - No markdown
        
        User Instruction:
        {user_prompt}
        """

    # ========================================================
    # PLACEHOLDER RESPONSE
    # ========================================================

    response = client.chat.completions.create(
        model=deployment_name,
        messages=[
            {
                "role": "system",
                "content": system_prompt
            }
        ],
        temperature=0
    )

    ai_response = response.choices[0].message.content.strip()

    # Convert AI JSON string → Python dict
    ai_config = json.loads(ai_response)

    return ai_config

def update_jmx_file(jmx_content, config):
    """
    Updates JMeter ThreadGroup values dynamically.
    """

    root = ET.fromstring(jmx_content)

    threads = str(config.get("threads", 1))
    rampup = str(config.get("rampup", 1))
    loops = str(config.get("loops", 1))
    duration = str(config.get("duration", 60))

    # ========================================================
    # Update Thread Group Properties
    # ========================================================

    for elem in root.iter():

        # Number of Threads
        if (
            elem.tag == "stringProp"
            and elem.attrib.get("name") == "ThreadGroup.num_threads"
        ):
            elem.text = threads

        # Ramp-Up Period
        elif (
            elem.tag == "stringProp"
            and elem.attrib.get("name") == "ThreadGroup.ramp_time"
        ):
            elem.text = rampup

        # Scheduler Duration
        elif (
            elem.tag == "stringProp"
            and elem.attrib.get("name") == "ThreadGroup.duration"
        ):
            elem.text = duration

        # Enable Scheduler
        elif (
            elem.tag == "boolProp"
            and elem.attrib.get("name") == "ThreadGroup.scheduler"
        ):
            elem.text = "true"

        # Loop Controller
        elif (
            elem.tag == "stringProp"
            and elem.attrib.get("name") == "LoopController.loops"
        ):
            elem.text = loops

    updated_xml = ET.tostring(
        root,
        encoding="utf-8"
    )

    return updated_xml.decode("utf-8")


def validate_jmx(jmx_content):
    """
    Validates generated XML.
    """

    try:
        ET.fromstring(jmx_content)
        return True, None

    except Exception as e:
        return False, str(e)
