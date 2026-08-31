import subprocess
from github import Github, GithubException  # Make sure GithubException is imported
from gitlab import Gitlab
import pandas as pd
import re
from github import Github
from pyasn1_modules.rfc8017 import emptyString
from selenium.webdriver.chrome.service import Service
import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.wait import WebDriverWait
import os
import json
import shutil
import threading
import time
from datetime import datetime
import utilities.Utilities_Xpath as utils
import utilities.utils_action as action_utils
import utilities.db_utils.handler as db_handler
import utilities.TMT_Connection.Test_management_tool_utils as tmt_utils
import utilitymodule  # Required for Performance / JMeter / k6 operations
import xml.etree.ElementTree as ET
import stat
from PIL import Image
import pytesseract
import io
import base64
from langchain_core.messages import HumanMessage
from langchain_openai import AzureChatOpenAI
from dotenv import load_dotenv;
import jmx_parser_engine as jmx_engine

load_dotenv()
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from fpdf import FPDF

# setting details - source either file or database
from config.settings_reader import get_source, get_update_user, get_model, get_xpath_key
from desktop.session import *
from desktop.recorder import *

source = get_source()
model_type = get_model()
xpath_tag_keys = get_xpath_key()


AUTH_TOKEN = st.session_state.get("AUTH_TOKEN", "default_or_fallback_token")
AUTH_TOKEN = os.getenv("AUTH_TOKEN", "")
# ── AZURE OPENAI DEPLOYMENT MAPPINGS ──────────
AZURE_KEYS = [
    "AZURE_TENANT_ID", "AZURE_CLIENT_ID", "AZURE_CLIENT_SECRET",
    "AZURE_OPENAI_API_KEY", "AZURE_OPENAI_ENDPOINT",
    "AZURE_OPENAI_DEPLOYMENT_NAME", "OPENAI_API_VERSION", "AZURE_OPENAI_API_VERSION"
]
for key in AZURE_KEYS:
    if key in st.secrets:
        os.environ[key] = str(st.secrets[key])

if "AZURE_OPENAI_DEPLOYMENT_NAME" not in os.environ:
    os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"] = "qepracticekey"

if "OPENAI_API_VERSION" not in os.environ:
    os.environ["OPENAI_API_VERSION"] = "2023-05-15"

# Setup output folder
current_path = os.getcwd()
input_folder = os.path.join(current_path, "Input")
output_folder = os.path.join(current_path, "output")
Action_collection = os.path.join(output_folder, "Action_collection")
Action_collection_desktop = os.path.join(Action_collection, "Action_collection_desktop")
Page_collection = os.path.join(output_folder, "page_file_generator")
Test_case_collection = os.path.join(output_folder, "Test_Cases_collection")
Test_file_generator = os.path.join(output_folder, "test_file_generator")
feature_file_collection = os.path.join(output_folder, "Feature_file_generator")
test_data_folder = os.path.join(output_folder, "Test_data_generator")
api_template_file = os.path.join(input_folder, "Api_template.xlsx")
GIT_WORKSPACE = os.path.join(current_path, "git_test_artifacts")
JMX_FOLDER = os.path.join(current_path, "generated_jmx_files")
K6_FOLDER = os.path.join(current_path, "generated_k6_files")

os.makedirs(Page_collection, exist_ok=True)
os.makedirs(Test_case_collection, exist_ok=True)
os.makedirs(Action_collection, exist_ok=True)
os.makedirs(feature_file_collection, exist_ok=True)
os.makedirs(test_data_folder, exist_ok=True)
os.makedirs(Action_collection_desktop, exist_ok=True)
os.makedirs(GIT_WORKSPACE, exist_ok=True)
os.makedirs(JMX_FOLDER, exist_ok=True)
os.makedirs(K6_FOLDER, exist_ok=True)

page_screenshot_folder = os.path.join(Action_collection, "Sauce_demo")
os.makedirs(page_screenshot_folder, exist_ok=True)
os.makedirs(Test_file_generator, exist_ok=True)

#-------------------------------------------------
#FUNCTION TO RECORD AN DOWNLOAD HAR FILE FOR PERFORMANCE TEST SCRIPT GENERATION
#--------------------------------------------------
def extract_xhr_network_logs(driver, max_payload_len=300):
    """Filter non-GET API calls and limit payload token usage."""
    xhr_summary = []
    try:
        logs = driver.get_log("performance")
        for entry in logs:
            message = json.loads(entry["message"])["message"]
            if message.get("method") == "Network.requestWillBeSent":
                params = message.get("params", {})
                request = params.get("request", {})
                req_method = request.get("method", "GET")
                url = request.get("url", "")

                # Ignore static assets and telemetry noise
                if any(ext in url for ext in
                       [".png", ".jpg", ".css", ".js", ".svg", ".woff", "datadoghq", "analytics"]):
                    continue

                # Focus strictly on state-changing API endpoints
                if req_method in ["POST", "PUT", "DELETE", "PATCH"]:
                    post_data = str(request.get("postData", ""))
                    # Truncate large payloads to stay within token limits
                    if len(post_data) > max_payload_len:
                        post_data = post_data[:max_payload_len] + "... [truncated]"

                    xhr_summary.append(
                        f"API Endpoint: {req_method} {url}\n"
                        f"Payload: {post_data}\n"
                    )
    except Exception as e:
        print(f"Log parsing error: {e}")

    # Keep only unique requests to prevent redundant tokens
    unique_logs = list(dict.fromkeys(xhr_summary))
    return "\n".join(unique_logs[:5])  # Cap at top 5 critical API calls


def extract_clean_api_network_logs(driver):
    """
    Intercepts Chrome performance logs and filters out RUM, Analytics,
    and third-party telemetry to expose ONLY business API endpoints.
    """
    clean_calls = []
    ignored_domains = [
        "datadoghq.com", "amplitude.com", "microsoftonline.com",
        "cloudflareinsights.com", "azure.windows.net", "google.com"
    ]
    ignored_extensions = [".png", ".jpg", ".css", ".js", ".svg", ".woff", ".ico"]

    try:
        logs = driver.get_log("performance")
        for entry in logs:
            try:
                msg_data = json.loads(entry["message"])["message"]
                if msg_data.get("method") == "Network.requestWillBeSent":
                    req = msg_data.get("params", {}).get("request", {})
                    url = req.get("url", "")
                    method = req.get("method", "GET")

                    # Skip static assets and third-party tracking noise
                    if any(ext in url.lower() for ext in ignored_extensions):
                        continue
                    if any(domain in url.lower() for domain in ignored_domains):
                        continue

                    headers = req.get("headers", {})
                    content_type = headers.get("Content-Type", headers.get("content-type", "application/json"))
                    post_data = req.get("postData", "No Payload")

                    # Record business API endpoints (XHR/AJAX)
                    if "/ajax/" in url or method in ["POST", "PUT", "DELETE", "PATCH"]:
                        clean_calls.append(
                            f"ENDPOINT: {method} {url}\n"
                            f"Header Content-Type: {content_type}\n"
                            f"Body Payload: {post_data}\n"
                        )
            except Exception:
                continue
    except Exception as e:
        print(f"Network Extraction Error: {e}")

    # Remove duplicates while maintaining chronological order
    unique_calls = list(dict.fromkeys(clean_calls))
    return "\n---\n".join(unique_calls)

# -------------------------------------------
# HELPER: EXECUTIVE PDF GENERATOR
# -------------------------------------------
def generate_executive_pdf(report_path, go_status, total_samples, total_err_pct, global_avg_load, global_p90_load,
                           global_tps, runtime_threads, runtime_rampup, runtime_duration, slowest_page, slowest_time,
                           jmx_page_metrics):
    """Generates a professional Executive PDF Report using fpdf2 with safe margins & widths."""
    try:
        pdf = FPDF()
        pdf.set_margins(15, 15, 15)
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)

        # Header Banner
        pdf.set_fill_color(0, 120, 212)
        pdf.rect(0, 0, 210, 25, 'F')

        pdf.set_font("Helvetica", "B", 16)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(0, 8, "TigerQE Performance Test Executive Report", new_x="LMARGIN", new_y="NEXT", align="L")
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 6, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", new_x="LMARGIN", new_y="NEXT",
                 align="L")

        pdf.ln(10)

        # Executive Status
        pdf.set_font("Helvetica", "B", 14)
        pdf.set_text_color(0, 120, 212)
        pdf.cell(90, 10, "1. Executive Pass/Fail Decision", new_x="RIGHT", new_y="TOP")

        if go_status == "GO":
            pdf.set_fill_color(212, 237, 218)
            pdf.set_text_color(21, 87, 36)
            status_text = "STATUS: GO (SLA PASSED)"
        else:
            pdf.set_fill_color(248, 215, 218)
            pdf.set_text_color(114, 28, 36)
            status_text = "STATUS: NO GO (SLA FAILED)"

        pdf.cell(90, 10, status_text, new_x="LMARGIN", new_y="NEXT", align="C", fill=True)
        pdf.ln(5)

        # Run Configuration
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(50, 50, 50)
        pdf.cell(0, 8, "2. Execution Workload Parameters", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 10)

        pdf.cell(45, 8, f"Virtual Users: {runtime_threads}", border=1, align="C")
        pdf.cell(45, 8, f"Ramp-up: {runtime_rampup}s", border=1, align="C")
        pdf.cell(45, 8, f"Duration: {runtime_duration}s", border=1, align="C")
        pdf.cell(45, 8, f"Total Samples: {total_samples}", border=1, align="C", new_x="LMARGIN", new_y="NEXT")

        pdf.ln(6)

        # Performance KPIs
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "3. Core Performance Metric Summary", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 10)

        pdf.cell(45, 8, f"Avg Latency: {global_avg_load:.2f} ms", border=1, align="C")
        pdf.cell(45, 8, f"P90 Latency: {global_p90_load:.2f} ms", border=1, align="C")
        pdf.cell(45, 8, f"Throughput: {global_tps:.2f} TPS", border=1, align="C")
        pdf.cell(45, 8, f"Error Rate: {total_err_pct:.2f}%", border=1, align="C", new_x="LMARGIN", new_y="NEXT")

        pdf.ln(6)

        # Highlights & Slowest Endpoint
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "4. Infrastructure Bottleneck Highlights", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(0, 6,
                       f"* Slowest Execution Pipeline: '{slowest_page}' registered the highest response footprint, averaging {slowest_time:.2f} ms.")
        pdf.multi_cell(0, 6,
                       f"* Total Backend Operations Processed: {total_samples} requests with an execution failure frequency of {total_err_pct:.2f}%.")

        pdf.ln(4)

        # Endpoint Table Breakdown
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "5. Top Endpoint Response Breakdown", new_x="LMARGIN", new_y="NEXT")

        pdf.set_font("Helvetica", "B", 9)
        pdf.set_fill_color(0, 120, 212)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(70, 7, "API Endpoint Label", border=1, fill=True)
        pdf.cell(20, 7, "Samples", border=1, fill=True, align="C")
        pdf.cell(20, 7, "Fails", border=1, fill=True, align="C")
        pdf.cell(30, 7, "Avg (ms)", border=1, fill=True, align="C")
        pdf.cell(40, 7, "P90 (ms)", border=1, fill=True, align="C", new_x="LMARGIN", new_y="NEXT")

        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(30, 30, 30)

        for item in jmx_page_metrics[:10]:
            name_str = str(item.get('name', 'N/A'))
            lbl = name_str if len(name_str) < 35 else name_str[:32] + "..."
            pdf.cell(70, 6, lbl, border=1)
            pdf.cell(20, 6, str(item.get('samples', 0)), border=1, align="C")
            pdf.cell(20, 6, str(item.get('fail', 0)), border=1, align="C")
            pdf.cell(30, 6, f"{float(item.get('load', 0)):.2f}", border=1, align="C")
            pdf.cell(40, 6, f"{float(item.get('p90', 0)):.2f}", border=1, align="C", new_x="LMARGIN", new_y="NEXT")

        pdf.ln(6)
        pdf.set_font("Helvetica", "I", 8)
        pdf.set_text_color(120, 120, 120)
        pdf.cell(0, 5, "Confidential - TigerQE Quality Engineering Platform Center of Excellence", align="C")

        pdf.output(report_path)
    except Exception as pdf_err:
        print(f"[PDF ENGINE ERROR] Executive PDF build failed: {pdf_err}")


# -------------------------------------------
# HELPER: HTML DASHBOARD RENDERER (JMETER)
# -------------------------------------------
def build_html_dashboard_content(overall_go_status, go_bg_color, go_text_color, go_border_color,
                                 slowest_page, slowest_time, total_samples, total_err_pct,
                                 jmx_page_metrics, global_avg_load, global_p90_load,
                                 runtime_threads, runtime_rampup, loop_display_val, runtime_duration,
                                 global_tps):
    """Builds the standardized HTML Performance Dashboard String for JMeter."""
    return f"""<!DOCTYPE html>
<html>
<head>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
body {{ font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background:#f4f6f8; margin:0; padding:25px; color:#333; height: 100vh; overflow-y: auto; }}
.top-layout-row {{ display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 25px; border-bottom: 2px solid #e0e0e0; padding-bottom: 15px; }}
.header-container {{ display: flex; flex-direction: column; }}
.report-title {{ color: #0078D4; margin: 0; font-size: 28px; font-weight: 700; letter-spacing: -0.5px; }}
.go-status-badge {{ background-color: {go_bg_color}; color: {go_text_color}; border: 2px solid {go_border_color}; padding: 10px 24px; border-radius: 6px; font-size: 18px; font-weight: bold; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.05); height: fit-content; align-self: center; }}

.chatbot-embedded-box {{ background: #fff; border: 1px solid #0078D4; border-radius: 8px; margin: 20px 0; box-shadow: 0 3px 10px rgba(0,120,212,0.08); overflow: hidden; }}
.chatbot-embedded-header {{ background: #0078D4; color: white; padding: 12px 20px; font-weight: bold; font-size: 16px; display: flex; align-items: center; gap: 10px; }}
.chatbot-embedded-body {{ padding: 20px; background: #fafafa; display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
.chatbot-point-card {{ background: white; border: 1px solid #e0e0e0; border-radius: 6px; padding: 15px; box-shadow: 0 1px 3px rgba(0,0,0,0.02); }}
.chatbot-card-title {{ font-weight: bold; color: #0078D4; margin-bottom: 10px; font-size: 14px; display: flex; align-items: center; gap: 6px; }}
.chatbot-point-card ul {{ margin: 0; padding-left: 20px; font-size: 13px; color: #444; line-height: 1.6; }}
.chatbot-point-card li {{ margin-bottom: 8px; }}

table {{ border-collapse: collapse; width:100%; margin:15px 0; box-shadow: 0 2px 5px rgba(0,0,0,0.05); background:#fff; }}
th, td {{ border:1px solid #ddd; padding:10px 6px; text-align:center; vertical-align: middle; }}
th {{ background:#0078D4; color:white; font-size:12px; white-space: nowrap; }} 
td {{ font-size:12px; font-variant-numeric: tabular-nums; }} 
.section-split-header {{ color: #0078D4; border-left: 4px solid #0078D4; padding-left: 10px; margin-top: 40px; margin-bottom: 10px; font-weight: 700; }}
button.unit-toggle-btn {{ background: #0078D4; color: white; border: none; padding: 6px 14px; font-weight: bold; border-radius: 4px; cursor: pointer; }}
</style>
</head>
<body>

<div class="top-layout-row">
    <div class="header-container">
        <h1 class="report-title">Performance Dashboard Report</h1>
        <p style="margin: 5px 0 0 0; color: #666; font-size: 14px;">Automated Performance Execution Engine Workspace</p>
    </div>
    <div style="display: flex; gap: 12px; align-items: center;">
        <button class="unit-toggle-btn" style="background: #28a745; font-size: 13px; padding: 10px 18px;" onclick="window.print()">
            📥 Save / Print PDF Report
        </button>
        <div class="go-status-badge">
            Deployment Status: {overall_go_status}
        </div>
    </div>
</div>

<div class="chatbot-embedded-box">
    <div class="chatbot-embedded-header">
        <span>🤖 QE Optimization Insights</span>
    </div>
    <div class="chatbot-embedded-body">
        <div class="chatbot-point-card">
            <div class="chatbot-card-title">📊 Key Metrics Overview</div>
            <ul>
                <li><strong>Slowest Component:</strong> <code>{slowest_page}</code> averaging <strong>{slowest_time:.2f} ms</strong>.</li>
                <li><strong>Total Requests:</strong> Parsed <strong>{total_samples}</strong> requests with <strong>{total_err_pct:.2f}%</strong> error rate.</li>
            </ul>
        </div>
        <div class="chatbot-point-card">
            <div class="chatbot-card-title">💡 System Benchmarks</div>
            <ul>
                <li><strong>Average Response Time:</strong> {global_avg_load:.2f} ms</li>
                <li><strong>P90 Latency:</strong> {global_p90_load:.2f} ms</li>
                <li><strong>Throughput:</strong> {global_tps:.2f} TPS</li>
            </ul>
        </div>
    </div>
</div>

<h2 class="section-split-header">Performance Summary Breakdown</h2>
<table>
<tr>
<th>Requests Label</th>
<th># Samples</th>
<th>FAIL</th>
<th>Error %</th>
<th>Average</th>
<th>Min</th>
<th>Max</th>
<th>Median</th>
<th>90th pct</th>
<th>Throughput (TPS)</th>
</tr>
""" + "".join([f"""
<tr>
<td style="text-align:left; padding-left:8px; font-weight:bold;">{item['name']}</td>
<td>{item['samples']}</td>
<td>{item['fail']}</td>
<td>{item['error_pct']}</td>
<td style="color:green; font-weight:bold;">{item['load']:.2f} ms</td>
<td>{item['min']}</td>
<td>{item['max']}</td>
<td>{item['median']:.2f}</td>
<td>{item['p90']:.2f}</td>
<td>{item['tps']:.2f}</td>
</tr>
""" for item in jmx_page_metrics]) + f"""
</table>

<h2 class="section-split-header">Execution Settings</h2>
<div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-top: 15px;">
    <div style="background: #fff; padding: 18px 12px; border-radius: 8px; border: 1px solid #d0d7de; text-align: center;">
        <div style="font-size: 11px; color: #656d76; font-weight: 700; text-transform: uppercase;">Users (VUs/Threads)</div>
        <div style="font-size: 26px; font-weight: 800; color: #0078D4; margin-top: 6px;">{runtime_threads}</div>
    </div>
    <div style="background: #fff; padding: 18px 12px; border-radius: 8px; border: 1px solid #d0d7de; text-align: center;">
        <div style="font-size: 11px; color: #656d76; font-weight: 700; text-transform: uppercase;">Ramp-Up</div>
        <div style="font-size: 26px; font-weight: 800; color: #0078D4; margin-top: 6px;">{runtime_rampup} s</div>
    </div>
    <div style="background: #fff; padding: 18px 12px; border-radius: 8px; border: 1px solid #d0d7de; text-align: center;">
        <div style="font-size: 11px; color: #656d76; font-weight: 700; text-transform: uppercase;">Loops</div>
        <div style="font-size: 26px; font-weight: 800; color: #0078D4; margin-top: 6px;">{loop_display_val}</div>
    </div>
    <div style="background: #fff; padding: 18px 12px; border-radius: 8px; border: 1px solid #d0d7de; text-align: center;">
        <div style="font-size: 11px; color: #656d76; font-weight: 700; text-transform: uppercase;">Duration</div>
        <div style="font-size: 26px; font-weight: 800; color: #0078D4; margin-top: 6px;">{runtime_duration} s</div>
    </div>
</div>

</body>
</html>
"""


