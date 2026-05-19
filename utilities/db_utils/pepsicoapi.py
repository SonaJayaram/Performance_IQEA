import os
from openai import OpenAI

def verify_pepgenx_connection():
    """
    Verify PepGenX connection using OpenAI client.
    """

    # Load credentials (you can set these in your environment or .env)
    api_key = "a64e7f49-2779-49f5-abb2-cd46584807da"
    model ="gpt-4o"
    url = "https://pepgenx-apigateway-qa.global.gw01.aks01.eus.nonprod.azure.intra.pepsico.com/"
    apigee_endpoint = "https://apim-na.qa.mypepsico.com/cgf/pepgenx"

    # ✅ Use the base URL shared by PepGenX
    base_url = "https://apim-na.qa.mypepsico.com/"

    try:
        # Initialize client
        client = OpenAI(api_key=api_key, base_url=base_url)

        # Attempt a lightweight call
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": "Hello! Please confirm my PepGenX connection is active."}
            ],
            max_tokens=20,
        )

        # ✅ If we reach here, call succeeded
        print("✅ Connection successful!")
        print("Response:", response.choices[0].message.content)

    except Exception as e:
        # Catch and print any network/auth errors
        print(f"❌ Connection failed: {e.__class__.__name__}: {str(e)}")


if __name__ == "__main__":
    verify_pepgenx_connection()