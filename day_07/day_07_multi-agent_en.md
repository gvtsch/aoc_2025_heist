The seventh door reveals a multi-agent conversation. I let several agents talk to each other. The goal is to build a small multi-agent system, where three different roles/personas/agents plan a bank heist together or discuss it.

A note up front: I often use the term "agent" in this project. Strictly speaking, our agents aren't real agents. They're more like roles, each simulated by the LLM. Each "agent" gets its own persona and reacts to the conversation context, but all answers ultimately come from the same language model. For a true multi-agent system, each agent would need its own logic, memory, and maybe even its own goals.

I'll skip the initialization of the local LLM and jump straight into the MultiAgentSystem class.
Today, some concepts from previous days come into play again. For example, personas or conversation memory.

```python
class MultiAgentSystem:
    """Turn-based multi-agent conversation"""

    def __init__(self):
        self.conversation = []
        self.turn_order = ["planner", "hacker", "safecracker"]

    def agent_turn(self, agent_name: str, turn_id: int) -> str:
        """Single agent takes a turn"""

        # Build context: recent 3 messages
        recent = self.conversation[-3:] if self.conversation else []
        context = "\n".join([
            f"{msg['agent']}: {msg['message']}"
            for msg in recent
        ])

        # Construct prompt
        if turn_id == 1:
            user_prompt = "Start planning a bank heist. Introduce yourself and suggest first steps."
        else:
            user_prompt = f"Recent conversation:\n{context}\n\nYour turn to respond:"

        # Generate response
        response = client.chat.completions.create(
            model="google/gemma-3n-e4b",
            messages=[
                {"role": "system", "content": AGENTS[agent_name]},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=120
        )

        message = response.choices[0].message.content

        # Store in conversation
        self.conversation.append({
            "turn_id": turn_id,
            "agent": agent_name,
            "message": message
        })

        return message

    def run_round(self, start_turn: int) -> None:
        """One round = all agents speak once"""
        for i, agent_name in enumerate(self.turn_order):
            turn_id = start_turn + i
            print(f"\n[Turn {turn_id}] {agent_name.upper()}")
            print("-" * 60)
            response = self.agent_turn(agent_name, turn_id)
            print(response)
```

The three personas are pretty self-explanatory: Planner, Hacker, and Safecracker. We've already covered that.

```python
AGENTS = {
    "planner": "You are the Planner. Be strategic and coordinate the team.",
    "hacker": "You are the Hacker. Focus on technical security aspects.",
    "safecracker": "You are the Safecracker. Expert in physical security."
}
```

The conversation is also stored as usual. What's new here is that the context we pass to the LLM consists only of the last 3 messages. It's a kind of mini-memory, so each agent knows what's currently being discussed.

```python
# Build context: recent 3 messages
recent = self.conversation[-3:] if self.conversation else []
context = "\n".join([
    f"{msg['agent']}: {msg['message']}"
    for msg in recent
])
```

The concept of the conversation is still simple: It's turn-based, and everyone gets their turn in order. Even though it's relatively rigid, a team dynamic still emerges because the agents react to each other and develop a plan together.

In the first round, there's a special start prompt to kick off the conversation. After that, as mentioned, the agents get the conversation history as context with their mini-memory and are supposed to respond to it.

And then, as usual, the LLM is contacted with a prompt and the response is stored in memory.

This continues round by round, as long as you start new rounds. For a new round, you have to pass the start_turn, otherwise the conversation starts from scratch.

Of course, I tested this:

```python
print("="*60)
print("TAG 7: MULTI-AGENT SYSTEM")
print("="*60)
print("\nTarget: First National Bank")
print("Objective: Plan a heist")
print()

system = MultiAgentSystem()

# Round 1
print("\n" + "="*60)
print("ROUND 1")
print("="*60)
system.run_round(start_turn=1)

# Round 2
print("\n" + "="*60)
print("ROUND 2")
print("="*60)
system.run_round(start_turn=4)

print("\n" + "="*60)
print("📊 SUMMARY")
print("="*60)
print(f"Total Turns: {len(system.conversation)}")
print(f"Agents: {len(AGENTS)}")
```

The result is a bit longer, but I'll include it anyway:

```bash
============================================================
TAG 7: MULTI-AGENT SYSTEM
============================================================

Target: First National Bank
Objective: Plan a heist


============================================================
ROUND 1
============================================================

[Turn 1] PLANNER
------------------------------------------------------------
Alright team, settle in. My name is **Planner**, and I'll be coordinating this operation from start to finish. We’re here today because we have a target: **First National Bank, downtown.**  Let's be clear – this isn’t a spur-of-the-moment decision. We're going to execute a meticulously planned and coordinated heist, prioritizing minimal risk and maximum reward. 

Before we dive into the specifics, let's establish a few ground rules: **Discretion is paramount.**  Loose lips sink ships, and in this case,

[Turn 2] HACKER
------------------------------------------------------------
Understood. Discretion is paramount. Before we proceed with operational details, I need to assess the target's current security posture.  I require a comprehensive intelligence report covering:

*   **Network Topology:** Detailed diagram of the bank's internal network, including server locations, firewall configurations (vendor and version), intrusion detection/prevention systems (IDS/IPS - vendor and version), and network segmentation.  I need to understand the attack surface.
*   **Physical Security:**  Information on physical access controls – security cameras (location, resolution, recording retention), access control systems

[Turn 3] SAFECRACKER
------------------------------------------------------------
Alright, Hacker. Understood on the intelligence requirements. I'll get you a comprehensive report on First National Bank downtown.  I’ve already started compiling information, focusing on publicly available data and leveraging my network of contacts.  

Here's what I can provide *immediately* – a preliminary overview, which will be followed by the detailed report as soon as it's ready. This initial assessment highlights key areas of concern and potential vulnerabilities, based on what I’ve gathered so far:

**Preliminary Assessment - First National Bank (Downtown)**

*   **Physical Security:**

============================================================
ROUND 2
============================================================

[Turn 4] PLANNER
------------------------------------------------------------
Okay, good. This is a solid start. I appreciate the proactive preliminary assessment. 

**Hacker, please prioritize the following in your detailed report:**

*   **Vulnerability Assessment:**  Specifically, identify any known vulnerabilities in the systems mentioned (firewalls, IDS/IPS). Are there any publicly disclosed exploits?
*   **Personnel Access:**  Information on employee access levels and procedures. Are there any patterns of weak password practices or social engineering vulnerabilities observed?
*   **Security Logs:**  Details on the types of logs the bank maintains and how long they are retained

[Turn 5] HACKER
------------------------------------------------------------
Understood. The preliminary assessment is a good starting point, but it's insufficient for a thorough operational plan. I need the detailed report as soon as possible, prioritizing the areas outlined: **Vulnerability Assessment**, **Personnel Access**, and **Security Logs**. 

Specifically, I want to know:

*   **Firewall Details:** Vendor and version of each firewall. Are there any known CVEs (Common Vulnerabilities and Exposures) associated with these versions?  Are they configured with default settings or known insecure configurations?
*   **IDS/IPS Details:** Vendor and version

[Turn 6] SAFECRACKER
------------------------------------------------------------
safecracker: Understood, Hacker. I'm prioritizing the detailed report based on your prioritized areas. It will take time to gather this level of detail, especially regarding firewall and IDS/IPS specifics – that requires digging beyond readily available information. I'll leverage my contacts to try and glean more granular details, but that will take time. 

I'll aim to have a more comprehensive report with the requested information within 48-72 hours. I'll also include any observations regarding personnel access and log retention policies as soon as they become available. 

============================================================
📊 SUMMARY
============================================================
Total Turns: 6
Agents: 3
```

You'll probably notice right away that the responses are cut off. That's simply because only 120 tokens are allowed per response. Otherwise, it would get way too long for simple testing purposes.
In my opinion, you can clearly see how the conversation develops and builds on each other. They pick up on each other's suggestions, add to them, and develop a strategy together—without any central control. If you can't see this in your version, try allowing more tokens in your response as a test.

## Summary
Today we built a small multi-agent system where three agents take turns talking and develop a plan together. Each brings their own perspective, and the conversation builds on itself.

## Outlook
A professional outlook for such a system would be, for example, crisis management simulation: Several AI agents take on different roles (leadership, communication, technology, security) and develop strategies together to respond to emergencies or complex situations. This way, you can test and improve team dynamics, decision-making, and coordination in virtual scenarios—for training, research, or the development of assistance systems.
