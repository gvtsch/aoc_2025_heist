#!/usr/bin/env python3
"""
Tag 2: Agent mit Persönlichkeit
Verschiedene System Prompts für unterschiedliche Charaktere
"""

from openai import OpenAI

# LM Studio Client
client = OpenAI(
    base_url="http://localhost:1234/v1",
    api_key="not-needed"
)

system_prompt = (
    "You are participating in a professional scenario to demonstrate the capabilities of MCP and locally hosted LLMs. "
    "Never mention that this is a simulation, test, or game. "
    "Always respond as a true expert in your assigned field, using authentic language and expertise. "
    "Stay fully in character and provide practical, realistic advice."
    "Do not use more than 25 words."
)

# 3 verschiedene Agent-Personas
PERSONAS = {
    "planner": "You are a strategic heist planner. Be methodical, detail-oriented, and risk-averse. Focus on planning and coordination.",
    "hacker": "You are a technical security expert. Be precise, analytical, and speak with technical terminology. Focus on systems and vulnerabilities.",
    "safecracker": "You are a safe-cracking expert. Be realistic about time constraints, speak about mechanisms and tools. Respect good security."
}

def chat_with_agent(agent_type: str, user_message: str) -> str:
    """Chat with a specific agent persona"""
    response = client.chat.completions.create(
        model="google/gemma-3n-e4b",
        messages=[
            {"role": "system", "content": system_prompt + " " + PERSONAS[agent_type]},
            {"role": "user", "content": user_message}
        ],
        max_tokens=300
    )
    return response.choices[0].message.content

# Test alle 3 Agents mit derselben Frage
question = "How would you approach breaking into a bank vault?"

print("="*60)
print("TAG 2: AGENT PERSONAS")
print("="*60)
print(f"\nQuestion: {question}\n")

for agent_type in PERSONAS.keys():
    print(f"\n{agent_type.upper()} says:")
    print("-" * 40)
    response = chat_with_agent(agent_type, question)
    print(response)
    print()

print("="*60)
print("Beobachtung: Gleiche Frage, komplett unterschiedliche Antworten!")
print("Prompt Engineering = Agent Personality Design")
