import os
import xml.etree.ElementTree as ET
from urllib.parse import urlparse
import json
import re  # Added to sanitize rogue markdown loops
import streamlit as st
from openai import AzureOpenAI
from datetime import datetime, timedelta
from azure.identity import DefaultAzureCredential
from azure.mgmt.monitor import MonitorManagementClient
from azure.identity import ClientSecretCredential

# ---------------------------------------------------
# SECURE CREDENTIAL RETRIEVAL FROM STREAMLIT SECRETS
# ---------------------------------------------------
api_key = st.secrets["AZURE_OPENAI_API_KEY"]
azure_endpoint = st.secrets["AZURE_OPENAI_ENDPOINT"]

deployment_name = "qepracticekey"
api_version = "2023-05-15"

# Initialize AzureOpenAI Client
client = AzureOpenAI(
    api_key=api_key,
    azure_endpoint=azure_endpoint,
    api_version=api_version
)


def is_page_loaded(driver):
    return driver.execute_script("return document.readyState")


def get_output_from_ai(final_prompt):
    """
    Queries Azure OpenAI deployment with strict formatting rules and maximized token windows
    to prevent incomplete generation cuts or XML corruption.
    """
    try:
        optimized_prompt = f"""{final_prompt}

        CRITICAL FORMATTING INSTRUCTION:
        Output ONLY the raw valid XML JMX content. Do not wrap the code in markdown code blocks like ```xml ... ```.
        End your response immediately after the closing </jmeterTestPlan> tag. Do not include any explanations, introduction, or conversational filler.
        """

        response = client.chat.completions.create(
            model=deployment_name,
            messages=[
                {
                    "role": "system",
                    "content": "You are a rigid Apache JMeter JMX generator script engine. You answer exclusively in valid, raw JMeter XML code. You never speak or explain."
                },
                {
                    "role": "user",
                    "content": optimized_prompt
                }
            ],
            temperature=0.1,
            max_tokens=8000,
            stop=["</jmeterTestPlan>"]
        )

        ai_output = response.choices[0].message.content
        if not ai_output:
            return None

        ai_output = ai_output.strip()

        # REMOVE markdown wrapping securely if present
        ai_output = re.sub(r"^```xml\s*", "", ai_output, flags=re.IGNORECASE)
        ai_output = re.sub(r"^```\s*", "", ai_output)
        ai_output = re.sub(r"```$", "", ai_output)
        ai_output = ai_output.strip()

        # STRENGTHEN CLOSED TOKEN FALLBACK CHECK
        if "</jmeterTestPlan>" not in ai_output:
            if ai_output.endswith("</hashTree>"):
                ai_output += "\n</jmeterTestPlan>"
            else:
                if not ai_output.endswith(">"):
                    ai_output = ai_output.rsplit('<', 1)[0]
                ai_output += "\n</hashTree>\n</hashTree>\n</jmeterTestPlan>"

        return ai_output.strip()

    except Exception as e:
        print(f"[ERROR] Critical LLM call failed or timed out: {e}")
        return None


def extract_ai_test_config(user_prompt, jmx_content):
    if not user_prompt.strip():
        return {"threads": 1, "rampup": 1, "loops": 1, "duration": 0}

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
    ai_response = ai_response.replace("```json", "").replace("```", "").strip()

    ai_config = json.loads(ai_response)
    return ai_config


def inject_grafana_backend_listener(root):
    """
    Programmatically injects a perfectly formed InfluxDB v1 BackendListener
    into the primary active hashTree layer of the JMeter XML tree.
    """
    for listener in root.iter("BackendListener"):
        if listener.attrib.get("testname") == "TigerQE_Grafana_InfluxDB_Listener":
            return

    target_hash_tree = None
    for child in root:
        if child.tag == "hashTree":
            target_hash_tree = child
            break

    if target_hash_tree is None:
        target_hash_tree = root.find(".//hashTree")

    if target_hash_tree is not None:
        # Default base URL pointing to 10.0.0.4:8086
        influx_base = st.secrets.get("INFLUX_URL", "[http://10.0.0.4:8086](http://10.0.0.4:8086)")
        influx_db = st.secrets.get("INFLUX_DB", "jmeter")
        influx_user = st.secrets.get("INFLUX_USER", "")
        influx_pass = st.secrets.get("INFLUX_PASSWORD", "")

        constructed_url = f"{influx_base}/write?db={influx_db}"

        backend_listener = ET.Element(
            "BackendListener",
            guiclass="BackendListenerGui",
            testclass="BackendListener",
            testname="TigerQE_Grafana_InfluxDB_Listener",
            enabled="true"
        )
        elem_prop = ET.SubElement(backend_listener, "elementProp", name="arguments", elementType="Arguments",
                                  guiclass="ArgumentsPanel", testclass="Arguments", enabled="true")
        coll_prop = ET.SubElement(elem_prop, "collectionProp", name="Arguments.arguments")

        configs = [
            ("influxdbMetricsSender", "org.apache.jmeter.visualizers.backend.influxdb.HttpMetricsSender"),
            ("influxdbUrl", constructed_url),
            ("application", "TigerQE_Automation_Workflow"),
            ("measurement", "jmeter"),
            ("summaryOnly", "false"),
            ("samplersRegex", ".*"),
            ("percentiles", "90;95;99"),
            ("testTitle", f"Execution_Run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"),
            ("user", influx_user),
            ("password", influx_pass),
            ("eventMetrics", "all")
        ]

        for name, value in configs:
            arg = ET.SubElement(coll_prop, "elementProp", name=name, elementType="Argument")
            ET.SubElement(arg, "stringProp", name="Argument.name").text = name
            ET.SubElement(arg, "stringProp", name="Argument.value").text = value
            ET.SubElement(arg, "stringProp", name="Argument.metadata").text = "="

        ET.SubElement(backend_listener, "stringProp", name="classname").text = \
            "org.apache.jmeter.visualizers.backend.influxdb.InfluxdbBackendListenerClient"

        target_hash_tree.append(backend_listener)
        target_hash_tree.append(ET.Element("hashTree"))