# -------------------------------------------
# HELPER: K6 DASHBOARD RENDERER (K6)
# -------------------------------------------
def build_k6_html_dashboard_content(overall_go_status, go_bg_color, go_text_color, go_border_color,
                                    slowest_page, slowest_time, total_samples, total_err_pct,
                                    k6_page_metrics, global_avg_load, global_p90_load,
                                    runtime_threads, runtime_rampup, loop_display_val, runtime_duration,
                                    global_tps, web_vitals, browser_network):
    """Builds the HTML Performance Dashboard exclusively for k6 browser tests."""
    return f"""<!DOCTYPE html>
<html>
<head>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
body {{ font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background:#f4f6f8; margin:0; padding:25px; color:#333; height: 100vh; overflow-y: auto; }}
.top-layout-row {{ display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 25px; border-bottom: 2px solid #e0e0e0; padding-bottom: 15px; }}
.header-container {{ display: flex; flex-direction: column; }}
.report-title {{ color: #0078D4; margin: 0; font-size: 28px; font-weight: 700; letter-spacing: -0.5px; }}
.go-status-badge {{ background-color: {go_bg_color}; color: {go_text_color}; border: 2px solid {go_border_color}; padding: 10px 24px; border-radius: 6px; font-size: 18px; font-weight: bold; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.05); height: fit-content; align-self: center; }}

.chatbot-embedded-box {{ background: #fff; border: 1px solid #0078D4; border-radius: 8px; margin: 20px 0; box-shadow: 0 3px 10px rgba(0,120,212,0.08); overflow: hidden; }}
.chatbot-embedded-header {{ background: #0078D4; color: white; padding: 12px 20px; font-weight: bold; font-size: 16px; display: flex; align-items: center; gap: 10px; }}
.chatbot-embedded-body {{ padding: 20px; background: #fafafa; display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
.chatbot-point-card {{ background: white; border: 1px solid #e0e0e0; border-radius: 6px; padding: 15px; box-shadow: 0 1px 3px rgba(0,0,0,0.02); }}
.chatbot-card-title {{ font-weight: bold; color: #0078D4; margin-bottom: 10px; font-size: 14px; display: flex; align-items: center; gap: 6px; }}
.chatbot-point-card ul {{ margin: 0; padding-left: 20px; font-size: 13px; color: #444; line-height: 1.6; }}
.chatbot-point-card li {{ margin-bottom: 8px; }}

table {{ border-collapse: collapse; width:100%; margin:15px 0; box-shadow: 0 2px 5px rgba(0,0,0,0.05); background:#fff; }}
th, td {{ border:1px solid #ddd; padding:10px 6px; text-align:center; vertical-align: middle; }}
th {{ background:#0078D4; color:white; font-size:12px; white-space: nowrap; }} 
td {{ font-size:12px; font-variant-numeric: tabular-nums; }} 
.section-split-header {{ color: #0078D4; border-left: 4px solid #0078D4; padding-left: 10px; margin-top: 40px; margin-bottom: 10px; font-weight: 700; }}
button.unit-toggle-btn {{ background: #0078D4; color: white; border: none; padding: 6px 14px; font-weight: bold; border-radius: 4px; cursor: pointer; }}
</style>
</head>
<body>

<div class="top-layout-row">
    <div class="header-container">
        <h1 class="report-title">k6 Browser Performance Dashboard</h1>
        <p style="margin: 5px 0 0 0; color: #666; font-size: 14px;">Automated k6 Browser Workload & Web Vitals Execution Engine</p>
    </div>
    <div style="display: flex; gap: 12px; align-items: center;">
        <button class="unit-toggle-btn" style="background: #28a745; font-size: 13px; padding: 10px 18px;" onclick="window.print()">
            📥 Save / Print PDF Report
        </button>
        <div class="go-status-badge">
            Deployment Status: {overall_go_status}
        </div>
    </div>
</div>

<div class="chatbot-embedded-box">
    <div class="chatbot-embedded-header">
        <span>🤖 QE Optimization Insights</span>
    </div>
    <div class="chatbot-embedded-body">
        <div class="chatbot-point-card">
            <div class="chatbot-card-title">📊 Key Metrics Overview</div>
            <ul>
                <li><strong>Slowest Component:</strong> <code>{slowest_page}</code> averaging <strong>{slowest_time:.2f} ms</strong>.</li>
                <li><strong>Total Requests:</strong> Parsed <strong>{total_samples}</strong> requests with <strong>{total_err_pct:.2f}%</strong> error rate.</li>
            </ul>
        </div>
        <div class="chatbot-point-card">
            <div class="chatbot-card-title">💡 System Benchmarks</div>
            <ul>
                <li><strong>Average Response Time:</strong> {global_avg_load:.2f} ms</li>
                <li><strong>P90 Latency:</strong> {global_p90_load:.2f} ms</li>
                <li><strong>Throughput:</strong> {global_tps:.2f} TPS</li>
            </ul>
        </div>
    </div>
</div>

<h2 class="section-split-header">🌐 Frontend Web Vitals & Browser Metrics</h2>
<div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin-top: 15px;">
    <div style="background: #fff; padding: 15px; border-radius: 8px; border: 1px solid #d0d7de; text-align: center;">
        <div style="font-size: 11px; color: #656d76; font-weight: 700; text-transform: uppercase;">First Contentful Paint (FCP)</div>
        <div style="font-size: 22px; font-weight: 800; color: #0078D4; margin-top: 6px;">{web_vitals.get('fcp', 0.0):.2f} ms</div>
    </div>
    <div style="background: #fff; padding: 15px; border-radius: 8px; border: 1px solid #d0d7de; text-align: center;">
        <div style="font-size: 11px; color: #656d76; font-weight: 700; text-transform: uppercase;">Largest Contentful Paint (LCP)</div>
        <div style="font-size: 22px; font-weight: 800; color: #0078D4; margin-top: 6px;">{web_vitals.get('lcp', 0.0):.2f} ms</div>
    </div>
    <div style="background: #fff; padding: 15px; border-radius: 8px; border: 1px solid #d0d7de; text-align: center;">
        <div style="font-size: 11px; color: #656d76; font-weight: 700; text-transform: uppercase;">Time to First Byte (TTFB)</div>
        <div style="font-size: 22px; font-weight: 800; color: #0078D4; margin-top: 6px;">{web_vitals.get('ttfb', 0.0):.2f} ms</div>
    </div>
    <div style="background: #fff; padding: 15px; border-radius: 8px; border: 1px solid #d0d7de; text-align: center;">
        <div style="font-size: 11px; color: #656d76; font-weight: 700; text-transform: uppercase;">Cumulative Layout Shift (CLS)</div>
        <div style="font-size: 22px; font-weight: 800; color: #0078D4; margin-top: 6px;">{web_vitals.get('cls', 0.0):.3f}</div>
    </div>
    <div style="background: #fff; padding: 15px; border-radius: 8px; border: 1px solid #d0d7de; text-align: center;">
        <div style="font-size: 11px; color: #656d76; font-weight: 700; text-transform: uppercase;">Interaction to Next Paint (INP)</div>
        <div style="font-size: 22px; font-weight: 800; color: #0078D4; margin-top: 6px;">{web_vitals.get('inp', 0.0):.2f} ms</div>
    </div>
    <div style="background: #fff; padding: 15px; border-radius: 8px; border: 1px solid #d0d7de; text-align: center;">
        <div style="font-size: 11px; color: #656d76; font-weight: 700; text-transform: uppercase;">Browser Data Recv / Sent</div>
        <div style="font-size: 18px; font-weight: 800; color: #28a745; margin-top: 6px;">{browser_network.get('recv_kb', 0.0):.1f} KB / {browser_network.get('sent_kb', 0.0):.1f} KB</div>
    </div>
</div>

<h2 class="section-split-header">Performance Summary Breakdown</h2>
<table>
<tr>
<th>Requests Label</th>
<th># Samples</th>
<th>FAIL</th>
<th>Error %</th>
<th>Average</th>
<th>Min</th>
<th>Max</th>
<th>Median</th>
<th>90th pct</th>
<th>Throughput (TPS)</th>
</tr>
""" + "".join([f"""
<tr>
<td style="text-align:left; padding-left:8px; font-weight:bold;">{item['name']}</td>
<td>{item['samples']}</td>
<td>{item['fail']}</td>
<td>{item['error_pct']}</td>
<td style="color:green; font-weight:bold;">{item['load']:.2f} ms</td>
<td>{item['min']}</td>
<td>{item['max']}</td>
<td>{item['median']:.2f}</td>
<td>{item['p90']:.2f}</td>
<td>{item['tps']:.2f}</td>
</tr>
""" for item in k6_page_metrics]) + f"""
</table>

<h2 class="section-split-header">Execution Settings</h2>
<div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-top: 15px;">
    <div style="background: #fff; padding: 18px 12px; border-radius: 8px; border: 1px solid #d0d7de; text-align: center;">
        <div style="font-size: 11px; color: #656d76; font-weight: 700; text-transform: uppercase;">Users (VUs/Threads)</div>
        <div style="font-size: 26px; font-weight: 800; color: #0078D4; margin-top: 6px;">{runtime_threads}</div>
    </div>
    <div style="background: #fff; padding: 18px 12px; border-radius: 8px; border: 1px solid #d0d7de; text-align: center;">
        <div style="font-size: 11px; color: #656d76; font-weight: 700; text-transform: uppercase;">Ramp-Up</div>
        <div style="font-size: 26px; font-weight: 800; color: #0078D4; margin-top: 6px;">{runtime_rampup} s</div>
    </div>
    <div style="background: #fff; padding: 18px 12px; border-radius: 8px; border: 1px solid #d0d7de; text-align: center;">
        <div style="font-size: 11px; color: #656d76; font-weight: 700; text-transform: uppercase;">Loops</div>
        <div style="font-size: 26px; font-weight: 800; color: #0078D4; margin-top: 6px;">{loop_display_val}</div>
    </div>
    <div style="background: #fff; padding: 18px 12px; border-radius: 8px; border: 1px solid #d0d7de; text-align: center;">
        <div style="font-size: 11px; color: #656d76; font-weight: 700; text-transform: uppercase;">Duration</div>
        <div style="font-size: 26px; font-weight: 800; color: #0078D4; margin-top: 6px;">{runtime_duration} s</div>
    </div>
</div>

</body>
</html>
"""


st.set_page_config(
    page_title="TigerQE AI iQEA",
    page_icon="🤖",
    layout="centered"
)

# Session state setup
if "page_url" not in st.session_state:
    st.session_state.page_url = None
if "repo_url" not in st.session_state:
    st.session_state.repo_url = None
if "selected_images" not in st.session_state:
    st.session_state.selected_images = []
if "show_popup" not in st.session_state:
    st.session_state.show_popup = False
if "show_form" not in st.session_state:
    st.session_state.show_form = False
if 'stop_monitor' not in st.session_state:
    st.session_state.stop_monitor = {"stop": False}
if 'monitor_thread' not in st.session_state:
    st.session_state.monitor_thread = None
if 'driver' not in st.session_state:
    st.session_state.driver = None
if 'recording_started' not in st.session_state:
    st.session_state.recording_started = False
if 'actions' not in st.session_state:
    st.session_state.actions = []
if 'selected_xpaths' not in st.session_state:
    st.session_state.selected_xpaths = []
if 'prompt_response' not in st.session_state:
    st.session_state.prompt_response = ""
if 'prompt_response_page_file' not in st.session_state:
    st.session_state.prompt_response_page_file = ""
if 'last_page' not in st.session_state:
    st.session_state.last_page = None
if 'selected_tags' not in st.session_state:
    st.session_state.selected_tags = ["input", "button"]
if 'selected_app' not in st.session_state:
    st.session_state.selected_app = []
if 'requirements_details' not in st.session_state:
    st.session_state.requirements_details = None
if 'accuracy_response' not in st.session_state:
    st.session_state.accuracy_response = None
if 'testcase_response' not in st.session_state:
    st.session_state.testcase_response = []
if 'scenario_response' not in st.session_state:
    st.session_state.scenario_response = []
if 'all_testcases' not in st.session_state:
    st.session_state.all_testcases = []
if 'testcase_regeneration' not in st.session_state:
    st.session_state.testcase_regeneration = None
if 'overall_accuracy' not in st.session_state:
    st.session_state.overall_accuracy = None
if "scroll_to_top" not in st.session_state:
    st.session_state.scroll_to_top = False
if "checkbox1_state" not in st.session_state:
    st.session_state.checkbox1_state = True
if "checkbox2_state" not in st.session_state:
    st.session_state.checkbox2_state = False
if "checkbox3_state" not in st.session_state:
    st.session_state.checkbox3_state = True
if "checkbox4_state" not in st.session_state:
    st.session_state.checkbox4_state = True
if "checkbox5_state" not in st.session_state:
    st.session_state.checkbox5_state = True
if "checkbox6_state" not in st.session_state:
    st.session_state.checkbox6_state = True
if "checkbox7_state" not in st.session_state:
    st.session_state.checkbox7_state = True
if "checkbox8_state" not in st.session_state:
    st.session_state.checkbox8_state = True
if "checkbox9_state" not in st.session_state:
    st.session_state.checkbox9_state = True
if "failed_files" not in st.session_state:
    st.session_state.failed_files = []
if "regenerate_clicked" not in st.session_state:
    st.session_state.regenerate_clicked = False
if "save_testcases" not in st.session_state:
    st.session_state.save_testcases = False
if "save_regenerated_testcases" not in st.session_state:
    st.session_state.save_regenerated_testcases = False
if 'workflow_text' not in st.session_state:
    st.session_state.workflow_text = []
if "generated_test_script" not in st.session_state:
    st.session_state.generated_test_script = None
if "script_gen_inputs" not in st.session_state:
    st.session_state.script_gen_inputs = {}
if "script_editor_version" not in st.session_state:
    st.session_state.script_editor_version = 0
if 'injected_windows' not in st.session_state:
    st.session_state.injected_windows = {}
if 'workflow_text_desktop' not in st.session_state:
    st.session_state.workflow_text_desktop = []
if "xpath_for_new_page" not in st.session_state:
    st.session_state.xpath_for_new_page = False
if "xpath_for_new_page_user_info" not in st.session_state:
    st.session_state.xpath_for_new_page_user_info = False

# ── Record & Playback session state ──
if "recorded_script" not in st.session_state:
    st.session_state.recorded_script = None
if "recorded_script_language" not in st.session_state:
    st.session_state.recorded_script_language = "Python-Selenium"
if "rb_actions_snapshot" not in st.session_state:
    st.session_state.rb_actions_snapshot = []

# --- Track expander state only for collection ---
if "open_expander_collection" not in st.session_state:
    st.session_state.open_expander_collection = False
if "recorded_actions_history" not in st.session_state:
    st.session_state.recorded_actions_history = False

# ---------- TMT integration----------
if "tmt_tool" not in st.session_state:
    st.session_state.tmt_tool = "None"
if "tmt_connected" not in st.session_state:
    st.session_state.tmt_connected = False
if "tmt_existing_tcs" not in st.session_state:
    st.session_state.tmt_existing_tcs = []
if "tmt_selected_plan_id" not in st.session_state:
    st.session_state.tmt_selected_plan_id = None
if "tmt_selected_suite_id" not in st.session_state:
    st.session_state.tmt_selected_suite_id = None
if "tmt_plans" not in st.session_state:
    st.session_state.tmt_plans = []
if "tmt_suites" not in st.session_state:
    st.session_state.tmt_suites = []
if "gap_analysis_result" not in st.session_state:
    st.session_state.gap_analysis_result = None
if "tmt_jira_project_key" not in st.session_state:
    st.session_state.tmt_jira_project_key = ""
if "tmt_fetch_type" not in st.session_state:
    st.session_state.tmt_fetch_type = "Test Cases"
if "tmt_gap_approved" not in st.session_state:
    st.session_state.tmt_gap_approved = False
if "tmt_replacement_responses" not in st.session_state:
    st.session_state.tmt_replacement_responses = []
if "tmt_deletion_notice" not in st.session_state:
    st.session_state.tmt_deletion_notice = []
if "tmt_gen_inputs" not in st.session_state:
    st.session_state.tmt_gen_inputs = {}

if "document_source_selector" not in st.session_state:
    st.session_state.document_source_selector = "Files"

if "uploaded_file_path" not in st.session_state:
    st.session_state.uploaded_file_path = None

if "azure_workitem_id" not in st.session_state:
    st.session_state.azure_workitem_id = ""

if "jira_workitem_id" not in st.session_state:
    st.session_state.jira_workitem_id = ""
if "excel_path" not in st.session_state:
    st.session_state.excel_path = ""
