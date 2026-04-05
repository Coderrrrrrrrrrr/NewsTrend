import os
from openai import OpenAI

api_key = "177665e4-d44d-46d9-8349-aa57049e0894"
base_url = "https://ark.cn-beijing.volces.com/api/v3"
model = "deepseek-v3-2-251201"

client = OpenAI(
    base_url=base_url,
    api_key=api_key
)

try:
    print(f"Connecting to {base_url} with model {model}...")
    # Trying standard chat completion first
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": "你好"}],
    )
    print("Success with chat.completions:")
    print(response.choices[0].message.content)
except Exception as e:
    print(f"Failed with chat.completions: {e}")
    print("Trying client.responses.create as in your example...")
    try:
        # Note: 'responses.create' is not standard OpenAI, 
        # but if user's example has it, maybe it's in a specific SDK version.
        # Actually, let's check if 'responses' exists.
        if hasattr(client, 'responses'):
             response = client.responses.create(
                model=model,
                input=[{"role": "user", "content": "你好"}],
            )
             print("Success with responses.create:")
             print(response)
        else:
            print("Client has no 'responses' attribute.")
    except Exception as e2:
        print(f"Failed with responses.create: {e2}")
