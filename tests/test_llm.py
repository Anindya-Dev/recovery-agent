import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

if __name__ == "__main__":
    api_key = os.getenv("NVIDIA_API_KEY")

    if not api_key:
        raise ValueError("NVIDIA_API_KEY is not set")

    client = OpenAI(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=api_key,
    )

    response = client.chat.completions.create(
        model="nvidia/nemotron-3.5-lightning-30b-a3b",
        messages=[
            {
                "role": "user",
                "content": "Reply with exactly: API connection successful",
            }
        ],
        temperature=0,
        max_tokens=50,
        extra_body={
            "chat_template_kwargs": {
                "enable_thinking": False
            }
        },
    )

    print(response.choices[0].message.content)
