#!/usr/bin/env python3
"""
Day 19: Initialize Analytics Database
Creates analytics database with Day 18/19 format
"""

import sqlite3
import os

DB_PATH = os.getenv("DATABASE_PATH", "./heist_analytics.db")

def init_database():
    """Initialize all required tables"""

    # Ensure directory exists (if DB_PATH has directory component)
    db_dir = os.path.dirname(DB_PATH)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print(f"📊 Initializing database at: {DB_PATH}")

    # Sessions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            start_time REAL NOT NULL,
            end_time REAL,
            status TEXT DEFAULT 'active',
            total_turns INTEGER DEFAULT 0,
            success BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("✓ Created sessions table")

    # Agents table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            agent_name TEXT NOT NULL,
            role TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id)
        )
    """)
    print("✓ Created agents table")

    # Actions/Turns table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            turn_number INTEGER NOT NULL,
            agent_name TEXT NOT NULL,
            action_type TEXT,
            timestamp REAL NOT NULL,
            details TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id)
        )
    """)
    print("✓ Created actions table")

    # Tool calls table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tool_calls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            agent_name TEXT NOT NULL,
            tool_name TEXT NOT NULL,
            timestamp REAL NOT NULL,
            success BOOLEAN DEFAULT 1,
            execution_time REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id)
        )
    """)
    print("✓ Created tool_calls table")

    # Messages table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            turn_id INTEGER,
            agent_name TEXT NOT NULL,
            agent_role TEXT,
            message TEXT NOT NULL,
            timestamp REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id)
        )
    """)
    print("✓ Created messages table")

    # Tool usage summary table (for tool-stats endpoint)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tool_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            tool_name TEXT NOT NULL,
            operation TEXT DEFAULT 'execute',
            usage_count INTEGER DEFAULT 0,
            success BOOLEAN DEFAULT 1,
            avg_execution_time REAL,
            success_rate REAL,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id)
        )
    """)
    print("✓ Created tool_usage table")

    # Game data table (for Mole Game)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS games (
            game_id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            mole_agent TEXT NOT NULL,
            sabotage_pattern TEXT NOT NULL,
            detected BOOLEAN DEFAULT 0,
            detected_agent TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id)
        )
    """)
    print("✓ Created games table")

    # Create indexes for performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_actions_session ON actions(session_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tool_calls_session ON tool_calls(session_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_actions_timestamp ON actions(timestamp)")
    print("✓ Created indexes")

    conn.commit()

    # Insert demo data
    print("\n📝 Inserting demo data...")

    demo_sessions = [
        ("demo_session_001", 1734000000, 1734003600, "completed", 45, 1),
        ("demo_session_002", 1734010000, 1734012800, "completed", 38, 1),
        ("demo_session_003", 1734020000, 1734023400, "completed", 52, 0),
    ]

    cursor.executemany("""
        INSERT OR IGNORE INTO sessions (session_id, start_time, end_time, status, total_turns, success)
        VALUES (?, ?, ?, ?, ?, ?)
    """, demo_sessions)

    # Demo agents
    demo_agents = [
        ("demo_session_001", "Communicator", "communication"),
        ("demo_session_001", "Planner", "planning"),
        ("demo_session_001", "Executor", "execution"),
        ("demo_session_002", "Scout", "reconnaissance"),
        ("demo_session_002", "Hacker", "technical"),
        ("demo_session_002", "Driver", "logistics"),
    ]

    cursor.executemany("""
        INSERT OR IGNORE INTO agents (session_id, agent_name, role)
        VALUES (?, ?, ?)
    """, demo_agents)

    # Demo tool calls
    import random
    tools = ["search_memory", "create_plan", "execute_action", "communicate", "analyze"]

    for session_id, _, _, _, turns, _ in demo_sessions:
        agents_for_session = [a[1] for a in demo_agents if a[0] == session_id]

        if not agents_for_session:
            # Default agents if none found
            agents_for_session = ["Agent1", "Agent2", "Agent3"]

        for turn in range(turns):
            agent = random.choice(agents_for_session)
            tool = random.choice(tools)
            timestamp = 1734000000 + (turn * 60)

            cursor.execute("""
                INSERT INTO tool_calls (session_id, agent_name, tool_name, timestamp, execution_time)
                VALUES (?, ?, ?, ?, ?)
            """, (session_id, agent, tool, timestamp, random.uniform(0.1, 2.0)))

    # Demo messages with turn_id and agent_role
    demo_messages = [
        ("demo_session_001", 1, "Communicator", "communication", "Let's start planning the vault entry.", 1734000000),
        ("demo_session_001", 2, "Planner", "planning", "I'll create the master plan.", 1734000060),
        ("demo_session_001", 3, "Executor", "execution", "Ready to execute when you are.", 1734000120),
        ("demo_session_002", 1, "Scout", "reconnaissance", "Checking the perimeter.", 1734010000),
        ("demo_session_002", 2, "Hacker", "technical", "Systems look vulnerable.", 1734010060),
        ("demo_session_002", 3, "Driver", "logistics", "Getaway route secured.", 1734010120),
    ]

    cursor.executemany("""
        INSERT INTO messages (session_id, turn_id, agent_name, agent_role, message, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    """, demo_messages)

    # Create tool_usage summaries from tool_calls
    cursor.execute("""
        INSERT INTO tool_usage (session_id, tool_name, operation, usage_count, avg_execution_time, success_rate)
        SELECT
            session_id,
            tool_name,
            'execute' as operation,
            COUNT(*) as usage_count,
            AVG(execution_time) as avg_execution_time,
            AVG(CASE WHEN success = 1 THEN 1.0 ELSE 0.0 END) as success_rate
        FROM tool_calls
        GROUP BY session_id, tool_name
    """)

    conn.commit()
    print("✓ Inserted demo data")

    # Verify
    cursor.execute("SELECT COUNT(*) FROM sessions")
    session_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM tool_calls")
    tool_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM messages")
    message_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM tool_usage")
    tool_usage_count = cursor.fetchone()[0]

    print(f"\n✅ Database initialized successfully!")
    print(f"   Sessions: {session_count}")
    print(f"   Tool calls: {tool_count}")
    print(f"   Messages: {message_count}")
    print(f"   Tool usage summaries: {tool_usage_count}")

    conn.close()

if __name__ == "__main__":
    init_database()
