from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:1234/v1",
    api_key="google/gemma-3n-e4b"
)

response = client.chat.completions.create(
    model="test-model",
    messages=[{"role": "user", "content": "Say OK"}],
    max_tokens=100
)

print(response.choices[0].message.content)