### test_data_generate
if "test_data_action_data" not in st.session_state:
    st.session_state.test_data_action_data = ""
if "test_files_content" not in st.session_state:
    st.session_state.test_files_content = ""
if "test_data_addition_info" not in st.session_state:
    st.session_state.test_data_addition_info = ""
if "test_data_llm_response" not in st.session_state:
    st.session_state.test_data_llm_response = ""
#### Api
if "api_data" not in st.session_state:
    st.session_state.api_data = ""
####xpath
if "select_all" not in st.session_state:
    st.session_state.select_all = False

# Performance Agent session states
if "generated_jmx" not in st.session_state:
    st.session_state.generated_jmx = ""
if "generated_jmx_path" not in st.session_state:
    st.session_state.generated_jmx_path = ""
if "generated_k6_script" not in st.session_state:
    st.session_state.generated_k6_script = ""
if "generated_k6_path" not in st.session_state:
    st.session_state.generated_k6_path = ""

st.title(" 🤖 TigerQE AI Platform - iQEA (Intelligent QE Assistant)")

###desktop
if "desktop_action_name" not in st.session_state:
    st.session_state.desktop_action_name = ""
if "recorder" not in st.session_state:
    st.session_state.recorder = DesktopRecorder()

##playback
if "rb_language" not in st.session_state:
    st.session_state.rb_language = "Python-Selenium"

# 1. Open the browser
page_url = st.text_input("Enter the URL of the page:")
st.session_state.page_url = page_url
if st.button("Open Browser"):
    if page_url:
        clean_url = page_url.strip()
        if clean_url and not clean_url.startswith(("http://", "https://")):
            clean_url = "https://" + clean_url
        if not clean_url:
            st.warning("⚠️ Please enter a valid URL.")
        else:
            chromedriver_path = os.path.join(input_folder, "chromedriver.exe")
            chrome_options = Options()
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-software-rasterizer")
            chrome_options.add_argument("--remote-debugging-port=9222")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--remote-allow-origins=*")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
            st.session_state.driver = webdriver.Chrome(options=chrome_options)
            st.session_state.driver.get(clean_url)
            st.session_state.driver.maximize_window()
            WebDriverWait(st.session_state.driver, 30).until(utils.is_page_loaded)
            st.success("✅ Browser opened and ready.")
    else:
        st.warning("⚠️ Please enter a URL before opening the browser.")

# ==============================
# TOOL RAIL
# ==============================
from contextlib import contextmanager


@contextmanager
def _workspace(title):
    """Render the active tool inside a single bordered card."""
    with st.container(border=True):
        yield


st.markdown("""
<style>
.stButton>button[kind="primary"]{background:#F47B20;border-color:#F47B20;}
.stButton>button{font-weight:600;}
.iqea-phase{
    background:transparent;
    color:#E8650A !important;
    font-weight:800; font-size:15px; letter-spacing:.6px; text-transform:uppercase;
    text-align:center; padding:2px 0 8px 0;
    margin:0 0 12px 0; border-bottom:2px solid #F47B20;
}
.iqea-rail [data-testid="stVerticalBlockBorderWrapper"]{
    background:#ffffff; border:1px solid #E3E6EC !important; border-radius:12px;
    box-shadow:0 3px 10px rgba(0,0,0,.05); min-height:170px;
}
</style>
""", unsafe_allow_html=True)

_IQEA_PHASES = [
    ("🎬 Capture", [("recorder", "🔴 Recorder")]),
    ("📝 Author", [("testcases", "🧮 Test Cases"), ("testdata", "🧪 Test Data"),
                  *([("bdd", "🧾 BDD Feature")] if source == "database" else []), ]),
    ("🔧 Build", [("pom", "🔎 Locators / POM"), ("scripts", "📜 Script Gen")]),
    ("🚀 Run & Report", [
        ("execute", "▶️ Execute & Report"),
        ("performance", "📊 Performance Testing"),
        *([("artifacts", "📥 Artifacts")] if source == "database" else []),
    ]),
    ("🔗 Integrate", [("repo", "⚙️ Repo Push")]),
]

if "iqea_active_tool" not in st.session_state:
    st.session_state.iqea_active_tool = "recorder"

st.markdown("##### 🧰 Select Agent")
st.markdown("<div class='iqea-rail'>", unsafe_allow_html=True)
_rail_cols = st.columns(len(_IQEA_PHASES))
for _col, (_phase, _tools) in zip(_rail_cols, _IQEA_PHASES):
    with _col:
        with st.container(border=True):
            st.markdown(f"<div class='iqea-phase'>{_phase}</div>", unsafe_allow_html=True)
            for _tid, _label in _tools:
                if st.button(
                        _label,
                        key=f"iqea_nav_{_tid}",
                        use_container_width=True,
                        type="primary" if st.session_state.iqea_active_tool == _tid else "secondary",
                ):
                    st.session_state.iqea_active_tool = _tid
                    st.rerun()
st.markdown("</div>", unsafe_allow_html=True)

_tool = st.session_state.iqea_active_tool
st.divider()

if _tool == "recorder":
    with _workspace("🔴 User Workflow Recorder"):
        option = st.radio(
            "Choose where to record:",
            ('Web', 'Desktop')
        )
        if option == 'Web':
            st.subheader("Record User Actions & Capture Screenshots of User Navigation")
            st.session_state.workflow_text = []
            if not st.session_state.recording_started and st.button("🎥 Start Recording"):
                if st.session_state.driver:
                    if "monitor_threads" in st.session_state:
                        st.session_state.stop_monitor["stop"] = True
                        for t in st.session_state.monitor_threads:
                            if t and t.is_alive():
                                t.join(timeout=2)

                    st.session_state.injected_windows = {}
                    st.session_state.last_urls = {}
                    st.session_state.current_window_ref = {"handle": None}
                    st.session_state.stop_monitor = {"stop": False}
                    st.session_state.monitor_threads = []
                    st.session_state.actions = []
                    st.session_state.workflow_text = []
                    st.session_state.recorded_script = None
                    st.session_state.rb_actions_snapshot = []
                    handle = st.session_state.driver.current_window_handle
                    st.session_state.driver.execute_script(action_utils.injection_script_agentflow())
                    print(f"✅ JS injected in new window {handle} ({st.session_state.driver.current_url})")
                    st.session_state.injected_windows[handle] = True

                    t1 = threading.Thread(
                        target=utils.thread_new_window_checker,
                        args=(
                            st.session_state.driver,
                            st.session_state.injected_windows,
                            st.session_state.last_urls,
                            st.session_state.stop_monitor,
                            page_screenshot_folder,
                            st.session_state.current_window_ref
                        ),
                        daemon=True
                    )
                    t2 = threading.Thread(
                        target=utils.thread_focus_and_url_monitor,
                        args=(
                            st.session_state.driver,
                            st.session_state.injected_windows,
                            st.session_state.last_urls,
                            st.session_state.stop_monitor,
                            page_screenshot_folder,
                            st.session_state.current_window_ref
                        ),
                        daemon=True
                    )
                    t3 = threading.Thread(
                        target=utils.thread_focus_screenshot,
                        args=(
                            st.session_state.driver,
                            st.session_state.stop_monitor,
                            page_screenshot_folder, source
                        ),
                        daemon=True
                    )
                    t4 = threading.Thread(
                        target=utils.thread_reinject_action_check,
                        args=(
                            st.session_state.driver,
                            st.session_state.stop_monitor,
                            st.session_state.last_urls, st.session_state.current_window_ref,
                            st.session_state.injected_windows
                        ),
                        daemon=True
                    )
                    t1.start()
                    t2.start()
                    t3.start()
                    t4.start()

                    st.session_state.monitor_threads = [t1, t2, t3, t4]
                    st.session_state.recording_started = True
                    st.success("Recording started. Please interact in the browser.")
            if st.session_state.recording_started and st.button("🛑 Stop Recording"):

                st.session_state.actions = action_utils.get_recorded_actions(
                    st.session_state.driver)
                st.session_state.rb_actions_snapshot = list(st.session_state.actions)
                st.session_state.recording_started = False

                st.session_state.stop_monitor["stop"] = True

                # 2. Extract captured XHR network requests (PUT/POST/Payloads)
                captured_network_data = extract_xhr_network_logs(st.session_state.driver)
                st.session_state["captured_network_logs"] = captured_network_data

                # 3. SAVE TO PHYSICAL FILE (Added Block)
                har_filename = os.path.join(Action_collection, "network_traffic_log.har")
                with open(har_filename, "w", encoding="utf-8") as f:
                    f.write(captured_network_data)

                for t in st.session_state.get("monitor_threads", []):
                    if t and t.is_alive():
                        t.join(timeout=2)

                st.session_state.monitor_threads = []
                st.success("Recording stopped. Performed actions are captured.")
                actions = []
                st.session_state.injected_windows.clear()

            if st.session_state.actions:
                st.session_state.workflow_text = []
                page_name = st.text_input("Enter Page Name for Saving the Workflow:")
                if st.button("💾 Save Workflow"):

                    if not page_name:
                        st.warning("⚠ Please enter a name for the workflow.")
                    else:
                        st.session_state.workflow_text = action_utils.generate_workflow_manual(st.session_state.actions)
                        workflow_saved = False
                        print("workflow_text", st.session_state.workflow_text)
                        if source == "database":
                            action_id = db_handler.save_action_to_db(page_name, st.session_state.workflow_text,
                                                                     get_update_user())
                            st.success(f"✅ Action saved to database (ID: {action_id})")
                        elif source == "file":
                            filename = os.path.join(Action_collection, f"{page_name}_actions.txt")


                            def clean_text(s):
                                return (
                                    s.replace("\u200b", "")
                                    .replace("\xa0", " ")
                                    .strip()
                                )


                            cleaned = [clean_text(x) for x in st.session_state.workflow_text]
                            with open(filename, "w", encoding="utf-8") as f:
                                f.write("\n".join(cleaned))
                            st.success(f"✅ Workflow saved: {filename}")
                            st.download_button("⬇ Download Workflow", data="\n".join(st.session_state.workflow_text),
                                               file_name=f"{page_name}_actions.txt")
                            workflow_saved = True
                        if workflow_saved:
                            clear_actions = """(function() {
                                            window.__recordedActions = [];
                                            localStorage.removeItem("recordedActions");
                                            console.log("🧹 Cleared previous recorded actions before new recording session.");
                                        })();"""
                            st.session_state.driver.execute_script(clear_actions)
                            st.session_state.actions.clear()
                            st.session_state.workflow_text.clear()
                            st.session_state.show_popup = True
                            st.session_state.show_form = False

        if option == 'Desktop':
            st.subheader("Record User Actions & Capture Screenshots of User Navigation")

            if "desktop_recording_started" not in st.session_state:
                st.session_state.desktop_recording_started = False
            if "recorder" not in st.session_state:
                st.session_state.recorder = None

            application_path = st.text_input(
                "Enter full path to application (.exe):",
                placeholder=r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE"
            )

            if application_path and not st.session_state.desktop_recording_started:
                if st.button("🎥 Launch and Start Recording"):
                    with st.spinner("Launching application, please wait..."):
                        try:
                            session = DesktopSession(application_path)
                            app = session.start(timeout=15)

                            recorder = DesktopRecorder()
                            recorder.start()

                            st.session_state.recorder = recorder
                            st.session_state.desktop_recording_started = True
                            st.rerun()

                        except Exception as e:
                            st.error(f"Failed to launch application: {e}")

            if st.session_state.desktop_recording_started:
                st.info("🔴 Recording in progress... Interact with the application, then click Stop.")

                if st.button("🛑 Stop Recording"):
                    st.session_state.recorder.stop()
                    st.session_state.desktop_recording_started = False
                    action_count = len(st.session_state.recorder.get_actions())
                    st.success(f"✅ Recording stopped. {action_count} action(s) captured.")
                    st.rerun()

            if (not st.session_state.desktop_recording_started
                    and st.session_state.recorder
                    and st.session_state.recorder.get_actions()):

                workflow_name = st.text_input("Enter name for saving the workflow:")

                if workflow_name:
                    if st.button("💾 Save Desktop Workflow"):
                        file_name = workflow_name
                        st.session_state.workflow_text_desktop = st.session_state.recorder.save(file_name)
                        filename = os.path.join(Action_collection_desktop, f"{file_name}_desktop_actions.txt")


                        def clean_text(s):
                            return (
                                s.replace("\u200b", "")
                                .replace("\xa0", " ")
                                .strip()
                            )


                        cleaned = [clean_text(x) for x in st.session_state.workflow_text_desktop]
                        with open(filename, "w", encoding="utf-8") as f:
                            f.write("\n".join(cleaned))
                        st.success(f"✅ Workflow saved: {filename}")
                        st.download_button("⬇ Download Workflow",
                                           data="\n".join(st.session_state.workflow_text_desktop),
                                           file_name=f"{file_name}_actions.txt")
                        st.session_state.recorder = None
                        st.session_state.workflow_text_desktop = []

        if st.session_state.rb_actions_snapshot:
            with st.expander("⚡ Quick Script Generator (Record & Playback)", expanded=False):
                st.caption(
                    "Generate an automation script directly from your recorded actions — "
                    "no page file or test case needed."
                )
                st.session_state.rb_language = st.selectbox(
                    "Select target language / framework",
                    ["Python-Selenium", "Python-Playwright", "Java-Selenium", "Java-Playwright", "UTAM-JavaScript"],
                    key="rb_language_select"
                )
                rb_script_name = st.text_input("Script file name (without extension):", key="rb_script_name")

                if st.button("⚡ Generate Script from Recording", key="rb_generate_btn"):
                    with st.spinner("Generating script from recorded actions..."):
                        actions_formatted = action_utils.format_actions_for_script_generation(
                            st.session_state.rb_actions_snapshot
                        )
                        script = utils.generate_script_from_recorded_actions(actions_formatted,
                                                                             st.session_state.rb_language)
                        if script:
                            st.session_state.recorded_script = script
                            st.session_state.recorded_script_language = st.session_state.rb_language
                            st.success("✅ Script generated from recording.")
                        else:
                            st.error("Failed to generate script from recording.check the error logs")

                if st.session_state.recorded_script:
                    _rb_lang = st.session_state.recorded_script_language
                    _code_lang = (
                        "java" if "java" in _rb_lang.lower()
                        else ("javascript" if "javascript" in _rb_lang.lower() else "python")
                    )
                    st.subheader("📝 Generated Script")
                    st.code(st.session_state.recorded_script, language=_code_lang)

                    with st.expander("✏️ Edit before saving", expanded=False):
                        st.text_area(
                            "Edit the script:",
                            value=st.session_state.recorded_script,
                            key="rb_script_editor",
                            height=500
                        )

                    if st.button("💾 Save Script", key="rb_save_btn"):
                        if not rb_script_name:
                            st.warning("Please enter a script file name.")
                        else:
                            final_rb_script = st.session_state.get(
                                "rb_script_editor", st.session_state.recorded_script
                            )
                            utils.create_test_file(Test_file_generator, rb_script_name,
                                                   _rb_lang, final_rb_script)
                            st.success(f"✅ Script saved: {rb_script_name}")

if _tool == "bdd":
    with _workspace("🧾 BDD Feature File Generator"):
        st.title("Feature file Generator using recorded actions")
        Feature_file_name = st.text_input("Enter feature file Name")
        Action_data = ""
        if source == "file":
            Action_data = utils.select_and_read_text_files(Action_collection)
        elif source == "database":
            all_files = db_handler.get_all_action_names()
            selected_files = st.multiselect("Feature - Select saved action files from database", all_files)

            if selected_files:
                merged_content = ""

                for file in selected_files:
                    content = db_handler.get_action_content_by_name(file, "action")
                    if content:
                        merged_content += f"\n### {file} ###\n{content}\n"
                    else:
                        st.warning(f"⚠️ Could not load content for: {file}")
                Action_data = merged_content

        action_prompt = f"""Summarize the following context into a concise and structured format (under 100 lines), preserving key actions, entities, and sequences. The goal is to retain essential meaning for AI understanding, automation, or test case generation. Avoid repetition, and group related items logically. Context: {Action_data} """
        action_data_processed = utils.get_queries_from_ai_updated(action_prompt)
        feature_prompt = utils.generate_pom_from_excel_feature("Feature_file", action_data_processed)
        if st.button("Generate_feature_File"):
            feature_response = utils.get_queries_from_ai_updated(feature_prompt)
            if source == "file":
                save_feature_file = os.path.join(feature_file_collection, f"{Feature_file_name}.feature")
                with open(save_feature_file, "w") as file:
                    file.write(feature_response.strip())

                st.write(f"Feature file saved here: {save_feature_file}")
            if source == "database":
                db_handler.save_featurefile_to_db(Feature_file_name, feature_response, get_update_user())
                st.success(f"feature file save in database for '{Feature_file_name}'")

