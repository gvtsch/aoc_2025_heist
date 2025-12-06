#!/usr/bin/env python3
"""
Tag 3: Conversation Memory
Agent sammelt Historie und "erinnert" sich
"""

from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:1234/v1",
    api_key="not-needed"
)

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

# Test
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