def update_jmx_file(jmx_content, config):
    """
    Updates JMeter ThreadGroup values dynamically, enforces hard stop schedules,
    maps global loop properties, injects strict hard timeouts to prevent overruns,
    and automatically strips layout-breaking desktop GUI visualizers and their empty hashTrees.
    """
    print("#### config", config)

    if isinstance(config, list):
        if len(config) > 0:
            config = config[0]
        else:
            config = {}

    root = ET.fromstring(jmx_content)
    elements_to_remove = []

    for parent in root.iter():
        children = list(parent)
        for idx, element in enumerate(children):
            guiclass = element.attrib.get("guiclass", "")
            testclass = element.attrib.get("testclass", "")

            if (
                    element.tag == "ViewResultsFullVisualizer" or
                    "ViewResultsFullVisualizer" in guiclass or
                    "TableVisualizer" in guiclass or
                    testclass == "ViewResultsFullVisualizer"
            ):
                elements_to_remove.append((parent, element))

                if idx + 1 < len(children) and children[idx + 1].tag == "hashTree":
                    elements_to_remove.append((parent, children[idx + 1]))

    removed_count = 0
    for parent, elem in elements_to_remove:
        if elem in parent:
            parent.remove(elem)
            removed_count += 1

    if removed_count > 0:
        print(f"[SANITIZER] Successfully stripped {removed_count} layout-breaking items and matching structural tags.")

    threads = str(config.get("threads", 1))
    rampup = str(config.get("rampup", 1))
    duration_val = int(config.get("duration", 0))
    loops = str(config.get("loops", 1))

    if duration_val == 0 and (loops == "-1" or config.get("duration") is not None):
        duration_val = 180

    is_scheduled_test = duration_val > 0
    if is_scheduled_test:
        loops = "-1"

    duration = str(duration_val)

    for elem in root.iter():
        if elem.attrib.get("name") == "ThreadGroup.num_threads":
            elem.text = threads
        elif elem.attrib.get("name") == "ThreadGroup.ramp_time":
            elem.text = rampup
        elif elem.attrib.get("name") == "ThreadGroup.duration":
            elem.text = duration
        elif elem.attrib.get("name") == "ThreadGroup.scheduler":
            elem.text = "true" if is_scheduled_test else "false"
        elif elem.attrib.get("name") == "LoopController.loops":
            elem.text = loops
        elif elem.attrib.get("name") == "LoopController.continue_forever":
            elem.text = "true" if is_scheduled_test else "false"
        elif elem.attrib.get("name") == "ThreadGroup.on_sample_error":
            elem.text = "continue"

    for sampler in list(root.iter("HTTPSamplerProxy")) + list(root.iter("ConfigTestElement")):
        connect_found = False
        response_found = False

        for prop in sampler.findall("stringProp"):
            if prop.attrib.get("name") == "HTTPSampler.connect_timeout":
                prop.text = "5000"
                connect_found = True
            elif prop.attrib.get("name") == "HTTPSampler.response_timeout":
                prop.text = "5000"
                response_found = True

        if not connect_found:
            c_prop = ET.SubElement(sampler, "stringProp", name="HTTPSampler.connect_timeout")
            c_prop.text = "5000"
        if not response_found:
            r_prop = ET.SubElement(sampler, "stringProp", name="HTTPSampler.response_timeout")
            r_prop.text = "5000"

    inject_grafana_backend_listener(root)

    updated_xml = ET.tostring(root, encoding="utf-8")
    return updated_xml.decode("utf-8")