if _tool == "testcases":
    with _workspace("🧮 E2E Scenario Based Test Case Generator"):

        st.title("E2E Scenario Based Test Case Generation")

        option = st.radio(
            "Choose your Flow with:",
            ('Documents', 'Recorded_Details')
        )

        if option == 'Recorded_Details':
            if source == "file":
                st.markdown("**Select Images (Mandatory)** <span style='color:red;'>*</span>", unsafe_allow_html=True)
                image_files = [f for f in os.listdir(page_screenshot_folder) if
                               f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]
                cols = st.columns(5)
                for idx, image_file in enumerate(image_files):
                    with cols[idx % 5]:
                        st.image(os.path.join(page_screenshot_folder, image_file), width=100)
                        if image_file not in st.session_state.selected_images:
                            if st.button(f"{image_file}", key=f"{image_file}"):
                                st.session_state.selected_images.append(image_file)
                        else:
                            if st.button(f"Deselect {image_file}", key=f"deselect_{image_file}"):
                                st.session_state.selected_images.remove(image_file)
            if source == "database":
                st.markdown("**Select Images from database (Mandatory)** <span style='color:red;'>*</span>",
                            unsafe_allow_html=True)

                screenshots = db_handler.get_all_screenshots()

                if not screenshots:
                    st.warning("⚠️ No images found in the database.")
                else:
                    cols = st.columns(5)

                    for idx, screenshot in enumerate(screenshots):
                        with cols[idx % 5]:
                            image = Image.open(io.BytesIO(screenshot.image_data))

                            max_width = 100
                            aspect_ratio = image.height / image.width
                            resized_image = image.resize((max_width, int(max_width * aspect_ratio)))

                            st.image(resized_image, use_container_width=False)

                            label = f"{screenshot.page_name}_{screenshot.id}"

                            if label not in st.session_state.selected_images:
                                if st.button(f"{label}", key=f"{label}"):
                                    st.session_state.selected_images.append(label)
                            else:
                                if st.button(f"Deselect {label}", key=f"deselect_{label}"):
                                    st.session_state.selected_images.remove(label)

            if st.session_state.selected_images:
                st.write("### Selected images in order:")
                for i, img_name in enumerate(st.session_state.selected_images, 1):
                    st.write(f"{i}. {img_name}")

            if st.button("Clear All Selection"):
                st.session_state.selected_images = []

            st.markdown("**Upload Wireframe / Additional Images (Optional)**", unsafe_allow_html=True)
            wireframe_uploads = st.file_uploader(
                "Upload wireframe or additional images",
                type=["png", "jpg", "jpeg"],
                accept_multiple_files=True,
                key="wireframe_image_uploader"
            )
            if wireframe_uploads:
                for wf_file in wireframe_uploads:
                    save_path = os.path.join(page_screenshot_folder, wf_file.name)
                    with open(save_path, "wb") as f:
                        f.write(wf_file.getbuffer())
                    if wf_file.name not in st.session_state.selected_images:
                        st.session_state.selected_images.append(wf_file.name)
                st.success(f"{len(wireframe_uploads)} wireframe image(s) added to selection.")

            st.markdown("**Enter the additional information or requirements** <span style='color:red;'>*</span>",
                        unsafe_allow_html=True)
            prompt = st.text_area("Enter the test requirements", "", key="user_requirements_textarea")
            st.markdown("**Please select relevent action file(Optional)**", unsafe_allow_html=True)
            Action_data = ""
            if source == "file":
                Action_data = utils.select_and_read_text_files(Action_collection)
            elif source == "database":
                all_files = db_handler.get_all_action_names()
                selected_files = st.multiselect("Select saved action files from database", all_files)

                if selected_files:
                    merged_content = ""

                    for file in selected_files:
                        content = db_handler.get_action_content_by_name(file, "action")
                        if content:
                            merged_content += f"\n### {file} ###\n{content}\n"
                        else:
                            st.warning(f"⚠️ Could not load content for: {file}")
                    Action_data = merged_content
        elif option == 'Documents':
            pbi_mode = "Web"
            wireframe_files = None

            source_type = st.selectbox(
                "Select Source Type",
                options=["Files", "Azure Board", "Jira"],
                index=0,
            )
            st.session_state.document_source_selector = source_type
            if source_type == "Files":
                pbi_mode = st.radio(
                    "Application Type",
                    options=["Web", "Power BI"],
                    index=0,
                    horizontal=True,
                    key="doc_app_type_radio",
                    help="Web keeps the standard functional test case flow. Power BI generates "
                         "manual test cases to validate a Power BI report (visuals, filters, slicers) "
                         "from the requirements document and wireframe."
                )
                uploaded_file = st.file_uploader(
                    "Upload a PDF, Text, Word, or Excel document",
                    type=['pdf', 'docx', 'xlsx', 'txt'],
                    key="uploaded_file_uploader"
                )

                if pbi_mode == "Power BI":
                    st.markdown(
                        "**Upload Power BI wireframe image(s)** <span style='color:red;'>*</span> "
                        "— fed directly to the AI to detect visuals, visual type & position",
                        unsafe_allow_html=True
                    )
                    st.caption(
                        "💡 Upload **one wireframe per report page** (e.g. a separate image for the "
                        "Summary page and the Sales Operations page). Pages without a wireframe are "
                        "still covered from the requirements text, but an image gives far better "
                        "visual-type and layout validation."
                    )
                    wireframe_files = st.file_uploader(
                        "Upload wireframe image(s) for the Power BI report — one per page",
                        type=["png", "jpg", "jpeg", "bmp", "webp"],
                        accept_multiple_files=True,
                        key="pbi_wireframe_uploader"
                    )
                if uploaded_file is not None:
                    filename = uploaded_file.name.lower()

                    if filename.endswith(".pdf"):
                        st.success("PDF file uploaded successfully!")
                    elif filename.endswith(".docx"):
                        st.success("Word file uploaded successfully!")
                    elif filename.endswith(".xlsx"):
                        st.success("Excel file uploaded successfully!")
                    elif filename.endswith(".txt"):
                        st.success("Text file uploaded successfully!")
                        try:
                            text_content = uploaded_file.read().decode("utf-8", errors="ignore")
                        except Exception as e:
                            st.error(f"Error reading TXT file: {e}")
                    else:
                        st.error("Unsupported file format.")
            elif source_type == "Azure Board":
                st.info("Enter Azure Work Item ID (numeric)")
                workitem = st.text_input("Azure Work Item ID", value=st.session_state.azure_workitem_id,
                                         key="azure_workitem_text")
                st.session_state.azure_workitem_id = workitem.strip()

                if workitem and not workitem.isdigit():
                    st.warning("Work Item ID typically numeric — ensure it's correct.")

            elif source_type == "Jira":
                st.info("Enter Jira Issue ID (e.g. PROJ-123)")
                jira_id = st.text_input("Jira Issue ID", value=st.session_state.jira_workitem_id,
                                        key="jira_workitem_text")
                st.session_state.jira_workitem_id = jira_id.strip()
            Document_image_data = ""
            image_uploaded_files = st.file_uploader(
                "📁 Upload one or more image files (Optional)",
                type=["jpg", "jpeg", "png", "bmp", "tiff", "webp"],
                accept_multiple_files=True
            )
            if image_uploaded_files:
                st.info("📸 Image processed.")
                for image_uploaded_file in image_uploaded_files:
                    try:
                        image = Image.open(image_uploaded_file)
                        extracted_text = pytesseract.image_to_string(image)
                        if extracted_text.strip():
                            Document_image_data += f"\nImage: {image_uploaded_file.name}\nExtracted Text:\n{extracted_text.strip()}\n"
                        else:
                            Document_image_data += f"\nImage: {image_uploaded_file.name}\nExtracted Text: No text found\n"

                    except Exception as e:
                        st.error(f"Error processing {image_uploaded_file.name}: {e}")

            st.markdown("Enter the navigation details (Optional)",
                        unsafe_allow_html=True)
            Navigation_details = st.text_area("Enter Navigation Details", "", key="navigation_details_textarea")

        with st.expander("🔗 Test Management Integration (Optional)", expanded=False):
            st.caption(
                "Connect to Azure Test Plans or Jira to fetch existing test cases and run a gap analysis before generation.")
            tmt_tool = st.radio(
                "Select Test Management Tool",
                options=["None", "Azure Test Plans", "Jira"],
                horizontal=True,
                key="tmt_tool_radio"
            )
            st.session_state.tmt_tool = tmt_tool

            if tmt_tool == "Azure Test Plans":
                col_az1, col_az2 = st.columns(2)
                with col_az1:
                    st.text_input("Organization URL", value="https://dev.azure.com/QE-Practice-team", key="tmt_az_org",
                                  disabled=True)
                with col_az2:
                    st.text_input("Project", value="qe-practice", key="tmt_az_project", disabled=True)

                fetch_type = st.selectbox(
                    "Fetch Type",
                    options=["Test Cases", "Test Plan"],
                    index=0 if st.session_state.tmt_fetch_type == "Test Cases" else 1,
                    key="tmt_fetch_type_select",
                    help="Select 'Test Cases' if you don't have a Test Plans license (trial accounts). Select 'Test Plan' to fetch via a specific plan and suite."
                )
                st.session_state.tmt_fetch_type = fetch_type

                if fetch_type == "Test Cases":
                    if st.button("📥 Fetch Test Cases Directly"):
                        with st.spinner("Fetching test cases from project..."):
                            try:
                                tcs = tmt_utils.get_all_testcases_direct()
                                st.session_state.tmt_existing_tcs = tcs
                                st.session_state.tmt_connected = True
                                st.success(f"✅ Fetched {len(tcs)} test case(s) directly from project.")
                            except Exception as e:
                                st.error(f"❌ Fetch failed: {e}")
                                st.session_state.tmt_connected = False

                else:
                    if st.button("🔌 Connect & Fetch Test Plans"):
                        with st.spinner("Fetching test plans..."):
                            try:
                                st.session_state.tmt_plans = tmt_utils.get_test_plans()
                                st.session_state.tmt_connected = True
                                st.success(f"✅ Connected — {len(st.session_state.tmt_plans)} test plan(s) found.")
                            except Exception as e:
                                st.error(f"❌ Connection failed: {e}")
                                st.session_state.tmt_connected = False

                    if st.session_state.tmt_connected and st.session_state.tmt_plans:
                        plan_options = {p["name"]: p["id"] for p in st.session_state.tmt_plans}
                        selected_plan_name = st.selectbox("Select Test Plan", options=list(plan_options.keys()),
                                                          key="tmt_plan_select")
                        st.session_state.tmt_selected_plan_id = plan_options[selected_plan_name]

                        scope = st.radio("Scope", ["All Suites", "Specific Suite"], horizontal=True,
                                         key="tmt_scope_radio")
                        if scope == "Specific Suite":
                            if st.button("Load Suites"):
                                st.session_state.tmt_suites = tmt_utils.get_test_suites(
                                    st.session_state.tmt_selected_plan_id)
                            if st.session_state.tmt_suites:
                                suite_options = {s["name"]: s["id"] for s in st.session_state.tmt_suites}
                                selected_suite_name = st.selectbox("Select Suite", options=list(suite_options.keys()),
                                                                   key="tmt_suite_select")
                                st.session_state.tmt_selected_suite_id = suite_options[selected_suite_name]
                        else:
                            st.session_state.tmt_selected_suite_id = None

                        if st.button("📥 Fetch Existing Test Cases"):
                            with st.spinner("Fetching existing test cases..."):
                                try:
                                    if st.session_state.tmt_selected_suite_id:
                                        tcs = tmt_utils.get_testcases_from_suite(
                                            st.session_state.tmt_selected_plan_id,
                                            st.session_state.tmt_selected_suite_id
                                        )
                                    else:
                                        tcs = tmt_utils.get_all_testcases_from_plan(
                                            st.session_state.tmt_selected_plan_id
                                        )
                                    st.session_state.tmt_existing_tcs = tcs
                                    st.success(f"✅ Fetched {len(tcs)} existing test case(s).")
                                except Exception as e:
                                    st.error(f"❌ Failed to fetch test cases: {e}")

            elif tmt_tool == "Jira":
                col_j1, col_j2 = st.columns(2)
                with col_j1:
                    jira_project = st.text_input("Jira Project Key (e.g. QA)", key="tmt_jira_project_input")
                    st.session_state.tmt_jira_project_key = jira_project.strip()

                if st.button("📥 Fetch Jira Test Cases"):
                    with st.spinner("Fetching Jira test cases..."):
                        try:
                            tcs = tmt_utils.get_jira_testcases(st.session_state.tmt_jira_project_key)
                            st.session_state.tmt_existing_tcs = tcs
                            st.session_state.tmt_connected = True
                            st.success(f"✅ Fetched {len(tcs)} Jira test case(s).")
                        except Exception as e:
                            st.error(f"❌ Jira fetch failed: {e}")

            if st.session_state.tmt_existing_tcs:
                st.info(
                    f"📋 {len(st.session_state.tmt_existing_tcs)} existing test case(s) loaded — gap analysis will run before generation.")
                with st.expander("Preview existing test cases"):
                    for tc in st.session_state.tmt_existing_tcs[:10]:
                        st.write(f"**{tc['id']}** — {tc['title']}")
                    if len(st.session_state.tmt_existing_tcs) > 10:
                        st.caption(f"...and {len(st.session_state.tmt_existing_tcs) - 10} more")
            else:
                st.caption("No existing test cases loaded — generation will proceed without gap analysis.")

        if st.button("Generate Functional Test Cases"):
            st.session_state.testcase_response = []
            st.session_state.testcases_saved = False
            st.session_state.scenario_response = None
            st.session_state.all_testcases = None
            st.session_state.overall_accuracy = None
            st.session_state.testcase_regeneration = None
            st.session_state.save_testcases = False
            st.session_state.regenerate_clicked = False
            st.session_state.save_regenerated_testcases = False

            if option == 'Recorded_Details':
                if st.session_state.selected_images and prompt:
                    navigation = ', '.join(st.session_state.selected_images)

                    image_data = ""
                    if source == "file":
                        for image_name in st.session_state.selected_images:
                            image_path = os.path.join(page_screenshot_folder, image_name)
                            if os.path.exists(image_path):
                                image = Image.open(image_path)
                                st.image(image, caption=image_name, use_container_width=True)

                                try:
                                    extracted_text = pytesseract.image_to_string(image)
                                    if extracted_text:
                                        image_data += f"\nImage: {image_name}\nExtracted Text: {extracted_text}\n"
                                    else:
                                        image_data += f"\nImage: {image_name}\nExtracted Text: No text found\n"
                                except Exception as e:
                                    st.error(f"Error extracting text from {image_name}: {e}")
                            else:
                                st.error(f"Image not found: {image_name}")

                    elif source == "database":
                        screenshots = db_handler.get_all_screenshots()

                        db_image_map = {f"{s.page_name}_{s.id}": s.image_data for s in screenshots}

                        for image_key in st.session_state.selected_images:
                            if image_key in db_image_map:
                                try:
                                    image = Image.open(io.BytesIO(db_image_map[image_key]))
                                    st.image(image, caption=image_key, use_container_width=True)

                                    extracted_text = pytesseract.image_to_string(image)
                                    if extracted_text:
                                        image_data += f"\nImage: {image_key}\nExtracted Text: {extracted_text}\n"
                                    else:
                                        image_data += f"\nImage: {image_key}\nExtracted Text: No text found\n"
                                except Exception as e:
                                    st.error(f"Error extracting text from {image_key}: {e}")
                            else:
                                st.error(f"Image not found in database: {image_key}")
                    image_prompt = f"""Summarize the following context into a concise and structured format (under 100 lines), preserving key actions, entities, and sequences. The goal is to retain essential meaning for AI understanding, automation, or test case generation. Avoid repetition, and group related items logically. Context: {image_data} """
                    print(image_prompt)
                    image_data_processed = utils.get_queries_from_ai_updated(image_prompt) or image_data
                    print(image_data_processed)
                    if not Action_data:
                        Action_data = None

                    if st.session_state.tmt_existing_tcs:
                        with st.spinner("🔍 Running gap analysis against existing test cases..."):
                            gap_result = utils.analyze_testcase_gaps(
                                st.session_state.tmt_existing_tcs,
                                Action_data,
                                image_data_processed,
                                prompt
                            )
                        st.session_state.gap_analysis_result = gap_result
                        st.session_state.tmt_gap_approved = False
                        st.session_state.tmt_replacement_responses = ""
                        st.session_state.tmt_deletion_notice = []
                        st.session_state.tmt_gen_inputs = {
                            "navigation": navigation,
                            "image_data_processed": image_data_processed,
                            "Action_data": Action_data,
                            "prompt": prompt
                        }
                    else:
                        if model_type == "azureopenai":
                            constructedprompt = utils.generate_pom_from_excel_testcases(
                                "Test_case_generation", navigation, image_data_processed, Action_data, prompt)
                        else:
                            constructedprompt = utils.generate_pom_from_excel_testcases(
                                "Test_case_generation_gemini", navigation, image_data_processed, Action_data, prompt)
                        st.session_state.testcase_response = utils.generate_testcases_with_dynamic_stop(
                            constructedprompt, 15, 5)
                        utils.parse_and_display_testcases_categorywise(st.session_state.testcase_response)

            elif option == 'Documents' and source_type is not None:

                if source_type == "Files" and uploaded_file is not None:
                    extracted_data = utils.extract_text_from_document(uploaded_file, uploaded_file.name)
                elif source_type == "Azure Board" and st.session_state.azure_workitem_id is not None:
                    try:
                        exists, message = tmt_utils.validate_work_item_exists(st.session_state.azure_workitem_id)
                        if exists:
                            extracted_data = tmt_utils.fetch_workitem_detail(st.session_state.azure_workitem_id)
                        else:
                            st.error(message)
                            st.error("Please enter valid workitem")
                            st.stop()
                    except Exception as e:
                        st.error("Invalid Work Item")
                elif source_type == "Jira" and st.session_state.jira_workitem_id is not None:
                    try:
                        exists, message = tmt_utils.validate_work_item_exists(st.session_state.jira_workitem_id)
                        if exists:

                            extracted_data = tmt_utils.fetch_workitem_detail(st.session_state.jira_workitem_id)
                        else:
                            st.error(message)
                            st.error("Please enter valid workitem")
                            st.stop()
                    except Exception as e:
                        st.error("Invalid Work Item")
                if source_type == "Files" and pbi_mode == "Power BI":
                    if not wireframe_files:
                        st.warning("⚠️ Please upload at least one wireframe image for Power BI test case generation.")
                        st.stop()

                    mime_map = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
                                "bmp": "image/bmp", "webp": "image/webp"}
                    wireframe_payload = []
                    wireframe_ocr = ""
                    for wf in wireframe_files:
                        raw = wf.getvalue()
                        ext = os.path.splitext(wf.name)[1].lower().lstrip(".")
                        wf_mime = mime_map.get(ext, "image/png")
                        wf_b64 = base64.b64encode(raw).decode()
                        wireframe_payload.append((wf_mime, wf_b64))
                        try:
                            wf_img = Image.open(io.BytesIO(raw))
                            st.image(wf_img, caption=wf.name, use_container_width=True)
                        except Exception as e:
                            print(f"[WARN] Could not preview wireframe {wf.name}: {e}")
                        with st.spinner(f"🖼️ Reading wireframe '{wf.name}' with vision model..."):
                            wireframe_ocr += utils.extract_wireframe_details_via_llm(
                                wf_b64, wf_mime, wf.name)

                    st.session_state.testcase_response = []
                    st.session_state.scenario_response = []
                    st.session_state.all_testcases = []

                    constructedprompt = utils.generate_excel_testcases_with_document(
                        "Test_case_generation_pbi", extracted_data, wireframe_ocr, Navigation_details)
                    with st.spinner("🔍 Analyzing wireframe & generating Power BI validation test cases..."):
                        st.session_state.testcase_response = utils.generate_testcases_with_dynamic_stop(
                            constructedprompt, 20, 5, image_payload=wireframe_payload)
                    utils.parse_and_display_testcases_categorywise(st.session_state.testcase_response)
                else:
                    image_prompt = f"""Summarize the following context into a concise and structured format (under 100 lines), preserving key actions, entities, and sequences. The goal is to retain essential meaning for AI understanding, automation, or test case generation. Avoid repetition, and group related items logically. Context: {Document_image_data} """
                    if model_type == "azureopenai":
                        Document_image_data_processed = utils.get_queries_from_ai_updated(image_prompt)
                    else:
                        Document_image_data_processed = utils.llm_pepgenx(image_prompt)
                    print(Document_image_data_processed)

                    st.session_state.testcase_response = []
                    st.session_state.scenario_response = []
                    st.session_state.all_testcases = []
                    if model_type == "azureopenai":
                        print("Model Type is AzureOpenAi")
                        constructedprompt = utils.generate_excel_testcases_with_document(
                            "Test_case_generation_document",
                            extracted_data, Document_image_data_processed, Navigation_details)
                    else:
                        print("Model Type is gimini")
                        constructedprompt = utils.generate_excel_testcases_with_document(
                            "Test_case_generation_document_gemini",
                            extracted_data)
                    st.session_state.testcase_response = utils.generate_testcases_with_dynamic_stop(constructedprompt,
                                                                                                    120, 5)
                    utils.parse_and_display_testcases_categorywise(st.session_state.testcase_response)

        if st.session_state.gap_analysis_result and not st.session_state.tmt_gap_approved:
            gap_result = st.session_state.gap_analysis_result
            st.markdown("### 📊 Gap Analysis Result")
            col_g1, col_g2, col_g3 = st.columns(3)
            col_g1.metric("🆕 New Scenarios", len(gap_result["new"]))
            col_g2.metric("✏️ Need Replacement", len(gap_result["update"]))
            col_g3.metric("✅ Already Covered", len(gap_result["skip"]))

            if gap_result["new"]:
                with st.expander("🆕 New scenarios to generate"):
                    for i, scenario in enumerate(gap_result["new"], 1):
                        st.write(f"{i}. {scenario}")

            if gap_result["update"]:
                with st.expander("✏️ Test cases to be replaced (you will be asked to delete originals manually)"):
                    for item in gap_result["update"]:
                        st.write(f"**{item['id']}** — {item['title']}")
                        st.caption(f"Reason: {item['reason']}")

            if st.button("✅ Approve & Generate"):
                st.session_state.tmt_gap_approved = True
                st.rerun()

        if st.session_state.tmt_gap_approved and st.session_state.gap_analysis_result and not st.session_state.testcase_response:
            gap_result = st.session_state.gap_analysis_result
            inputs = st.session_state.tmt_gen_inputs
            navigation = inputs.get("navigation", "")
            image_data_processed = inputs.get("image_data_processed", "")
            Action_data = inputs.get("Action_data", None)
            prompt = inputs.get("prompt", "")

            if gap_result["new"]:
                with st.spinner(f"Generating {len(gap_result['new'])} new test case(s)..."):
                    st.session_state.testcase_response = utils.generate_targeted_testcases(
                        scenarios=gap_result["new"],
                        action_data=Action_data,
                        image_data=image_data_processed,
                        requirements=prompt
                    )
                st.success(f"✅ {len(gap_result['new'])} new test case(s) generated.")
            else:
                st.session_state.testcase_response = ""
                st.info("No new scenarios from gap analysis — only replacements will be generated.")

            if gap_result["update"]:
                st.info(f"Generating {len(gap_result['update'])} replacement test case(s)...")
                replacement_combined = ""
                deletion_notice = []
                for item in gap_result["update"]:
                    with st.spinner(f"Replacing: {item['title']}..."):
                        replacement = utils.generate_replacement_testcase(
                            title=item["title"],
                            reason=item["reason"],
                            action_data=Action_data,
                            image_data=image_data_processed,
                            requirements=prompt
                        )
                    if replacement:
                        replacement_combined += "\n" + replacement
                        deletion_notice.append(item)
                        st.success(f"✅ Replacement generated for: {item['title']}")
                    else:
                        st.warning(f"⚠️ Could not generate replacement for: {item['title']}")
                st.session_state.tmt_replacement_responses = replacement_combined
                st.session_state.tmt_deletion_notice = deletion_notice

                if replacement_combined:
                    st.session_state.testcase_response = (
                            st.session_state.testcase_response + "\n" + replacement_combined
                    )

            utils.parse_and_display_testcases_categorywise(st.session_state.testcase_response)

        if st.session_state.testcase_response:
            st.session_state.save_testcases = True
        if st.session_state.save_testcases and st.button("💾 Save test cases"):
            utils.covert_response_to_testcases_single_file(st.session_state.testcase_response, Test_case_collection)
            st.session_state.excel_path = utils.covert_response_to_testcases_single_sheet(
                st.session_state.testcase_response, Test_case_collection)
            st.session_state.testcases_saved = True
            st.session_state.show_popup = True
            st.session_state.show_form = False

        if st.session_state.get("testcases_saved") and st.session_state.tmt_deletion_notice:
            st.warning(
                "⚠️ The following existing test cases were replaced by newly generated ones. Please **delete them manually** from Azure DevOps:")
            for item in st.session_state.tmt_deletion_notice:
                st.markdown(f"- **{item['id']}** | {item['title']} — _{item['reason']}_")

        if st.session_state.get("testcases_saved") and st.session_state.tmt_existing_tcs:
            gap = st.session_state.gap_analysis_result or {}
            new_count = len(gap.get("new", []))
            update_count = len(gap.get("update", []))

            with st.expander("📤 Push to Azure DevOps", expanded=True):
                st.markdown(
                    f"Ready to push: **{new_count} new** test cases | "
                    f"**{update_count} replacement** test cases as individual Azure DevOps Test Case work items."
                )

                user_story_id = st.text_input(
                    "User Story ID (optional) — leave blank to create test cases without a parent",
                    value="",
                    key="tmt_push_userstory_id"
                )

                if st.button("📤 Push Individual Test Cases to Azure DevOps"):
                    parent_id = user_story_id.strip() or None

                    if parent_id:
                        exists, message = tmt_utils.validate_work_item_exists(parent_id)
                        if not exists:
                            st.error(f"❌ {message}")
                            st.stop()

                    rows = utils.parse_testcases_from_markdown(st.session_state.testcase_response)

                    tc_groups = {}
                    current_name = None
                    for row in rows:
                        name = row["name"].strip()
                        if name:
                            current_name = name
                            tc_groups[current_name] = []
                        if current_name:
                            tc_groups[current_name].append(row)

                    if not tc_groups:
                        st.warning("⚠️ No test cases found to push.")
                    else:
                        push_errors = []
                        created_ids = []
                        progress = st.progress(0)
                        total = len(tc_groups)

                        for i, (tc_title, tc_rows) in enumerate(tc_groups.items(), 1):
                            try:
                                steps_xml = tmt_utils.build_steps_xml(tc_rows)
                                wi_id = tmt_utils.create_testcase_with_steps(
                                    title=tc_title,
                                    steps_xml=steps_xml,
                                    parent_id=parent_id
                                )
                                if wi_id:
                                    created_ids.append(wi_id)
                                    st.write(f"✅ Created: **{tc_title}** — Work Item ID: {wi_id}")
                                else:
                                    push_errors.append(f"Failed to create: {tc_title}")
                            except Exception as e:
                                push_errors.append(f"{tc_title}: {e}")
                            progress.progress(i / total)

                        st.success(f"✅ {len(created_ids)} of {total} test cases pushed to Azure DevOps.")
                        if push_errors:
                            for err in push_errors:
                                st.error(err)

        if st.session_state.get("testcases_saved") and not st.session_state.tmt_existing_tcs:
            if option == "Documents" and source_type == "Azure Board":
                if st.button("📤 Export test cases to azure Board"):
                    try:
                        sub_work_item = tmt_utils.create_test_case(st.session_state.azure_workitem_id)
                        tmt_utils.upload_attachment_to_testcase(sub_work_item, st.session_state.excel_path)
                        st.success(f"✅ Test cases were successfully exported!\n\n📄 Work Item ID: **{sub_work_item}**")
                    except Exception as e:
                        st.error("Invalid Work Item")
                    st.session_state.save_testcases = False

            elif option in ("Documents", "Recorded_Details"):
                source_key = source_type if option == "Documents" else "Recorded"
                if st.session_state.show_popup and not st.session_state.show_form:
                    st.write("**Do you want to export the generated testcases?**")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Yes", key=f"export_yes_{source_key}"):
                            st.session_state.show_popup = False
                            st.session_state.show_form = True
                    with col2:
                        if st.button("No", key=f"export_no_{source_key}"):
                            st.session_state.show_popup = False
                            st.session_state.show_form = False
                            st.session_state.xpath_for_new_page_user_info = True
                            st.rerun()

                if st.session_state.show_form:
                    st.info("Enter Work Item ID (numeric, optional)")
                    workitem = st.text_input("Work Item ID", value=st.session_state.azure_workitem_id,
                                             key="azure_workitem_text")
                    st.session_state.azure_workitem_id = workitem.strip()
                    if workitem and not workitem.isdigit():
                        st.warning("Work Item ID typically numeric — ensure it's correct.")
                    if st.button("📤 Export test cases to Azure"):
                        try:
                            if st.session_state.azure_workitem_id:
                                exists, message = tmt_utils.validate_work_item_exists(
                                    st.session_state.azure_workitem_id)
                                if exists:
                                    child_id = tmt_utils.create_test_case(st.session_state.azure_workitem_id)
                                else:
                                    st.error(f"{message} — Please enter a valid Work Item.")
                                    st.stop()
                            else:
                                child_id = tmt_utils.create_direct_test_case()
                            tmt_utils.upload_attachment_to_testcase(child_id, st.session_state.excel_path)
                            st.success(f"✅ Test cases exported — Work Item ID: **{child_id}**")
                        except Exception as e:
                            st.error(f"Export failed: {e}")

