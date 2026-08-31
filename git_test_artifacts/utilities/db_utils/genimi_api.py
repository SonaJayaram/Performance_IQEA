import os
import openai
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI
load_dotenv()
source = "gemini"
# Set environment variables

#os.environ["OPENAI_API_KEY"] = os.getenv("GEMINI_API_KEY")
#os.environ["OPENAI_API_BASE"] = os.getenv("GEMINI_ENDPOINT")
os.environ["OPENAI_API_KEY"] = os.getenv("AZURE_OPENAI_API_KEY")
os.environ["OPENAI_API_BASE"] = os.getenv("AZURE_OPENAI_ENDPOINT")
client = openai.OpenAI(api_key =  os.environ["OPENAI_API_KEY"],
                       base_url = os.environ["OPENAI_API_BASE"])


def get_queries_from_ai_updated_gemini(formatted_summary):
    # Access the variables
    #model = "gemini-2.5-pro"
    model = "AzureChatOpenAI"
    # model = AzureChatOpenAI(
    #     openai_api_version="2023-05-15",
    #     azure_deployment="qepracticekey",
    #     max_tokens=4000,  # adjust depending on your model quota
    #     temperature=0
    # )
    response = client.chat.completions.create(model=model,
                                          messages=[{
                                                     "content": formatted_summary
                                                     }
                                                    ])
    print(response.choices[0].message.content)
    return response.choices[0].message.content
formatted_summary="7 wonders name?"

get_queries_from_ai_updated_gemini(formatted_summary)