def validate_jmx(jmx_content):
    try:
        ET.fromstring(jmx_content)
        return True, None
    except Exception as e:
        return False, str(e)


def get_azure_server_metrics(duration_minutes=3):
    try:
        resource_id = (
            "/subscriptions/18bbb40d-2c02-4256-a11a-2aafc355952b"
            "/resourceGroups/quality-engineering-coe"
            "/providers/Microsoft.Web/sites/vsm-api-tiger"
        )

        credential = ClientSecretCredential(
            tenant_id=st.secrets["AZURE_TENANT_ID"],
            client_id=st.secrets["AZURE_CLIENT_ID"],
            client_secret=st.secrets["AZURE_CLIENT_SECRET"]
        )

        sub_id = resource_id.split("/")[2]
        monitor_client = MonitorManagementClient(credential, sub_id)

        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=duration_minutes)
        timespan = f"{start_time.isoformat()}Z/{end_time.isoformat()}Z"

        metrics_response = monitor_client.metrics.list(
            resource_id,
            timespan=timespan,
            interval="PT1M",
            metricnames="CpuTime,AverageMemoryWorkingSet",
            aggregation="Average"
        )
        print("##### metrics response ", metrics_response)
        parsed_metrics = {"cpu_time": 0.0, "memory_mb": 0.0}

        for metric in metrics_response.value:
            points = [p.average for p in metric.timeseries[0].data if p.average is not None]
            avg_val = max(points) if points else 0.0

            print("##### metric name value : ", metric.name.value)
            if metric.name.value == "CpuTime":
                estimated_cpu_pct = (avg_val / 60.0) * 100.0
                parsed_metrics["cpu_time"] = min(100.0, estimated_cpu_pct)

            elif metric.name.value == "AverageMemoryWorkingSet":
                memory_consumed_mb = avg_val / (1024 * 1024)
                estimated_mem_pct = (memory_consumed_mb / 1792.0) * 100.0
                parsed_metrics["memory_mb"] = min(100.0, estimated_mem_pct)

        return parsed_metrics

    except Exception as e:
        print(f"[AZURE MONITOR ERROR] Failed to fetch server metrics: {e}")
        return None


def patch_influx_endpoint(jmx_content, master_ip="10.0.0.4", database_name="jmeter"):
    """
    Locates the InfluxDB BackendListener URL node and forcefully
    overwrites it to point to the user-specified IP address.
    """
    try:
        clean_ip = master_ip.strip() if master_ip and master_ip.strip() else "10.0.0.4"
        root_xml = ET.fromstring(jmx_content)
        for element in root_xml.iter("BackendListener"):
            for prop in element.iter("elementProp"):
                for argument in prop.iter("elementProp"):
                    arg_name = argument.find("stringProp[@name='Argument.name']")
                    arg_val = argument.find("stringProp[@name='Argument.value']")

                    if arg_name is not None and arg_name.text == "influxdbUrl" and arg_val is not None:
                        # Direct parameter assignment with user-provided IP
                        arg_val.text = f"http://{clean_ip}:8086/write?db={database_name}"

        return ET.tostring(root_xml, encoding="utf-8").decode("utf-8")
    except Exception as e:
        print(f"[ERROR] Failed to patch InfluxDB Endpoint matrix: {e}")
        return jmx_content


def get_k6_output_from_ai(final_prompt):
    """Queries Azure OpenAI deployment specifically for Grafana k6 JavaScript scripts."""
    try:
        optimized_prompt = f"""{final_prompt}

        CRITICAL FORMATTING INSTRUCTION:
        Output ONLY valid, runnable k6 JavaScript code. Do NOT wrap the code in markdown blocks like ```javascript or ```.
        Do NOT include explanations or conversational text.
        """

        response = client.chat.completions.create(
            model=deployment_name,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert Grafana k6 performance testing engineer. You generate exclusively valid, runnable JavaScript ES6 k6 test scripts. You never speak, explain, or output XML."
                },
                {
                    "role": "user",
                    "content": optimized_prompt
                }
            ],
            temperature=0.1,
            max_tokens=4000
        )

        ai_output = response.choices[0].message.content
        if not ai_output:
            return None

        ai_output = ai_output.strip()

        # Remove markdown code blocks if present
        ai_output = re.sub(r"^```javascript\s*", "", ai_output, flags=re.IGNORECASE)
        ai_output = re.sub(r"^```js\s*", "", ai_output, flags=re.IGNORECASE)
        ai_output = re.sub(r"^```\s*", "", ai_output)
        ai_output = re.sub(r"```$", "", ai_output)

        return ai_output.strip()

    except Exception as e:
        print(f"[ERROR] k6 LLM call failed: {e}")
        return None