if _tool == "testdata":
    with _workspace("🧪 Action-Driven Test Data Generator"):
        st.title("Enhanced Test Data Generator (Based on Action File)")
        st.session_state.test_data_action_data = ""
        st.session_state.test_files_content = ""
        if source == "file":
            st.session_state.test_files_content = utils.select_and_read_text_files_xpath(
                "test data generation -Test Cases files", Test_case_collection)
            st.session_state.test_data_action_data = utils.select_and_read_text_files_xpath(
                "test data generation -Recorded actions files", Action_collection)
        elif source == "database":
            all_testcase_files = db_handler.get_all_testcasefile_names()
            selected_testcase_files = st.multiselect("Select saved testcase files from database", all_testcase_files)
            if selected_testcase_files:
                merged_testcase_content = ""

                for file in selected_testcase_files:
                    content = db_handler.get_action_content_by_name(file, "testcase")
                    if content:
                        merged_testcase_content += f"\n### {file} ###\n{content}\n"
                    else:
                        st.session_state.failed_files.append(file)

                st.session_state.test_files_content = merged_testcase_content
                if st.session_state.failed_files:
                    st.warning("⚠️ Could not load content for the following files:\n- " + "\n- ".join(
                        st.session_state.failed_files))
            all_files = db_handler.get_all_action_names()
            selected_files = st.multiselect("Select saved action files from database for pagefile",
                                            all_files)
            if selected_files:
                merged_content = ""

                for file in selected_files:
                    content = db_handler.get_action_content_by_name(file, "action")
                    if content:
                        merged_content += f"\n### {file} ###\n{content}\n"
                    else:
                        st.warning(f"⚠️ Could not load content for: {file}")
                st.session_state.test_data_action_data = merged_content

        st.markdown("**Enter the additional information or sample data** <span style='color:red;'>*</span>",
                    unsafe_allow_html=True)
        st.session_state.test_data_addition_info = st.text_area("Optional: Provide additional test data", "",
                                                                key="user_data_textarea")
        if st.button("Generate Functional Test Data"):
            if st.session_state.test_data_action_data:
                constructed_prompt = utils.generate_promot_test_data_generator("test_data",
                                                                               st.session_state.test_data_action_data,
                                                                               st.session_state.test_files_content,
                                                                               st.session_state.test_data_addition_info)
                st.session_state.test_data_llm_response = utils.get_queries_from_ai_updated(constructed_prompt)
                st.success("Test data generated for given input")
            else:
                st.error("Please select action file")
        if st.session_state.test_data_llm_response:
            test_data_file_name = st.text_input("Enter the testdata file Name:")
            if st.button("Save Test Data"):
                if test_data_file_name:
                    utils.save_test_data_into_excel(st.session_state.test_data_llm_response, test_data_file_name,
                                                    test_data_folder)
                    st.success("Test data generated successfully")

                else:
                    st.error("Please select test data file name")

if _tool == "pom":
    with _workspace("🔎 Locators / POM File Generator"):
        st.title("Locator Generator for Visible Elements")

        selected_app = st.multiselect(
            "Select application type:",
            ["PowerBi", "Web"],
            default=["Web"])
        tags_placeholder = st.empty()
        if "Web" in selected_app:

            selected_tags = tags_placeholder.multiselect(
                "Select element types to extract:",
                xpath_tag_keys,
                default=st.session_state.selected_tags,
                key="selected_tags_multiselect"
            )
        else:
            tags_placeholder.empty()
            selected_tags = []

        st.session_state.selected_app = selected_app
        st.markdown("<a name='top-button'></a>", unsafe_allow_html=True)
        collect_clicked = st.button("Collecting Elements", key="collect_btn")

        if collect_clicked:
            st.session_state.selected_tags = selected_tags
            handles = st.session_state.driver.window_handles
            if len(handles) > 1:
                st.session_state.driver.switch_to.window(handles[-1])

            for key in ["prompt_response", "selected_xpaths", "prompt_response_page_file", "show_popup", "show_form"]:
                if key in st.session_state:
                    st.session_state[key] = "" if "response" in key else False

            formatted_summary = None
            st.session_state.selected_xpaths = []
            st.session_state.prompt_response = ""
            page_identifier = st.session_state.driver.current_url
            if "PowerBi" in selected_app:
                formatted_summary = utils.get_visible_element_powerBi(st.session_state.driver, page_identifier)
            if "Web" in selected_app:
                formatted_summary = utils.get_visible_element_iframe(st.session_state.driver, page_identifier,
                                                                     st.session_state.selected_tags)
            if formatted_summary is None:
                formatted_summary = []
            if formatted_summary:
                if "PowerBi" in selected_app:
                    st.session_state.prompt_response = utils.get_queries_from_ai("PowerBi", formatted_summary)
                    print("OPen Ai response" + st.session_state.prompt_response)
                if "Web" in selected_app:
                    st.session_state.prompt_response = utils.get_queries_from_ai("Web", formatted_summary)
                    print("OPen Ai response" + st.session_state.prompt_response)
            else:
                st.info("No elements found in selected tag")
        if st.session_state.prompt_response:
            xpath_dict = utils.filter_duplicate_xpaths(
                utils.selecting_xpath(st.session_state.prompt_response))
            print(xpath_dict)
            st.title("Select XPath Expressions to Add to Excel")
            xpath_output_placeholder = st.empty()
            with xpath_output_placeholder.container():
                st.session_state.selected_xpaths = utils.adding_xpath_user_view(xpath_dict)
            page_name = st.text_input("Enter the Page Name:")
            if st.button("Add Selected XPaths to Excel"):
                if page_name and st.session_state.selected_xpaths:
                    print("going inside add excel")
                    print(st.session_state.selected_xpaths)
                    if st.session_state.selected_xpaths:
                        print("going inside add excel")
                        utils.adding_selected_xapth_excel(page_name)
                        st.session_state.show_popup = True
                        st.session_state.show_form = False
                elif not st.session_state.selected_xpaths:
                    st.error("Select at-least one xpath to add")
                elif not page_name:
                    st.error("Enter the Page name to add the selected xpath")

            if st.session_state.show_popup and not st.session_state.show_form:
                st.write("**Do you want to generate the page file?**")

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Yes"):
                        st.session_state.show_popup = False
                        st.session_state.show_form = True

                with col2:
                    if st.button("No"):
                        for _ in range(2):
                            st.session_state.show_popup = False
                            st.session_state.show_form = False
                            st.session_state.prompt_response = ""
                            xpath_output_placeholder = st.empty()
                            st.session_state.xpath_for_new_page_user_info = True
                            st.rerun()
                        st.info(
                            "Page file generation skipped..Please change to the new page in the browser and click 'Collecting Elements' again.")
            if st.session_state.show_form:
                st.header("Generating Page File")
                page_name = st.text_input("Enter Page Name (same as xpath details)", value=page_name)
                language = st.selectbox("Select Language",
                                        ["Java-Selenium", "Java-Playwright", "Python-Selenium", "Python-Playwright"])
                Action_data = ""
                if source == "file":
                    Action_data = utils.select_and_read_text_files_xpath("xpath", Action_collection)
                elif source == "database":
                    all_files = db_handler.get_all_action_names()
                    selected_files = st.multiselect("Select saved action files from database for pagefile",
                                                    all_files)

                    if selected_files:
                        merged_content = ""

                        for file in selected_files:
                            content = db_handler.get_action_content_by_name(file, "action")
                            if content:
                                merged_content += f"\n### {file} ###\n{content}\n"
                            else:
                                st.warning(f"⚠️ Could not load content for: {file}")
                        Action_data = merged_content

                if st.button("Generate Page File"):
                    st.session_state.prompt_response_page_file = ""
                    Prompt = utils.generate_pom_from_excel_with_action(language, page_name, language,
                                                                       Action_data)
                    st.session_state.prompt_response_page_file = utils.get_queries_from_ai("Page_File", Prompt)
                    st.subheader("Generated Page Class")
                    if source == "file":
                        utils.create_java_file(page_name, language, st.session_state.prompt_response_page_file)
                        st.success(f"Page file generated for '{page_name}' in '{language}' language.")
                        st.session_state.xpath_for_new_page = True
                    elif source == "database":
                        db_handler.save_pagefile_to_db(page_name, st.session_state.prompt_response_page_file,
                                                       get_update_user(), language)
                        st.success(f"Page file save in database for '{page_name}' in '{language}' language.")
                        st.session_state.xpath_for_new_page = True

        if st.session_state.xpath_for_new_page and st.button("Continue for New Page"):
            for _ in range(2):
                xpath_output_placeholder = st.empty()
                st.session_state.prompt_response_page_file = ""
                st.session_state.prompt_response = ""
                st.session_state.selected_xpaths = []
                st.session_state.show_popup = False
                st.session_state.show_form = False
                st.session_state.xpath_for_new_page = False
                xpath_output_placeholder.empty()
                st.session_state.xpath_for_new_page_user_info = True
                st.rerun()

        if st.session_state.xpath_for_new_page_user_info:
            st.info(
                "Please change to the new page in the browser and click 'Collecting Elements' again.")
            st.session_state.xpath_for_new_page_user_info = False

