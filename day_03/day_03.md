Welcome to Day 3! Once again, we are dealing with another cornerstone for the project: memory.

The problem: LLMs are stateless. How are agents supposed to know what has been discussed so far? This is crucial for this project (and for many other professional applications as well). The solution I am introducing here is a conversation memory.

The idea is that important—or all?—messages are stored in a history. For now, in this small example, I will store all messages. Next week, we will look at memory compression.

As in previous days, we start by establishing the connection to LM-Studio:

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:1234/v1",
    api_key="not-needed"
)
```

Then we begin by defining an agent with memory.

```python
class AgentWithMemory:
    """Agent mit Conversation History"""

    def __init__(self, persona: str):
        self.persona = persona
        self.conversation_history = []

    def chat(self, user_message: str) -> str:
        """Chat mit Memory"""
        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })

        # Build messages: system + full history
        messages = [
            {"role": "system", "content": self.persona}
        ] + self.conversation_history

        # Get LLM response
        response = client.chat.completions.create(
            model="google/gemma-3n-e4b",
            messages=messages,
            max_tokens=50
        )

        assistant_message = response.choices[0].message.content

        # Add assistant response to history
        self.conversation_history.append({
            "role": "assistant",
            "content": assistant_message
        })

        return assistant_message

    def get_context_size(self) -> int:
        """Calculate total tokens in context"""
        total_chars = sum(
            len(msg["content"]) for msg in self.conversation_history
        )
        return total_chars // 4  # rough estimate
```

The agent is again initialized with a persona. You can read more about what that is in yesterday's post. Additionally, the conversation_history is initialized.

In the chat function, every user message (prompt) is appended to this history. The same applies to the response.
Before that, however, the messages are constructed. Here, the system message is combined with the history. This way, the LLM receives the entire message history every time and can respond more accurately.

Finally, there is a function that counts the characters and roughly converts them into tokens. I use the factor 4, since on average, 4 characters (including spaces) correspond to one token in English.

This value is a rough estimate and can vary depending on language, text type, and model used.

For short words (e.g., "the", "and"), a token may consist of 3–4 characters.
For longer words or words with special characters (e.g., "computer", "don't"), a token may consist of more than 4 characters.
For numbers or special characters, the value can also vary.
For a more accurate estimate, you can use the tokenizer of the model in use (e.g., GPT, BERT).

Finally, I initialize the agent and start a conversation.

```python
agent = AgentWithMemory(
    persona="You are a bank heist planner."
)

print("="*60)
print("TAG 3: AGENT MEMORY")
print("="*60)

# Turn 1
print("\n[Turn 1]")
print("User: What's the target?")
response = agent.chat("What's the target?")
print(f"Agent: {response}")

# Turn 2
print("\n[Turn 2]")
print("User: What security systems does it have?")
response = agent.chat("What security systems does it have?")
print(f"Agent: {response}")

# Turn 3 - Test if agent remembers
print("\n[Turn 3]")
print("User: What was the target we discussed?")
response = agent.chat("What was the target we discussed?")
print(f"Agent: {response}")

print(f"\n📊 Context Size: ~{agent.get_context_size()} tokens")
print("⚠️  Problem: Context wächst linear → Token-Limit!")
```

I ask a few questions and also print out the answers.

My "conversation" also includes a test that checks whether the agent can remember previous messages. In other words, proof that the memory works.

## Summary
You can see from the conversation that it is possible to refer back to previously provided information. This has many advantages, but also the disadvantage that the context keeps growing and may eventually no longer fit into the context window. This can certainly happen with our locally hosted LLM. As mentioned, more on this next week when we discuss memory compression.