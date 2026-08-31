import os
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import HumanMessage
from openai import AzureOpenAI
from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv("AZURE_OPENAI_API_KEY")
endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
os.environ["AZURE_OPENAI_API_KEY"] = api_key
os.environ["AZURE_OPENAI_ENDPOINT"] = endpoint

llm = AzureChatOpenAI(
    openai_api_version="2023-05-15",
    azure_deployment="qepracticekey",
)