if _tool == "scripts":
    st.session_state.failed_files = []
    with _workspace("🧾 Test Automation Script Generator"):
        st.title("Automation Script Generator using page file and test cases")
        test_file_name = st.text_input("Enter the test File Name")
        test_file_language = st.selectbox("Select Language for test file",
                                          ["Java-Selenium", "Java-Playwright", "Python-Selenium", "Python-Playwright",
                                           "Desktop & Web[python-Selenium]", "UTAM-JavaScript"])
        if test_file_language != "Desktop & Web[python-Selenium]":
            page_files_content = ""
            test_files_content = ""
            Action_data = ""
            if source == "file":
                page_files_content = utils.select_and_read_text_files_xpath("page_test", Page_collection)
                test_files_content = utils.select_and_read_text_files_xpath("testcase_test", Test_case_collection)
                Action_data = utils.select_and_read_text_files_xpath("recorded action (Optional)", Action_collection)
            elif source == "database":
                all_page_files = db_handler.get_all_pagefile_names()
                all_testcase_files = db_handler.get_all_testcasefile_names()
                selected_page_files = st.multiselect("Select saved page files from database", all_page_files)
                selected_testcase_files = st.multiselect("Select saved testcase files from database",
                                                         all_testcase_files)
                if selected_page_files:
                    merged_page_content = ""

                    for file in selected_page_files:
                        content = db_handler.get_action_content_by_name(file, "page")
                        if content:
                            merged_page_content += f"\n### {file} ###\n{content}\n"
                        else:
                            st.session_state.failed_files.append(file)
                        if st.session_state.failed_files:
                            st.warning("⚠️ Could not load content for the following files:\n- " + "\n- ".join(
                                st.session_state.failed_files))
                    page_files_content = merged_page_content
                if selected_testcase_files:
                    merged_testcase_content = ""

                    for file in selected_testcase_files:
                        content = db_handler.get_action_content_by_name(file, "testcase")
                        if content:
                            merged_testcase_content += f"\n### {file} ###\n{content}\n"
                        else:
                            st.session_state.failed_files.append(file)

                    test_files_content = merged_testcase_content
                    if st.session_state.failed_files:
                        st.warning("⚠️ Could not load content for the following files:\n- " + "\n- ".join(
                            st.session_state.failed_files))
                all_files = db_handler.get_all_action_names()
                selected_files = st.multiselect("Select saved action files from database for Testscript (optional)",
                                                all_files)

                if selected_files:
                    merged_content = ""

                    for file in selected_files:
                        content = db_handler.get_action_content_by_name(file, "action")
                        if content:
                            merged_content += f"\n### {file} ###\n{content}\n"
                        else:
                            st.warning(f"⚠️ Could not load content for: {file}")
                    Action_data = merged_content
            if st.button("Generate_Test_Script", key="gen_script_main"):
                Lang_lib = "Test-" + test_file_language
                Prompt = utils.generate_test_script(Lang_lib, test_file_language, page_files_content,
                                                    test_files_content, Action_data)
                print("**********Script validator prompt************" + Prompt)
                test_script_response = utils.get_queries_from_ai_updated(Prompt)
                st.session_state.generated_test_script = test_script_response
                st.session_state.script_gen_inputs = {
                    "test_file_language": test_file_language,
                    "page_files_content": page_files_content,
                    "test_files_content": test_files_content,
                    "Action_data": Action_data,
                    "source": source,
                    "flow": "standard"
                }
                st.session_state.script_editor_version = st.session_state.get("script_editor_version", 0) + 1
                st.rerun()
        else:
            test_windows_application_path = st.text_input("Enter the test_windows_application_path ")
            Action_data = ""
            if source == "file":
                Action_data = utils.select_and_read_text_files_xpath("recorded action",
                                                                     Action_collection)
            elif source == "database":
                all_files = db_handler.get_all_action_names()
                selected_files = st.multiselect("Select saved action files from database for Testscript (optional)",
                                                all_files)

                if selected_files:
                    merged_content = ""

                    for file in selected_files:
                        content = db_handler.get_action_content_by_name(file, "action")
                        if content:
                            merged_content += f"\n### {file} ###\n{content}\n"
                        else:
                            st.warning(f"⚠️ Could not load content for: {file}")
                    Action_data = merged_content
            if st.button("Generate_Test_Script", key="gen_script_desktop"):
                Lang_lib = "Test-" + test_file_language
                Prompt = utils.generate_test_script_windows_web(Lang_lib, Action_data, test_windows_application_path)
                test_script_response = utils.get_queries_from_ai_updated(Prompt)
                st.session_state.generated_test_script = test_script_response
                st.session_state.script_gen_inputs = {
                    "test_file_language": test_file_language,
                    "page_files_content": "",
                    "test_files_content": "",
                    "Action_data": Action_data,
                    "source": source,
                    "flow": "desktop"
                }
                st.session_state.script_editor_version = st.session_state.get("script_editor_version", 0) + 1
                st.rerun()
        if st.session_state.get("generated_test_script"):
            ver = st.session_state.get("script_editor_version", 0)
            _lang = st.session_state.script_gen_inputs.get("test_file_language", "")
            _code_lang = "java" if "java" in _lang.lower() else (
                "javascript" if "javascript" in _lang.lower() else "python")

            st.subheader("📝 Generated Script")
            st.code(st.session_state.generated_test_script, language=_code_lang)

            with st.expander("✏️ Edit Script (expand to modify before saving)"):
                edited_script = st.text_area(
                    "Edit the script here:",
                    value=st.session_state.generated_test_script,
                    key=f"script_editor_{ver}",
                    height=500
                )

            st.subheader("💬 Review Feedback")
            review_details = st.text_area(
                "Enter specific review details, issues, or requirements (optional):",
                value="",
                key=f"script_review_{ver}",
                height=150,
                placeholder="e.g., 'TC02 step 3 is missing', 'Add wait for page load after login', ..."
            )
            col_save, col_regen = st.columns(2)
            with col_save:
                if st.button("💾 Save Generated Script", key="save_script_btn"):
                    final_script = st.session_state.get(f"script_editor_{ver}", st.session_state.generated_test_script)
                    gen_source = st.session_state.script_gen_inputs.get("source", source)
                    if gen_source == "file":
                        utils.create_test_file(Test_file_generator, test_file_name, test_file_language, final_script)
                    elif gen_source == "database":
                        db_handler.save_testfile_to_db(test_file_name, final_script, get_update_user(),
                                                       test_file_language)
                    st.success("✅ Script saved successfully!")
                    st.session_state.generated_test_script = None
            with col_regen:
                if st.button("🔄 Regenerate Script", key="regen_script_btn"):
                    current_script = st.session_state.get(f"script_editor_{ver}",
                                                          st.session_state.generated_test_script)
                    current_review = st.session_state.get(f"script_review_{ver}", "")
                    inputs = st.session_state.script_gen_inputs
                    regen_prompt = utils.generate_code_review_prompt(
                        inputs["test_file_language"],
                        inputs.get("page_files_content", ""),
                        inputs.get("test_files_content", ""),
                        inputs.get("Action_data", ""),
                        current_script,
                        current_review
                    )
                    regenerated_script = utils.get_queries_from_ai_updated(regen_prompt)
                    st.session_state.generated_test_script = regenerated_script
                    st.session_state.script_editor_version = ver + 1
                    st.rerun()

if _tool == "repo":
    with _workspace("⚙️ Source Code / Automation Bridge"):
        st.title("Upload code to Repository")
        if source == "file":
            pytest_files = utils.select_and_read_text_files_xpath("test_file", utils.Test_file_generator)
            pom_files = utils.select_and_read_text_files_xpath("pom_file", utils.Page_file_generator)
        elif source == "database":
            all_page_files = db_handler.get_all_pagefile_names()
            all_test_files = db_handler.get_all_testfile_names()
            selected_page_files = st.multiselect("Select saved page files from database to push", all_page_files)
            selected_test_files = st.multiselect("Select saved testcase files from database to push", all_test_files)
            temp_dir_page = db_handler.prepare_selected_files_for_github(selected_page_files)
            temp_dir_test = db_handler.prepare_selected_files_for_github(selected_test_files)
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
                    for file_name, content in pom_files.items():
                        pom_dest_path = f"{repo_pom_name.strip('/')}/{file_name}"
                        utils.push_file_to_gitlab(pom_dest_path, content, repo, branch)

                    for file_name, content in pytest_files.items():
                        pytest_dest_path = f"{repo_pytest_name.strip('/')}/{file_name}"
                        utils.push_file_to_gitlab(pytest_dest_path, content, repo, branch)
                elif source == "database":
                    if temp_dir_page and os.path.isdir(temp_dir_page):
                        for file_name in os.listdir(temp_dir_page):
                            file_path = os.path.join(temp_dir_page, file_name)
                            with open(file_path, "r", encoding="utf-8") as f:
                                content = f.read()
                            pom_dest_path = f"{repo_pom_name.strip('/')}/{file_name}"
                            utils.push_file_to_gitlab(pom_dest_path, content, repo, branch)

                    if temp_dir_test and os.path.isdir(temp_dir_test):
                        for file_name in os.listdir(temp_dir_test):
                            file_path = os.path.join(temp_dir_test, file_name)
                            with open(file_path, "r", encoding="utf-8") as f:
                                content = f.read()
                            pytest_dest_path = f"{repo_pytest_name.strip('/')}/{file_name}"
                            utils.push_file_to_gitlab(pytest_dest_path, content, repo, branch)

                    shutil.rmtree(temp_dir_page, ignore_errors=True)
                    shutil.rmtree(temp_dir_test, ignore_errors=True)

                    st.success("✅ Selected database files pushed to GitHub and temp files deleted.")
            else:
                st.warning("⚠️ Please enter both folder names in the repo.")

if _tool == "artifacts":
    if source == "database":
        with _workspace("📥 Download Artifacts"):
            st.title("Download Artifacts from Database")
            file_type = st.selectbox("Select FileType",
                                     ["Recorded_Action_file", "Page_file", "Test_file", "Testcase_file"])

            selected_files = []

            if file_type == "Recorded_Action_file":
                files = db_handler.get_all_action_names()
                selected_files = st.multiselect("Select Actions", files)
            elif file_type == "Page_file":
                files = db_handler.get_all_pagefile_names()
                selected_files = st.multiselect("Select Page Files", files)
            elif file_type == "Test_file":
                files = db_handler.get_all_testfile_names()
                selected_files = st.multiselect("Select Test Files", files)
            elif file_type == "Testcase_file":
                files = db_handler.get_all_testcasefile_names()
                selected_files = st.multiselect("Select Testcase Files", files)

            if st.button("📦 Download Files"):
                if selected_files:
                    zip_bytes = db_handler.download_files_from_database(selected_files, file_type)
                    if zip_bytes:
                        st.download_button(
                            label="⬇️ Download ZIP",
                            data=zip_bytes,
                            file_name="artifacts.zip",
                            mime="application/zip"
                        )
                        st.success(f"✅ Prepared {len(selected_files)} files for download.")
                    else:
                        st.warning("⚠️ Could not prepare the ZIP.")
                else:
                    st.warning("⚠️ Please select at least one file.")

if _tool == "execute":
    with _workspace("🚀 Test Execution & Allure Reporting"):
        st.title("Execute Generated Test Scripts and View Allure Reports")

        if source == "file":
            test_files = [f for f in os.listdir(Test_file_generator) if f.endswith('.py')]
            selected_file = st.selectbox("Select Test Script to Execute", test_files,
                                         key="test_file_select") if test_files else None
        elif source == "database":
            all_test_files = db_handler.get_all_testfile_names()
            selected_file = st.selectbox("Select Test Script to Execute", all_test_files,
                                         key="test_file_select") if all_test_files else None

        if selected_file:
            if st.button("Run Test Script"):
                if source == "file":
                    test_path = os.path.join(Test_file_generator, selected_file)
                elif source == "database":
                    content = db_handler.get_action_content_by_name(selected_file, "testfile")
                    if content:
                        temp_test_file = os.path.join(current_path, f"temp_{selected_file}.py")
                        with open(temp_test_file, "w") as f:
                            f.write(content)
                        test_path = temp_test_file
                    else:
                        st.error("Could not load test file from database.")
                        test_path = None
                if test_path:
                    command = f"python -m pytest -q --alluredir=allure-results {test_path}"
                    try:
                        result = subprocess.run(command, shell=True, capture_output=True, text=True, cwd=current_path)
                        st.session_state.test_execution_status = result.stdout + "\n" + result.stderr
                        if result.returncode == 0:
                            st.success("✅ Test execution completed successfully.")
                        else:
                            st.warning("⚠️ Test execution completed with issues.")
                        st.text_area("Execution Output", st.session_state.test_execution_status, height=200)
                        if source == "database":
                            if 'temp_test_file' in locals():
                                os.remove(temp_test_file)
                    except Exception as e:
                        st.error(f"❌ Error running test: {e}")

            if st.button("View Allure Report"):
                command = "allure serve allure-results"
                try:
                    subprocess.Popen(command, shell=True, cwd=current_path)
                    st.success("✅ Allure report server started. The report should open automatically in your browser.")
                except Exception as e:
                    st.error(f"❌ Error starting Allure server: {e}")
        else:
            st.info("ℹ️ No test scripts available.")

