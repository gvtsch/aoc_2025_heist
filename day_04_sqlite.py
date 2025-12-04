#!/usr/bin/env python3
"""
Tag 4: SQLite Persistenz
Gespräche überleben Neustart
"""

import sqlite3
from datetime import datetime
from openai import OpenAI

# Setup SQLite
conn = sqlite3.connect("agent_memory.db")
cursor = conn.cursor()

# Create table
cursor.execute("""
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_name TEXT NOT NULL,
    turn_id INTEGER NOT NULL,
    message TEXT NOT NULL,
    timestamp TEXT NOT NULL
)
""")
conn.commit()

# LM Studio client
client = OpenAI(
    base_url="http://localhost:1234/v1",
    api_key="not-needed"
)

def save_message(agent_name: str, turn_id: int, message: str):
    """Save message to database"""
    cursor.execute(
        "INSERT INTO messages (agent_name, turn_id, message, timestamp) VALUES (?, ?, ?, ?)",
        (agent_name, turn_id, message, datetime.now().isoformat())
    )
    conn.commit()

def get_conversation_history(agent_name: str) -> list:
    """Load conversation from database"""
    cursor.execute(
        "SELECT turn_id, message FROM messages WHERE agent_name = ? ORDER BY turn_id",
        (agent_name,)
    )
    return cursor.fetchall()

def agent_chat(agent_name: str, turn_id: int, user_message: str) -> str:
    """Chat with persistence"""
    # Save user message
    save_message(agent_name, turn_id, f"USER: {user_message}")

    # Get history
    history = get_conversation_history(agent_name)
    context = "\n".join([f"Turn {t}: {msg}" for t, msg in history])

    # Generate response
    response = client.chat.completions.create(
        model="google/gemma-3n-e4b",
        messages=[
            {"role": "system", "content": f"You are {agent_name}. Previous conversation:\n{context}"},
            {"role": "user", "content": user_message}
        ],
        max_tokens=100
    )

    agent_response = response.choices[0].message.content

    # Save agent response
    save_message(agent_name, turn_id, f"AGENT: {agent_response}")

    return agent_response

# Test
print("="*60)
print("TAG 4: SQLITE PERSISTENZ")
print("="*60)

agent_name = "planner"

print("\n[Session 1]")
resp1 = agent_chat(agent_name, 1, "Plan a bank heist")
print(f"Response: {resp1[:100]}...")

resp2 = agent_chat(agent_name, 2, "What about security?")
print(f"Response: {resp2[:100]}...")

print("\n[Session 2 - After Restart]")
print("Loading from database...")
history = get_conversation_history(agent_name)
print(f"Found {len(history)} messages in database!")

for turn_id, msg in history:
    print(f"  Turn {turn_id}: {msg[:60]}...")

conn.close()
