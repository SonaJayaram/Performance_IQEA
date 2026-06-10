import os
import pandas as pd
from openai import AzureOpenAI

# ----------------------------------------------------
# Azure OpenAI Credentials & Connection Initialization
# ----------------------------------------------------
api_key = "4fed2bedb59744a99b0424622f6d9d1b"
azure_endpoint = "https://qepracticekey.openai.azure.com/"
deployment_name = "qepracticekey"
api_version = "2023-05-15"

# Initialize the Azure-specific OpenAI client
client = AzureOpenAI(
    api_key=api_key,
    azure_endpoint=azure_endpoint,
    api_version=api_version
)


def load_jtl_report(file_path_or_buffer):
    """Loads a JMeter JTL/CSV report and standardizes columns."""
    try:
        df = pd.read_csv(file_path_or_buffer)
        # Strip trailing/leading spaces from column headers
        df.rename(columns={col: col.strip() for col in df.columns}, inplace=True)
        return df
    except Exception as e:
        raise ValueError(f"Error parsing performance data: {str(e)}")


def generate_summary(df):
    """Calculates core performance KPIs and determines automated Release Verdict."""
    # Ensure numerical consistency
    df['elapsed'] = pd.to_numeric(df['elapsed'], errors='coerce')

    # Handle error rate calculation based on JMeter's default logging behaviors
    if 'success' in df.columns:
        if df['success'].dtype == 'object':
            error_rate = (df['success'].astype(str).str.lower() != 'true').mean()
        else:
            error_rate = (df['success'] == False).mean()
    elif 'responseCode' in df.columns:
        error_rate = (df['responseCode'].astype(str) != '200').mean()
    else:
        error_rate = 0.0

    # Capture key latency metric percentiles
    p95 = df['elapsed'].quantile(0.95)
    p99 = df['elapsed'].quantile(0.99)
    mean_rt = df['elapsed'].mean()
    max_rt = df['elapsed'].max()

    # Compute Throughput (Transactions Per Second) across the log duration
    tps = 0.0
    if 'timeStamp' in df.columns and len(df) > 1:
        total_time_ms = df['timeStamp'].max() - df['timeStamp'].min()
        if total_time_ms > 0:
            tps = len(df) / (total_time_ms / 1000.0)

    # Heuristic scoring logic determining Go/No-Go boundaries
    # Penalizes score based on errors and high p95 response time thresholds
    error_penalty = error_rate * 100 * 2.5
    rt_penalty = 0
    if p95 > 2000: rt_penalty = 15
    if p95 > 5000: rt_penalty = 35

    release_score = max(0, min(100, int(100 - error_penalty - rt_penalty)))

    # Determine Status Title
    if release_score >= 80 and error_rate < 0.02:
        status = "GO (Release Ready)"
    elif release_score >= 50:
        status = "CAUTION (Review Required)"
    else:
        status = "NO-GO (Critical Issues Found)"

    return {
        'total_requests': len(df),
        'mean_response_time': round(mean_rt, 2),
        'p95_response_time': round(p95, 2),
        'p99_response_time': round(p99, 2),
        'max_response_time': round(max_rt, 2),
        'error_rate': round(error_rate * 100, 2),
        'throughput_tps': round(tps, 2),
        'release_score': release_score,
        'status': status
    }


def generate_recommendations(summary):
    """Leverages the initialized Azure deployment to yield optimization insights."""
    prompt = f"""
    Analyze the following performance test metrics from an engineering execution log and provide concrete optimization paths:

    - Total Requests: {summary['total_requests']}
    - Throughput: {summary['throughput_tps']} TPS
    - Mean Response Time: {summary['mean_response_time']} ms
    - 95th Percentile Response Time: {summary['p95_response_time']} ms
    - 99th Percentile Response Time: {summary['p99_response_time']} ms
    - Max Response Time: {summary['max_response_time']} ms
    - Error Rate: {summary['error_rate']}%
    - AI Release Score Verdict: {summary['status']} (Score: {summary['release_score']}/100)

    Provide structural recommendations grouped into:
    1. Performance Bottleneck Analysis
    2. Suggested Architectural & Infrastructure Remedies
    3. Operational Go/No-Go Recommendation Validation
    """

    try:
        # Note: 'model' field maps explicitly to your deployment_name config variable on Azure environments
        response = client.chat.completions.create(
            model=deployment_name,
            messages=[
                {"role": "system", "content": "You are an expert Performance Systems Architect."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.3
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Unable to fetch GenAI recommendations from Azure OpenAI: {str(e)}"