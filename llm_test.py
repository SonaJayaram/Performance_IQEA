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
        response = client.chat.completions.create(model=model,
                                                  messages=[{"role": "user",
                                                             "content": formatted_summary
                                                             }
                                                            ])
        print(response)
        return response.choices[0].message.content
    except Exception as e:
        print(f"[ERROR] LLM call failed: {e}")
        return None


formatted_summary = "hi"
get_queries_from_ai_updated(formatted_summary)