# ==============================================================================
# PERFORMANCE TESTING (JMETER / K6) INTEGRATED AGENT TOOL
# ==============================================================================
if _tool == "performance":
    with _workspace("📊 Performance Test Script Generator & Execution Engine"):
        st.title("Performance Test Script Generator & Execution Engine")

        perf_tool_choice = st.radio(
            "Select Performance Testing Tool",
            ["JMeter", "k6"],
            index=0, horizontal=True, key="perf_tool_choice_radio"
        )

        st.divider()

        # ── JMETER SECTION ──────────────────────────────────────────────────
        if perf_tool_choice == "JMeter":
            jmx_source_mode = st.radio(
                "Select Script Sourcing Method",
                [
                    "Upload Existing JMX Script File",
                    "Generate without AI -Rule based - HAR/Excel/Swagger",
                    "Generate with AI via Action File Blueprint"
                ],
                index=1, horizontal=True, key="jmx_source_mode_radio_split"
            )

            # ------------------------------------------------------------------
            # NEW OPTION: NO-LLM RULE-BASED JMX GENERATION ENGINE
            # ------------------------------------------------------------------
            if jmx_source_mode == "Generate without AI -Rule based - HAR/Excel/Swagger":
                st.markdown("##### ⚡ Direct Rule-Based JMX Generator (Deterministic / No-LLM)")

                input_type = st.radio(
                    "Select Input Source Format:",
                    ["DevTools HAR File (.har)", "Excel File", "Swagger / OpenAPI JSON"],
                    horizontal=True, key="nollm_input_type"
                )

                col_prefix, col_cookie = st.columns(2)
                with col_prefix:
                    scenario_prefix = st.text_input("Scenario / Feature Prefix:", value="Perf_Scenario1",
                                                    key="nollm_prefix")
                    deduct_dupes = st.checkbox("Deduct Duplicate Endpoints", value=True, key="nollm_dupes")
                    exclude_static_assets = st.checkbox("Exclude Static Assets (.css, .js, images)", value=True,
                                                        key="nollm_static")
                with col_cookie:
                    active_cookie = st.text_area("Paste Active Session Cookie String (Optional):", height=80,
                                                 key="nollm_cookie")

                parsed_api_list = []

                if input_type == "DevTools HAR File (.har)":
                    uploaded_har = st.file_uploader("Upload DevTools HAR File", type=["har", "json"],
                                                    key="nollm_har_uploader")
                    if uploaded_har:
                        har_data = json.load(uploaded_har)
                        parsed_api_list = jmx_engine.parse_har_file(
                            har_data,
                            user_cookie=active_cookie,
                            scenario_prefix=scenario_prefix,
                            deduct_duplicates=deduct_dupes,
                            exclude_static=exclude_static_assets
                        )
                        st.success(f"✅ Extracted {len(parsed_api_list)} API endpoints from HAR log!")

                elif input_type == "Excel File":
                    uploaded_excel = st.file_uploader("Upload API Inventory Excel", type=["xlsx", "xls"],
                                                      key="nollm_excel_uploader")
                    if uploaded_excel:
                        df_excel = pd.read_excel(uploaded_excel)
                        for idx, row in df_excel.iterrows():
                            name = row.get("Test_Case_Name") or row.get("Name") or f"API_{idx + 1}"
                            method = row.get("httpMethod") or row.get("Method") or "GET"
                            base_url = row.get("Source_BaseURL") or row.get("baseUrl") or row.get(
                                "Domain") or "${BASE_URL}"
                            endpoint = row.get("endPoint") or row.get("Path") or "/"
                            headers_raw = row.get("headers") or row.get("Headers")
                            body = row.get("BodyFormat") or row.get("Body")

                            parsed_headers = {}
                            if pd.notna(headers_raw):
                                try:
                                    parsed_headers = json.loads(str(headers_raw))
                                except Exception:
                                    pass
                            if active_cookie.strip():
                                parsed_headers["Cookie"] = active_cookie.strip()

                            parsed_api_list.append({
                                "name": f"{scenario_prefix}_{name}",
                                "method": str(method),
                                "base_url": str(base_url) if pd.notna(base_url) else "${BASE_URL}",
                                "path": str(endpoint) if pd.notna(endpoint) else "/",
                                "headers": parsed_headers,
                                "body": body if pd.notna(body) else None
                            })

                elif input_type == "Swagger / OpenAPI JSON":
                    uploaded_swagger = st.file_uploader("Upload Swagger / OpenAPI Specification", type=["json"],
                                                        key="nollm_swagger_uploader")
                    if uploaded_swagger:
                        swagger_data = json.load(uploaded_swagger)
                        host = swagger_data.get("host", "${BASE_URL}")
                        for path, methods in swagger_data.get("paths", {}).items():
                            for method, details in methods.items():
                                headers = {"Content-Type": "application/json", "Accept": "application/json"}
                                if active_cookie.strip():
                                    headers["Cookie"] = active_cookie.strip()
                                parsed_api_list.append({
                                    "name": f"{scenario_prefix}_{method.upper()}_{path.strip('/').replace('/', '_')}",
                                    "method": method.upper(),
                                    "base_url": host,
                                    "path": path,
                                    "headers": headers
                                })

                if st.button("⚡ Build Deterministic JMX Script", key="btn_build_nollm_jmx", type="primary"):
                    if parsed_api_list:
                        generated_xml_str = jmx_engine.create_standard_jmx(
                            parsed_api_list,
                            test_plan_name=f"{scenario_prefix} Test Plan"
                        )

                        # Cache generated output for the existing execution engine downstream
                        st.session_state.generated_jmx = generated_xml_str
                        st.session_state.generated_jmx_path = os.path.join(JMX_FOLDER, f"{scenario_prefix}_parsed.jmx")

                        with open(st.session_state.generated_jmx_path, "w", encoding="utf-8") as f:
                            f.write(generated_xml_str)

                        st.success(f"✅ Generated standard JMX for {len(parsed_api_list)} unique API endpoints!")
                    else:
                        st.error("Please upload a valid source file before generating.")

            if jmx_source_mode == "Upload Existing JMX Script File":
                uploaded_jmx = st.file_uploader("Upload your operational target .jmx file", type=["jmx"],
                                                key="perf_jmx_uploader")
                if uploaded_jmx:
                    st.session_state.generated_jmx = uploaded_jmx.getvalue().decode("utf-8")
                    st.session_state.generated_jmx_path = os.path.join(JMX_FOLDER, "runtime_api_execution.jmx")
                    with open(st.session_state.generated_jmx_path, "w", encoding="utf-8") as f:
                        f.write(st.session_state.generated_jmx)
                    st.success("📂 Baseline JMX configuration loaded and cached.")

                st.divider()
                enable_csv_datasets = st.checkbox("Include Optional Dataset Mapping (.csv)", value=False,
                                                  key="enable_csv_datasets_toggle")

                if enable_csv_datasets:
                    st.markdown("##### 📊 Map Supporting Execution Datasets (.csv)")
                    csv_source_selection = st.radio("Choose CSV Source Strategy", ["Upload CSV Datasets Locally",
                                                                                   "Download CSV Datasets from Git Remote Repository"],
                                                    key="csv_strategy_perf")
                    if csv_source_selection == "Upload CSV Datasets Locally":
                        local_csvs = st.file_uploader("Upload dataset files required by your JMX", type=["csv"],
                                                      accept_multiple_files=True, key="perf_local_csv")
                        if local_csvs:
                            for csv_file in local_csvs:
                                with open(os.path.join(GIT_WORKSPACE, csv_file.name), "wb") as f:
                                    f.write(csv_file.getbuffer())
                            st.success("✅ Local data components loaded.")
                    else:
                        col_g1, col_g2 = st.columns(2)
                        git_url = col_g1.text_input("Repository Remote URL",
                                                    value="https://github.com/SonaJayaram/Performance_IQEAUIIntegration.git",
                                                    key="git_url_perf")
                        git_branch = col_g2.text_input("Target Branch / Ref", value="feature/iqea-jmeter-enhancements",
                                                       key="git_branch_perf")
                        col_g3, col_g4 = st.columns(2)
                        git_token = col_g3.text_input("Personal Access Token", type="password", key="git_token_perf")
                        target_csv_files = col_g4.text_input("Comma-Separated Dataset Names to Pull", value="data.csv",
                                                             key="git_csv_perf")

                        if st.button("⚡ Sync Specified Git Data Components", key="btn_sync_git_perf"):
                            file_list = [f.strip() for f in target_csv_files.split(",") if f.strip()]
                            if git_url and file_list:
                                with st.spinner("Downloading datasets via raw endpoints..."):
                                    os.makedirs(GIT_WORKSPACE, exist_ok=True)
                                    clean_url = git_url.strip().removesuffix(".git").replace("https://github.com/", "")
                                    http = urllib3.PoolManager()
                                    headers = {"Authorization": f"token {git_token}"} if git_token else {}
                                    for remote_file_path in file_list:
                                        raw_url = f"https://raw.githubusercontent.com/{clean_url}/{git_branch}/{remote_file_path}"
                                        resp = http.request('GET', raw_url, headers=headers)
                                        if resp.status == 200:
                                            local_target_filename = os.path.basename(remote_file_path)
                                            with open(os.path.join(GIT_WORKSPACE, local_target_filename), "wb") as f:
                                                f.write(resp.data)
                                            st.success(f"✅ Downloaded and cached: {local_target_filename}")
                                        else:
                                            st.error(
                                                f"❌ Download failed for path: {remote_file_path} (Status: {resp.status})")

            elif jmx_source_mode == "Generate with AI via Action File Blueprint":
                action_folder = Action_collection
                action_files = [f for f in os.listdir(action_folder) if f.endswith("_actions.txt")] if os.path.exists(
                    action_folder) else []
                if not action_files:
                    st.warning("⚠ No recorded workflow action logs found in workspace.")
                else:
                    selected_action_file = st.selectbox("Select Recorded Workflow Profile", options=action_files,
                                                        key="sb_perf_action_file")
                    with open(os.path.join(action_folder, selected_action_file), "r", encoding="utf-8") as f:
                        actions_lines = f.read()

                        # Check for captured network logs in session
                        network_logs = st.session_state.get("captured_network_logs", "")

                    ai_prompt = st.text_area("Enter Additional Performance Test Settings",
                                             value="Generate Jmeter compatible jmx script with 10 users, 5 seconds rampup, 10 loops and 120 seconds test duration",
                                             key="ta_perf_ai_settings")

                    # ── ENHANCED JMETER PROMPT IMPLEMENTATION ──
                    if st.button("🚀 Generate AI-based JMX", key="btn_perf_gen_jmx"):
                        clean_api_logs = extract_clean_api_network_logs(
                            st.session_state.driver) if st.session_state.driver else ""
                        user_prompt = f"""
                        You are an expert Performance Testing Engineer specializing in Apache JMeter 5.6+.
                        Generate a complete, fully valid, and executable JMeter (.jmx) Test Plan XML based on the recorded UI actions and captured backend API calls below.

                        RECORDED UI WORKFLOW ACTIONS:
                        {actions_lines}

                        CAPTURED BACKEND API ENDPOINTS & PAYLOADS:
                        {clean_api_logs}

                        USER PERFORMANCE REQUIREMENTS:
                        {ai_prompt}

                        CRITICAL SAMPLER & METHOD RULES:
                        1. SAMPLER MAPPING:
                           - For EVERY captured API Endpoint listed above, generate a corresponding `<HTTPSamplerProxy>`.
                           - Match the exact HTTP Method (`PUT`, `POST`, `GET`, `DELETE`) captured in the endpoint data.
                        2. RAW JSON PAYLOAD BODY:
                           - For requests with a body payload (non-GET), set `<boolProp name="HTTPSampler.postBodyRaw">true</boolProp>`.
                           - Include the payload inside the sampler's `<elementProp name="HTTPsampler.Arguments" elementType="Arguments">` node:
                             <collectionProp name="Arguments.arguments">
                               <elementProp name="" elementType="HTTPArgument">
                                 <boolProp name="HTTPArgument.always_encode">false</boolProp>
                                 <stringProp name="Argument.value">EXACT_BODY_PAYLOAD_HERE</stringProp>
                                 <stringProp name="Argument.metadata">=</stringProp>
                               </elementProp>
                             </collectionProp>
                        3. HEADER MANAGER:
                           - Attach a `<HeaderManager>` child element to samplers requiring `Content-Type: application/json`.

                        STRICT XML SYNTAX RULES:
                        1. Every <boolProp> MUST be strictly: <boolProp name="Property.Name">true</boolProp> or <boolProp name="Property.Name">false</boolProp>.
                        2. Every <elementProp> for Arguments/Headers MUST strictly use class="HTTPArgument" or class="Header".
                        3. Return ONLY raw XML starting with <?xml version="1.0" encoding="UTF-8"?>. Do NOT include markdown code fences (```xml).
                        """

                        with st.spinner("Calling Core LLM Orchestrator via proxy paths..."):
                            raw_ai = utilitymodule.get_output_from_ai(user_prompt)
                            if raw_ai is None:
                                st.error("❌ JMX generation failed.")
                            else:
                                # Clean Markdown wrappers if returned by the LLM
                                clean_xml = raw_ai.strip()
                                if clean_xml.startswith("```"):
                                    clean_xml = re.sub(r"^```[a-zA-Z]*\n?", "", clean_xml)
                                    clean_xml = re.sub(r"\n?```$", "", clean_xml).strip()

                                ai_config = utilitymodule.extract_ai_test_config(ai_prompt, clean_xml)
                                st.session_state.generated_jmx = utilitymodule.update_jmx_file(clean_xml, ai_config)
                                st.session_state.generated_jmx_path = os.path.join(
                                    JMX_FOLDER, f"{selected_action_file.replace('_actions.txt', '')}.jmx"
                                )
                                with open(st.session_state.generated_jmx_path, "w", encoding="utf-8") as f:
                                    f.write(st.session_state.generated_jmx)
                                st.success("✅ JMX generated successfully!")

            if st.session_state.generated_jmx:
                st.divider()
                st.markdown("#### ⚙️ JMX Performance Execution Setup")
                execution_profile = st.selectbox("Choose Environment Infrastructure Config",
                                                 ["Local Dry Run / Smoke Test (Your Machine Only)",
                                                  "Actual Load Test (Distributed Master-Slave Config)"],
                                                 key="exec_env_matrix_split")

                st.markdown("##### ⚙️ Overriding Target Execution Runtime Properties")

                col_u0, col_u1, col_u2, col_u3, col_u4 = st.columns([2, 1.5, 1.5, 1.5, 1.5])

                master_ip_value = col_u0.text_input(
                    "Master / Telemetry IP",
                    value="10.0.0.4",
                    help="Target IP for InfluxDB backend metrics listener",
                    key="runtime_master_ip_input_split"
                )

                if "Local Dry Run" in execution_profile:
                    target_num_threads = col_u1.number_input("Concurrent Users (Threads)", min_value=1, value=1, step=1,
                                                             key="num_threads_input")
                    target_ramp_time = col_u2.number_input("Ramp-Up Period (Seconds)", min_value=1, value=1, step=1,
                                                           key="ramp_time_input")
                    target_loop_count = col_u3.number_input("Loop Interactions (-1 for Infinite)", min_value=-1,
                                                            value=1,
                                                            step=1, key="loop_count_input")
                    target_duration_time = col_u4.number_input("Test Run Schedule (Seconds)", min_value=0, value=5,
                                                               step=1,
                                                               key="duration_input")
                else:
                    target_num_threads = col_u1.number_input("Concurrent Users (Threads)", min_value=1, value=10,
                                                             step=1,
                                                             key="num_threads_input")
                    target_ramp_time = col_u2.number_input("Ramp-Up Period (Seconds)", min_value=1, value=5, step=1,
                                                           key="ramp_time_input")
                    target_loop_count = col_u3.number_input("Loop Interactions (-1 for Infinite)", min_value=-1,
                                                            value=-1,
                                                            step=1, key="loop_count_input")
                    target_duration_time = col_u4.number_input("Test Run Schedule (Seconds)", min_value=1, value=120,
                                                               step=1, key="duration_input")
                    st.caption("ℹ️ Distributed Slave VM IP: `10.0.0.5`")

                st.divider()
                st.markdown("### 📊 Live Telemetry Metric Redirection")
                grafana_url = st.text_input("Your Grafana Dashboard URL",
                                            value="http://localhost:3000/d/adf2bsx/iqeadashboard?orgId=1&refresh=5s&panelId=1",
                                            key="grafana_url_input_split")
                if "http" in grafana_url:
                    st.markdown(
                        f'<a href="{grafana_url}" target="_blank" style="text-decoration:none;"><div style="background-color:#800080;color:white;text-align:center;padding:10px;border-radius:5px;font-weight:bold;font-size:16px;margin-bottom:15px;cursor:pointer;">📈 Open Live Grafana Monitor Dashboard</div></a>',
                        unsafe_allow_html=True)

                if st.button("🚀 Fire Performance Execution Plan", key="btn_fire_performance_plan_split_main",
                             type="primary"):
                    st.info("Initiating orchestration pipeline and running target test context configuration...")
                    jmx_full_path = st.session_state.generated_jmx_path

                    if not jmx_full_path or not os.path.exists(jmx_full_path):
                        st.error("❌ Execution target configuration missing.")
                    else:
                        jmeter_path = r"D:\Practice\apache-jmeter-5.6.3\apache-jmeter-5.6.3\bin\jmeter.bat"

                        with open(jmx_full_path, "r", encoding="utf-8") as f:
                            original_jmx = f.read()
                        base_name = os.path.basename(jmx_full_path).replace(".jmx", "")
                        ai_config = {"threads": int(target_num_threads), "rampup": int(target_ramp_time),
                                     "loops": int(target_loop_count), "duration": int(target_duration_time)}

                        updated_jmx = utilitymodule.update_jmx_file(original_jmx, ai_config)
                        updated_jmx = utilitymodule.patch_influx_endpoint(updated_jmx, master_ip=master_ip_value)

                        try:
                            root_xml = ET.fromstring(updated_jmx)
                            for element in root_xml.iter("CSVDataSet"):
                                for prop in element.iter("stringProp"):
                                    if prop.attrib.get("name") == "filename":
                                        prop.text = os.path.basename(prop.text)
                            updated_jmx = ET.tostring(root_xml, encoding="utf-8").decode("utf-8")
                        except Exception:
                            pass

                        with open(jmx_full_path, "w", encoding="utf-8") as f:
                            f.write(updated_jmx)

                        report_base_dir = os.path.join(current_path, "jmeter_reports", base_name)
                        output_jtl = os.path.join(report_base_dir, f"{base_name}_log.jtl")
                        html_report_dir = os.path.join(report_base_dir, "html_dashboard")
                        pdf_report_path = os.path.join(report_base_dir, "Executive_Performance_Report.pdf")

                        if os.path.exists(report_base_dir):
                            shutil.rmtree(report_base_dir, ignore_errors=True)
                        os.makedirs(report_base_dir, exist_ok=True)

                        command = [jmeter_path, "-n", "-t", jmx_full_path, "-l", output_jtl,
                                   "-Jsummariser.name=summary"]
                        if execution_profile != "Local Dry Run / Smoke Test (Your Machine Only)":
                            command += ["-R", "10.0.0.5:1099"]

                        jmeter_bin_directory = os.path.dirname(jmeter_path)
                        custom_env = os.environ.copy()
                        if jmeter_bin_directory:
                            custom_env["JMETER_HOME"] = os.path.dirname(jmeter_bin_directory)

                        clean_master_ip = master_ip_value.strip() if master_ip_value and master_ip_value.strip() else "10.0.0.4"
                        custom_env[
                            "JVM_ARGS"] = f"-Djava.rmi.server.hostname={clean_master_ip} -Dclient.rmi.localport=60000 -Dserver.rmi.ssl.disable=true"

                        try:
                            process = subprocess.Popen(command, shell=True, env=custom_env, cwd=current_path,
                                                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                            log_stdout_box = st.empty()
                            accumulated_logs = ""
                            max_allowed_seconds = int(target_duration_time) + 60
                            start_time = datetime.now()

                            while True:
                                line = process.stdout.readline()
                                if line:
                                    accumulated_logs += line
                                    log_stdout_box.code(accumulated_logs[-3000:])
                                if not line and process.poll() is not None:
                                    break
                                if (datetime.now() - start_time).total_seconds() > max_allowed_seconds:
                                    st.warning("⚠️ Workload timeframe window hit.")
                                    break

                            if process.poll() is None:
                                subprocess.run(f"taskkill /F /T /PID {process.pid}", shell=True,
                                               stdout=subprocess.DEVNULL,
                                               stderr=subprocess.DEVNULL)
                            process.wait()
                            time.sleep(3)

                            if os.path.exists(output_jtl) and os.path.getsize(output_jtl) > 100:
                                st.success("🎉 Performance test workflow compiled completely!")

                                try:
                                    df_jtl = pd.read_csv(output_jtl)
                                    df_jtl.columns = [c.strip() for c in df_jtl.columns]

                                    total_samples = len(df_jtl)
                                    success_mask = df_jtl['success'].astype(str).str.strip().str.lower() == 'true'
                                    total_fails = len(df_jtl) - success_mask.sum()
                                    total_err_pct = (total_fails / total_samples) * 100 if total_samples > 0 else 0.0

                                    global_avg_load = df_jtl['elapsed'].mean() if total_samples > 0 else 0.0
                                    global_p90_load = df_jtl['elapsed'].quantile(0.90) if total_samples > 0 else 0.0

                                    grouped = df_jtl.groupby('label').agg(
                                        samples_count=('elapsed', 'count'),
                                        avg_load=('elapsed', 'mean'),
                                        min_val=('elapsed', 'min'),
                                        max_val=('elapsed', 'max'),
                                        median_val=('elapsed', 'median'),
                                        p90=('elapsed', lambda x: x.quantile(0.90)),
                                        p95=('elapsed', lambda x: x.quantile(0.95)),
                                        p99=('elapsed', lambda x: x.quantile(0.99)),
                                        success_count=('success', lambda x: (
                                                    x.astype(str).str.strip().str.lower() == 'true').sum())
                                    ).reset_index()

                                    jmx_page_metrics = []
                                    test_duration = float(target_duration_time) if float(
                                        target_duration_time) > 0 else 60.0

                                    for _, r in grouped.iterrows():
                                        lbl = str(r['label'])
                                        sc = int(r['samples_count'])
                                        fails = sc - int(r['success_count'])
                                        ep = (fails / sc) * 100 if sc > 0 else 0.0
                                        l_ms = float(r['avg_load'])
                                        p90_ms = float(r['p90'])
                                        calculated_tps = sc / test_duration

                                        jmx_page_metrics.append({
                                            "name": lbl, "samples": sc, "fail": fails, "error_pct": f"{ep:.2f}%",
                                            "load": l_ms, "min": int(r['min_val']), "max": int(r['max_val']),
                                            "median": float(r['median_val']), "p90": p90_ms,
                                            "p95": float(r['p95']), "p99": float(r['p99']), "tps": calculated_tps,
                                        })

                                    slowest_page = grouped.loc[grouped['avg_load'].idxmax()]['label'] if len(
                                        grouped) > 0 else "N/A"
                                    slowest_time = grouped['avg_load'].max() if len(grouped) > 0 else 0.0
                                    overall_go_status = "GO" if total_err_pct < 10.0 else "NO GO"

                                    powerbi_html_content = build_html_dashboard_content(
                                        overall_go_status, "#d4edda" if overall_go_status == "GO" else "#f8d7da",
                                        "#155724" if overall_go_status == "GO" else "#721c24",
                                        "#c3e6cb" if overall_go_status == "GO" else "#f5c6cb",
                                        slowest_page, slowest_time, total_samples, total_err_pct, jmx_page_metrics,
                                        global_avg_load, global_p90_load, target_num_threads, target_ramp_time,
                                        str(target_loop_count), target_duration_time, total_samples / test_duration
                                    )

                                    os.makedirs(html_report_dir, exist_ok=True)
                                    with open(os.path.join(html_report_dir, "index.html"), "w",
                                              encoding="utf-8") as out_f:
                                        out_f.write(powerbi_html_content)

                                    generate_executive_pdf(
                                        pdf_report_path, overall_go_status, total_samples,
                                        total_err_pct, global_avg_load, global_p90_load, total_samples / test_duration,
                                        target_num_threads, target_ramp_time, target_duration_time,
                                        slowest_page, slowest_time, jmx_page_metrics
                                    )

                                    st.success("✅ JMeter Performance Execution Complete!")
                                    st.info(f"📊 Dashboard Location: {html_report_dir}")

                                    if os.path.exists(pdf_report_path):
                                        with open(pdf_report_path, "rb") as pdf_f:
                                            st.download_button(
                                                label="📄 Download Executive PDF Report File",
                                                data=pdf_f.read(),
                                                file_name="Executive_Performance_Report.pdf",
                                                mime="application/pdf",
                                                use_container_width=True,
                                                key="btn_download_exec_pdf_ui"
                                            )
                                except Exception as d_err:
                                    st.error(f"❌ Failed to parse data values: {d_err}")
                        except Exception as ex:
                            st.error(f"❌ Core engine configuration crash: {ex}")

            if st.session_state.generated_jmx:
                st.divider()
                st.subheader("📄 Generated JMX Blueprint Output")
                st.code(st.session_state.generated_jmx, language="xml")
                target_download_filename = os.path.basename(
                    st.session_state.generated_jmx_path) if st.session_state.generated_jmx_path else "api_performance_plan.jmx"
                st.download_button(label="⬇ Download Plan Layout", data=st.session_state.generated_jmx,
                                   file_name=target_download_filename, mime="application/xml")

        # ── K6 SECTION ──────────────────────────────────────────────────────
        elif perf_tool_choice == "k6":
            k6_source_mode = st.radio(
                "Select Script Sourcing Method",
                ["Upload Existing k6 Script (.js)", "Generate with AI via Action File Blueprint"],
                index=1, horizontal=True, key="k6_source_mode_radio_split"
            )

            if k6_source_mode == "Upload Existing k6 Script (.js)":
                uploaded_k6 = st.file_uploader("Upload your target k6 .js script file", type=["js"],
                                               key="perf_k6_uploader")
                if uploaded_k6:
                    st.session_state.generated_k6_script = uploaded_k6.getvalue().decode("utf-8")
                    st.session_state.generated_k6_path = os.path.join(K6_FOLDER, "runtime_k6_execution.js")
                    with open(st.session_state.generated_k6_path, "w", encoding="utf-8") as f:
                        f.write(st.session_state.generated_k6_script)
                    st.success("📂 Baseline k6 script loaded and cached.")

            elif k6_source_mode == "Generate with AI via Action File Blueprint":
                action_folder = Action_collection
                action_files = [f for f in os.listdir(action_folder) if f.endswith("_actions.txt")] if os.path.exists(
                    action_folder) else []
                if not action_files:
                    st.warning("⚠ No recorded workflow action logs found in workspace.")
                else:
                    selected_action_file_k6 = st.selectbox("Select Recorded Workflow Profile", options=action_files,
                                                           key="sb_perf_k6_action_file")
                    with open(os.path.join(action_folder, selected_action_file_k6), "r", encoding="utf-8") as f:
                        actions_lines_k6 = f.read()

                    ai_prompt_k6 = st.text_area("Enter Additional k6 Performance Settings",
                                                value="Generate k6 ES6 script with 10 VUs, 5 seconds ramp-up, and 60 seconds duration",
                                                key="ta_perf_k6_ai_settings")

                    if st.button("🚀 Generate AI-based k6 Script", key="btn_perf_gen_k6"):
                        user_prompt_k6 = (
                            f"Generate a COMPLETE, VALID executable Grafana k6 JavaScript ES6 test script using 'k6/browser' for the following recorded workflows:\n"
                            f"{actions_lines_k6}\n\nAdditional parameters:\n{ai_prompt_k6}\n\n"
                            "CRITICAL RULES TO PREVENT INSTANT CRASHES & REGISTER BROWSER:\n"
                            "1. SCENARIO CONFIGURATION: You MUST define the browser type in scenario options as follows:\n"
                            "   export const options = {\n"
                            "     scenarios: {\n"
                            "       ui: {\n"
                            "         executor: 'ramping-vus',\n"
                            "         startVUs: 0,\n"
                            "         stages: [{ duration: '5s', target: 10 }, { duration: '60s', target: 10 }],\n"
                            "         options: {\n"
                            "           browser: { type: 'chrome' }\n"
                            "         }\n"
                            "       }\n"
                            "     }\n"
                            "   };\n"
                            "2. ASYNC INITIALIZATION: Always use `const browserContext = await browser.newContext();` and `const page = await browserContext.newPage();` inside the default async function.\n"
                            "3. SINGLE FILL: Never call `.fill()` multiple times sequentially on the same element.\n"
                            "4. SPA NAVIGATIONS: Only use `Promise.all([page.waitForNavigation(...), ...])` for the LOGIN and LOGOUT actions that reload the browser URL. For internal UI buttons/tabs, use `await page.locator(...).click();` directly.\n"
                            "5. DELAY FOR PAGE RENDERS: Import `sleep` from 'k6' and insert `sleep(1);` after each page/view navigation so Chromium metrics can be accurately sampled.\n"
                            "6. SAFE CLEANUP: In the `finally` block, check existence before closing:\n"
                            "   finally {{\n"
                            "     if (page) await page.close();\n"
                            "     if (browserContext) await browserContext.close();\n"
                            "   }}\n"
                            "7. Do NOT wrap output in markdown code fences."
                        )
                        with st.spinner("Calling Core LLM Orchestrator for k6 script generation..."):
                            raw_ai_k6 = utilitymodule.get_k6_output_from_ai(user_prompt_k6)
                            if not raw_ai_k6:
                                st.error("❌ k6 script generation failed.")
                            else:
                                st.session_state.generated_k6_script = raw_ai_k6.strip()
                                st.session_state.generated_k6_path = os.path.join(K6_FOLDER,
                                                                                  f"{selected_action_file_k6.replace('_actions.txt', '')}.js")
                                with open(st.session_state.generated_k6_path, "w", encoding="utf-8") as f:
                                    f.write(st.session_state.generated_k6_script)
                                st.success("✅ k6 script generated successfully!")

            if st.session_state.generated_k6_script:
                st.divider()
                st.markdown("#### ⚙️ k6 Performance Execution Setup")
                k6_exec_profile = st.selectbox("Choose Environment Infrastructure Config",
                                               ["Local Dry Run / Smoke Test (Your Machine Only)",
                                                "Actual Load Test (Distributed Master-Slave Config)"],
                                               key="k6_exec_profile_select")

                col_k1, col_k2, col_k3 = st.columns(3)
                k6_vus = col_k1.number_input("Virtual Users (VUs)", min_value=1, value=10, step=1, key="k6_vus_input")
                k6_rampup = col_k2.number_input("Ramp-up Period (Seconds)", min_value=0, value=5, step=1,
                                                key="k6_rampup_input")
                k6_duration = col_k3.number_input("Test Duration (Seconds)", min_value=5, value=60, step=5,
                                                  key="k6_duration_input")

                if st.button("🚀 Fire k6 Execution Plan", key="btn_fire_k6_plan", type="primary"):
                    st.info("Executing k6 workload engine...")
                    k6_report_dir = os.path.join(current_path, "k6_reports", "ui_k6_run")
                    os.makedirs(k6_report_dir, exist_ok=True)

                    k6_json_out = os.path.join(k6_report_dir, "k6_run_summary.json")
                    html_report_dir = os.path.join(k6_report_dir, "html_dashboard")
                    pdf_report_path = os.path.join(k6_report_dir, "Executive_k6_Performance_Report.pdf")

                    if os.path.exists(k6_json_out):
                        try:
                            os.remove(k6_json_out)
                        except Exception:
                            pass

                    k6_binary = r"C:\Program Files\k6\k6.exe"
                    slave_ip = "10.0.0.5"
                    slave_remote_json = r"C:\Windows\Temp\k6_remote_summary.json"

                    if "Local Dry Run" in k6_exec_profile:
                        cmd_run = [
                            k6_binary if os.path.exists(k6_binary) else "k6",
                            "run",
                            "-e", "K6_BROWSER_ENABLED=true",
                            "-e", "K6_BROWSER_HEADLESS=true",
                            "--stage", f"{k6_rampup}s:{k6_vus}",
                            "--stage", f"{k6_duration}s:{k6_vus}",
                            "--summary-export", k6_json_out,
                            st.session_state.generated_k6_path
                        ]
                    else:
                        st.caption(f"⚡ Dispatching k6 workload to Slave Generator Node: `{slave_ip}`...")
                        cmd_run = [
                            "ssh", "-o", "StrictHostKeyChecking=no", f"BusinessUser@{slave_ip}",
                            f"K6_BROWSER_ENABLED=true k6 run --quiet --stage {k6_rampup}s:{k6_vus} --stage {k6_duration}s:{k6_vus} --summary-export {slave_remote_json} -"
                        ]

                    env_vars = os.environ.copy()
                    env_vars["K6_BROWSER_ENABLED"] = "true"
                    env_vars["K6_BROWSER_HEADLESS"] = "true"

                    try:
                        if "Local Dry Run" in k6_exec_profile:
                            proc = subprocess.run(cmd_run, capture_output=True, text=True, check=False, env=env_vars)
                        else:
                            with open(st.session_state.generated_k6_path, "r", encoding="utf-8") as k6_f:
                                script_data = k6_f.read()
                            proc = subprocess.run(cmd_run, input=script_data, capture_output=True, text=True,
                                                  check=False, env=env_vars)

                            cmd_scp = [
                                "scp", "-o", "StrictHostKeyChecking=no",
                                f"BusinessUser@{slave_ip}:{slave_remote_json}",
                                k6_json_out
                            ]
                            subprocess.run(cmd_scp, capture_output=True, text=True, check=False)

                        logs = proc.stdout if proc.stdout else proc.stderr
                        if logs:
                            st.code(logs[-3000:])

                        if os.path.exists(k6_json_out):
                            st.success("✅ k6 Performance Execution Complete! Compiling Dashboard...")
                            with open(k6_json_out, "r", encoding="utf-8") as f_json:
                                data = json.load(f_json)

                            metrics = data.get("metrics", {})


                            def extract_val(metric_obj, key_name, default=0.0):
                                if not isinstance(metric_obj, dict):
                                    return default
                                vals = metric_obj.get("values", {})
                                if isinstance(vals, dict) and key_name in vals:
                                    return vals[key_name]
                                if key_name in metric_obj:
                                    return metric_obj[key_name]
                                return default


                            reqs_obj = metrics.get(
                                "browser_http_reqs",
                                metrics.get("http_reqs",
                                            metrics.get("iterations", metrics.get("browser_web_vital_fcp", {})))
                            )
                            dur_obj = metrics.get(
                                "browser_http_req_duration",
                                metrics.get("http_req_duration", metrics.get("iteration_duration", {}))
                            )
                            fail_obj = metrics.get(
                                "browser_http_req_failed",
                                metrics.get("http_req_failed", metrics.get("checks", {}))
                            )

                            web_vitals_data = {
                                "fcp": float(extract_val(metrics.get("browser_web_vital_fcp", {}), "avg", 0.0)),
                                "lcp": float(extract_val(metrics.get("browser_web_vital_lcp", {}), "avg", 0.0)),
                                "ttfb": float(extract_val(metrics.get("browser_web_vital_ttfb", {}), "avg", 0.0)),
                                "cls": float(extract_val(metrics.get("browser_web_vital_cls", {}), "avg", 0.0)),
                                "inp": float(extract_val(metrics.get("browser_web_vital_inp", {}), "avg", 0.0))
                            }

                            browser_network_data = {
                                "recv_kb": float(
                                    extract_val(metrics.get("browser_data_received", {}), "count", 0.0)) / 1024.0,
                                "sent_kb": float(
                                    extract_val(metrics.get("browser_data_sent", {}), "count", 0.0)) / 1024.0
                            }

                            total_samples = int(extract_val(reqs_obj, "count", 0))
                            failed_samples = int(extract_val(fail_obj, "fails", extract_val(fail_obj, "passes", 0)))
                            total_err_pct = (failed_samples / total_samples * 100) if total_samples > 0 else 0.0

                            global_avg_load = float(extract_val(dur_obj, "avg", 0.0))
                            global_min_load = float(extract_val(dur_obj, "min", 0.0))
                            global_max_load = float(extract_val(dur_obj, "max", 0.0))
                            global_med_load = float(extract_val(dur_obj, "med", 0.0))
                            global_p90_load = float(extract_val(dur_obj, "p(90)", 0.0))
                            global_tps = total_samples / k6_duration if k6_duration > 0 else 0.0

                            k6_page_metrics = [{
                                "name": "k6_execution_metrics",
                                "samples": total_samples,
                                "fail": failed_samples,
                                "error_pct": f"{total_err_pct:.2f}%",
                                "load": global_avg_load,
                                "min": int(global_min_load),
                                "max": int(global_max_load),
                                "median": global_med_load,
                                "p90": global_p90_load,
                                "tps": global_tps
                            }]

                            slowest_page = "k6_execution_metrics"
                            slowest_time = global_avg_load
                            overall_go_status = "GO" if total_err_pct < 10.0 else "NO GO"

                            k6_html_content = build_k6_html_dashboard_content(
                                overall_go_status, "#d4edda" if overall_go_status == "GO" else "#f8d7da",
                                "#155724" if overall_go_status == "GO" else "#721c24",
                                "#c3e6cb" if overall_go_status == "GO" else "#f5c6cb",
                                slowest_page, slowest_time, total_samples, total_err_pct,
                                k6_page_metrics, global_avg_load, global_p90_load,
                                k6_vus, k6_rampup, "1", k6_duration, global_tps,
                                web_vitals=web_vitals_data,
                                browser_network=browser_network_data
                            )

                            os.makedirs(html_report_dir, exist_ok=True)
                            with open(os.path.join(html_report_dir, "index.html"), "w", encoding="utf-8") as out_f:
                                out_f.write(k6_html_content)

                            generate_executive_pdf(
                                pdf_report_path, overall_go_status, total_samples,
                                total_err_pct, global_avg_load, global_p90_load, global_tps,
                                k6_vus, k6_rampup, k6_duration, slowest_page, slowest_time, k6_page_metrics
                            )

                            st.success("✅ k6 Analytics Engine Sync Complete!")
                            st.info(f"📊 Dashboard Location: {html_report_dir}")

                            if os.path.exists(pdf_report_path):
                                with open(pdf_report_path, "rb") as pdf_f:
                                    st.download_button(
                                        label="📄 Download Executive PDF Report File",
                                        data=pdf_f.read(),
                                        file_name="Executive_k6_Performance_Report.pdf",
                                        mime="application/pdf",
                                        use_container_width=True,
                                        key="btn_download_k6_pdf_ui"
                                    )
                        else:
                            st.error("❌ k6 execution failed: Summary JSON file was not generated.")

                    except FileNotFoundError:
                        st.error("❌ 'k6' binary not found. Please verify k6 installation path.")
                    except Exception as run_e:
                        st.error(f"❌ k6 execution error: {run_e}")

            if st.session_state.generated_k6_script:
                st.divider()
                st.subheader("📄 Generated k6 Script Output")
                st.code(st.session_state.generated_k6_script, language="javascript")
                target_download_k6_filename = os.path.basename(
                    st.session_state.generated_k6_path) if st.session_state.generated_k6_path else "k6_performance_script.js"
                st.download_button(label="⬇ Download k6 Script", data=st.session_state.generated_k6_script,
                                   file_name=target_download_k6_filename, mime="application/javascript")

# Footer of webpage
st.divider()
st.markdown("""    
    ### Contact Us
    - Reach us at [QE Core Team](mailto:sahil.gupta@tigeranalytics.com)
""")