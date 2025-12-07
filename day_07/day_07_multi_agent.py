#!/usr/bin/env python3
"""
Tag 7: Multi-Agent System
3 Agents im Gespräch miteinander
"""

from openai import OpenAI
from typing import List, Dict

client = OpenAI(
    base_url="http://localhost:1234/v1",
    api_key="not-needed"
)

# Agent Personas
AGENTS = {
    "planner": "You are the Planner. Be strategic and coordinate the team.",
    "hacker": "You are the Hacker. Focus on technical security aspects.",
    "safecracker": "You are the Safecracker. Expert in physical security."
}

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

# Run simulation
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
print("\n🎯 Beobachtung: Agents bauen aufeinander auf!")
print("Emergent behavior ohne explizite Koordinations-Anweisung!")
