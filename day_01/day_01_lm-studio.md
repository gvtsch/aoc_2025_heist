Today is about connecting to a locally hosted language model. There are various methods such as vllm, llama.cpp, ollama, or LM-Studio. Currently, I mainly use LM-Studio (except inside a Docker container, where I use ollama). The reasons vary, but functionally this doesn't have a major impact on my project at the moment.

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:1234/v1",
    api_key="google/gemma-3n-e4b"
)
```

Above, I've configured the connection to the model. For now, I'm just using a very small Gemma model. At the moment, it's not crucial whether the model is really good.

Then I try a simple test and send a prompt to the model.

```python
response = client.chat.completions.create(
    model="test-model",
    messages=[{"role": "user", "content": "Say OK"}],
    max_tokens=100
)
```


If a response comes back, that's already a good sign 😉 Now I just need to extract the content.

```python
print(response.choices[0].message.content)
```


And indeed, there's a readable answer :)

```bash
OK! 👍

Is there anything I can help you with?
```

## Conclusion

I've managed to establish a connection to the local language model. One of the cornerstones for the project.

## A few tips for getting started

If you want to try this yourself: You need the openai package (`pip install openai`) and, of course, LM Studio. Just start LM Studio, select a model, and activate the local server – then it works just like in the example above.

If the connection doesn't work: Check if LM Studio is really running and if the port number is correct. And don't panic, sometimes a restart helps. You can catch errors like this:

```python
try:
    response = client.chat.completions.create(
        model="test-model",
        messages=[{"role": "user", "content": "Say OK"}],
        max_tokens=100
    )
    print(response.choices[0].message.content)

except Exception as e:
    print("Connection error:", e)
```

And one more thought: Connecting to the model is just the first step. Later, the agents will communicate with each other through this channel – and that's when things get really exciting!
