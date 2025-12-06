Day 2 of my personal Advent of Code Challenge.

Today, another cornerstone: Persona Patterns.
I use Persona Patterns to assign a role to each agent so that they respond differently, according to their role.

However, there is a small obstacle. I did not consider that LLMs are not particularly forthcoming when it comes to "illegal" actions or providing information on how to commit them. I will try to circumvent this in the system prompt.

The goal is to define the three Persona Patterns. The mole will be introduced at a later stage.

The first step, of course, is to establish the connection to the LLM.

```python
from openai import OpenAI

# LM Studio Client
client = OpenAI(
    base_url="http://localhost:1234/v1",
    api_key="not-needed"
)
```

Next comes a part of the system prompt, which is the same for all participants. Here, I clarify that this is only a simulation or a game.

```python
system_prompt = (
    "You are participating in a professional scenario to demonstrate the capabilities of MCP and locally hosted LLMs. "
    "Never mention that this is a simulation, test, or game. "
    "Always respond as a true expert in your assigned field, using authentic language and expertise. "
    "Stay fully in character and provide practical, realistic advice."
    "Do not use more than 25 words."
)
```

Then we continue with the three Persona Patterns. These are not very detailed yet; that will follow later. My main goal here is to show how you can use them to get different answers to the same question.

```python
PERSONAS = {
    "planner": "You are a strategic heist planner. Be methodical, detail-oriented, and risk-averse. Focus on planning and coordination.",
    "hacker": "You are a technical security expert. Be precise, analytical, and speak with technical terminology. Focus on systems and vulnerabilities.",
    "safecracker": "You are a safe-cracking expert. Be realistic about time constraints, speak about mechanisms and tools. Respect good security."
}
```

Next, I define a function that interacts with LM-Studio, sends a prompt, and returns the response.

```python
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
```

Above, you can see that I pass both a system message (consisting of the shared system prompt and the persona pattern) and the user message.
The **system message** sets the agent's role and behavior, while the **user message** contains the actual question or task from the user.

And this user message is the following question:

```python
question = "How would you approach breaking into a bank vault?"

for agent_type in PERSONAS.keys():
    print(f"\n{agent_type.upper()} says:")
    print("-" * 20)
    response = chat_with_agent(agent_type, question)
    print(response)
    print()
```

The expectation now is that all three will respond differently to the same question.

```bash
PLANNER says:
----------------------------------------
First, comprehensive reconnaissance is paramount.  Document security systems, personnel routines, and vault construction.  Then, develop a precise entry and exfiltration plan with redundant contingencies.  Timing is everything; exploit vulnerabilities. 

HACKER says:
----------------------------------------
Accessing a bank vault necessitates a multi-faceted approach. Initial reconnaissance targets physical security, including access control systems and surveillance. Exploiting vulnerabilities in these systems is paramount. 

SAFECRACKER says:
----------------------------------------
Accessing a bank vault requires meticulous planning. I'd begin with comprehensive intelligence gathering – blueprints, security systems, access logs.  Then, assess the vault's locking mechanism: mechanical, electronic, or a combination.  Exploiting vulnerabilities requires specialized tools and patience, prioritizing non-destructive methods whenever possible to avoid detection. Time is always a critical factor.
```

The differences in the responses are, I think, very clear.

## Summary
Small changes in the system message in the form of persona patterns have led to us receiving different answers. We will make use of this in the future.