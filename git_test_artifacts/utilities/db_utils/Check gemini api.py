
from langchain_core.messages import HumanMessage
from langchain_openai import AzureChatOpenAI
import os
from dotenv import load_dotenv
load_dotenv()
def get_queries_from_ai_updated_again(formatted_summary):
    # Access the variables
    api_key = os.getenv("GEMINI_API_KEY")
    endpoint = os.getenv("GEMINI_ENDPOINT")

    # Set the environment variables explicitly if needed
    os.environ["GEMINI_API_KEY"] = api_key
    os.environ["GEMINI_ENDPOINT"] = endpoint

    model = AzureChatOpenAI(
        openai_api_version="2023-05-15",
        azure_deployment="qepracticekey",
        max_tokens=4000,  # adjust depending on your model quota
        temperature=0
    )
    prompt = formatted_summary
    message = HumanMessage(content=prompt)
    output_value = model([message])
    print(output_value)
    return output_value.content

get_queries_from_ai_updated_again("Hi")