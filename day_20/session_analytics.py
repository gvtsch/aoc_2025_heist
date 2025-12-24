"""
Day 20: Session Analytics (local copy from Day 19)
Analyzes and compares multiple heist sessions from SQLite database.
Standalone version for Interactive Dashboard.
"""

import sqlite3
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from collections import defaultdict, Counter
import json


class SessionAnalytics:
    """Analyzes session data from SQLite database."""

    def __init__(self, db_path: str = "heist_analytics.db"):
        self.db_path = db_path

    def _get_connection(self):
        """Get database connection."""
        return sqlite3.connect(self.db_path)

    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all sessions with basic info."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Try both column names for compatibility (total_turns or num_turns)
        try:
            cursor.execute("""
                SELECT
                    s.session_id,
                    s.start_time,
                    s.end_time,
                    s.total_turns,
                    s.status,
                    COUNT(m.id) as message_count
                FROM sessions s
                LEFT JOIN messages m ON s.session_id = m.session_id
                GROUP BY s.session_id
                ORDER BY s.start_time DESC
            """)
        except sqlite3.OperationalError:
            # Fallback to num_turns if total_turns doesn't exist
            cursor.execute("""
                SELECT
                    s.session_id,
                    s.start_time,
                    s.end_time,
                    s.num_turns,
                    s.status,
                    COUNT(m.id) as message_count
                FROM sessions s
                LEFT JOIN messages m ON s.session_id = m.session_id
                GROUP BY s.session_id
                ORDER BY s.start_time DESC
            """)

        sessions = []
        for row in cursor.fetchall():
            sessions.append({
                "session_id": row[0],
                "start_time": row[1],
                "end_time": row[2],
                "total_turns": row[3],
                "status": row[4],
                "message_count": row[5]
            })

        conn.close()
        return sessions

    def get_session_details(self, session_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific session."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Session metadata - try both column names for compatibility
        try:
            cursor.execute("""
                SELECT session_id, start_time, end_time, total_turns, status
                FROM sessions
                WHERE session_id = ?
            """, (session_id,))
        except sqlite3.OperationalError:
            # Fallback to num_turns if total_turns doesn't exist
            cursor.execute("""
                SELECT session_id, start_time, end_time, num_turns, status
                FROM sessions
                WHERE session_id = ?
            """, (session_id,))

        session_row = cursor.fetchone()
        if not session_row:
            conn.close()
            return {"error": "Session not found"}

        session_info = {
            "session_id": session_row[0],
            "start_time": session_row[1],
            "end_time": session_row[2],
            "total_turns": session_row[3],
            "status": session_row[4]
        }

        # Messages
        cursor.execute("""
            SELECT turn_id, agent_name, agent_role, message, timestamp
            FROM messages
            WHERE session_id = ?
            ORDER BY turn_id
        """, (session_id,))

        messages = []
        for row in cursor.fetchall():
            messages.append({
                "turn_id": row[0],
                "agent_name": row[1],
                "agent_role": row[2],
                "message": row[3],
                "timestamp": row[4]
            })

        session_info["messages"] = messages
        session_info["message_count"] = len(messages)

        # Tool usage - try tool_calls first, fallback to tool_usage
        try:
            cursor.execute("""
                SELECT agent_name, tool_name, success
                FROM tool_calls
                WHERE session_id = ?
                ORDER BY timestamp
            """, (session_id,))

            tool_usage = []
            for row in cursor.fetchall():
                tool_usage.append({
                    "agent": row[0],
                    "tool_name": row[1],
                    "success": bool(row[2]) if row[2] is not None else True
                })
        except sqlite3.OperationalError:
            # Fallback: use tool_usage table (older schema) - just basic info
            try:
                cursor.execute("""
                    SELECT tool_name, COUNT(*) as count
                    FROM tool_usage
                    WHERE session_id = ?
                    GROUP BY tool_name
                """, (session_id,))

                tool_usage = []
                for row in cursor.fetchall():
                    # Create synthetic per-agent data for compatibility
                    tool_usage.append({
                        "agent": "unknown",
                        "tool_name": row[0],
                        "success": True  # Assume success if not tracked
                    })
            except sqlite3.OperationalError:
                # No tool data available
                tool_usage = []

        session_info["tool_usage"] = tool_usage

        conn.close()
        return session_info

    def get_tool_statistics(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Get tool usage statistics, optionally filtered by session."""
        conn = self._get_connection()
        cursor = conn.cursor()

        if session_id:
            # Single session
            cursor.execute("""
                SELECT
                    tool_name,
                    COUNT(*) as total_calls,
                    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_calls,
                    AVG(CASE WHEN success = 1 THEN 1.0 ELSE 0.0 END) as success_rate
                FROM tool_usage
                WHERE session_id = ?
                GROUP BY tool_name
                ORDER BY total_calls DESC
            """, (session_id,))
        else:
            # All sessions
            cursor.execute("""
                SELECT
                    tool_name,
                    COUNT(*) as total_calls,
                    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_calls,
                    AVG(CASE WHEN success = 1 THEN 1.0 ELSE 0.0 END) as success_rate
                FROM tool_usage
                GROUP BY tool_name
                ORDER BY total_calls DESC
            """)

        stats = []
        for row in cursor.fetchall():
            stats.append({
                "tool_name": row[0],
                "total_calls": row[1],
                "successful_calls": row[2],
                "success_rate": round(row[3], 2)
            })

        conn.close()
        return {
            "session_id": session_id,
            "tool_statistics": stats
        }

    def get_agent_activity(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Get agent activity and interaction patterns."""
        conn = self._get_connection()
        cursor = conn.cursor()

        if session_id:
            # Single session
            cursor.execute("""
                SELECT agent_name, COUNT(*) as message_count
                FROM messages
                WHERE session_id = ?
                GROUP BY agent_name
                ORDER BY message_count DESC
            """, (session_id,))
        else:
            # All sessions
            cursor.execute("""
                SELECT agent_name, COUNT(*) as message_count
                FROM messages
                GROUP BY agent_name
                ORDER BY message_count DESC
            """)

        activity = []
        for row in cursor.fetchall():
            activity.append({
                "agent_name": row[0],
                "message_count": row[1]
            })

        # Interaction matrix (who follows whom in conversation)
        if session_id:
            cursor.execute("""
                SELECT
                    m1.agent_name as from_agent,
                    m2.agent_name as to_agent,
                    COUNT(*) as interaction_count
                FROM messages m1
                JOIN messages m2 ON m1.session_id = m2.session_id
                    AND m1.turn_id = m2.turn_id - 1
                WHERE m1.session_id = ?
                GROUP BY m1.agent_name, m2.agent_name
                ORDER BY interaction_count DESC
            """, (session_id,))
        else:
            cursor.execute("""
                SELECT
                    m1.agent_name as from_agent,
                    m2.agent_name as to_agent,
                    COUNT(*) as interaction_count
                FROM messages m1
                JOIN messages m2 ON m1.session_id = m2.session_id
                    AND m1.turn_id = m2.turn_id - 1
                GROUP BY m1.agent_name, m2.agent_name
                ORDER BY interaction_count DESC
            """)

        interactions = []
        for row in cursor.fetchall():
            interactions.append({
                "from_agent": row[0],
                "to_agent": row[1],
                "count": row[2]
            })

        conn.close()
        return {
            "session_id": session_id,
            "agent_activity": activity,
            "agent_interactions": interactions
        }

    def compare_sessions(self, session_ids: List[str]) -> Dict[str, Any]:
        """Compare multiple sessions side-by-side."""
        comparisons = {
            "sessions": [],
            "tool_comparison": {},
            "agent_comparison": {}
        }

        for session_id in session_ids:
            details = self.get_session_details(session_id)
            if "error" not in details:
                comparisons["sessions"].append({
                    "session_id": session_id,
                    "total_turns": details["total_turns"],
                    "message_count": details["message_count"],
                    "status": details["status"],
                    "start_time": details["start_time"]
                })

        # Tool usage comparison
        for session_id in session_ids:
            tool_stats = self.get_tool_statistics(session_id)
            comparisons["tool_comparison"][session_id] = tool_stats["tool_statistics"]

        # Agent activity comparison
        for session_id in session_ids:
            agent_activity = self.get_agent_activity(session_id)
            comparisons["agent_comparison"][session_id] = agent_activity["agent_activity"]

        return comparisons

    def get_session_timeline(self, session_id: str) -> List[Dict[str, Any]]:
        """Get chronological timeline of a session."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                turn_id,
                agent_name,
                agent_role,
                message,
                timestamp
            FROM messages
            WHERE session_id = ?
            ORDER BY turn_id
        """, (session_id,))

        timeline = []
        for row in cursor.fetchall():
            timeline.append({
                "turn_id": row[0],
                "agent": row[1],
                "role": row[2],
                "message": row[3],
                "timestamp": row[4]
            })

        conn.close()
        return timeline

    def get_success_metrics(self) -> Dict[str, Any]:
        """Calculate success metrics across all sessions."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Total sessions
        cursor.execute("SELECT COUNT(*) FROM sessions")
        total_sessions = cursor.fetchone()[0]

        # Completed sessions
        cursor.execute("SELECT COUNT(*) FROM sessions WHERE status = 'completed'")
        completed_sessions = cursor.fetchone()[0]

        # Average turns per session
        cursor.execute("SELECT AVG(total_turns) FROM sessions WHERE total_turns > 0")
        avg_turns = cursor.fetchone()[0] or 0

        # Tool success rates
        cursor.execute("""
            SELECT
                tool_name,
                AVG(CASE WHEN success = 1 THEN 1.0 ELSE 0.0 END) as success_rate,
                COUNT(*) as total_uses
            FROM tool_usage
            GROUP BY tool_name
            ORDER BY success_rate DESC
        """)

        tool_success = []
        for row in cursor.fetchall():
            tool_success.append({
                "tool_name": row[0],
                "success_rate": round(row[1], 2),
                "total_uses": row[2]
            })

        conn.close()

        return {
            "total_sessions": total_sessions,
            "completed_sessions": completed_sessions,
            "completion_rate": round(completed_sessions / total_sessions, 2) if total_sessions > 0 else 0,
            "average_turns_per_session": round(avg_turns, 1),
            "tool_success_rates": tool_success
        }

    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics for dashboard overview."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Total sessions
        cursor.execute("SELECT COUNT(*) FROM sessions")
        total_sessions = cursor.fetchone()[0]

        # Total messages
        cursor.execute("SELECT COUNT(*) FROM messages")
        total_messages = cursor.fetchone()[0]

        # Total tool uses
        cursor.execute("SELECT COUNT(*) FROM tool_usage")
        total_tools = cursor.fetchone()[0]

        # Completion rate
        cursor.execute("SELECT COUNT(*) FROM sessions WHERE status = 'completed'")
        completed_sessions = cursor.fetchone()[0]
        completion_rate = round((completed_sessions / total_sessions) * 100, 1) if total_sessions > 0 else 0

        conn.close()

        return {
            "total_sessions": total_sessions,
            "total_messages": total_messages,
            "total_tools": total_tools,
            "completion_percentage": completion_rate
        }


def main():
    """Demo: Session Analytics."""

    print("=" * 80)
    print("Day 18: Session Analytics Demo")
    print("=" * 80)

    analytics = SessionAnalytics()

    # List all sessions
    print("\n📋 All Sessions:")
    sessions = analytics.list_sessions()
    for session in sessions[:5]:  # Show first 5
        print(f"  {session['session_id']}: {session['total_turns']} turns, status: {session['status']}")

    if sessions:
        # Get details of most recent session
        latest_session = sessions[0]['session_id']
        print(f"\n📊 Session Details: {latest_session}")
        details = analytics.get_session_details(latest_session)
        print(f"  Messages: {details['message_count']}")
        print(f"  Tool Usage: {len(details['tool_usage'])} different tools")

        # Tool statistics
        print(f"\n🔧 Tool Statistics:")
        tool_stats = analytics.get_tool_statistics(latest_session)
        for stat in tool_stats['tool_statistics'][:5]:
            print(f"  {stat['tool_name']}: {stat['total_calls']} calls, {stat['success_rate']*100}% success")

        # Agent activity
        print(f"\n🤖 Agent Activity:")
        agent_activity = analytics.get_agent_activity(latest_session)
        for activity in agent_activity['agent_activity']:
            print(f"  {activity['agent_name']}: {activity['message_count']} messages")

        # Success metrics
        print(f"\n✅ Success Metrics:")
        metrics = analytics.get_success_metrics()
        print(f"  Total Sessions: {metrics['total_sessions']}")
        print(f"  Completion Rate: {metrics['completion_rate']*100}%")
        print(f"  Avg Turns/Session: {metrics['average_turns_per_session']}")

        # Compare sessions if we have at least 2
        if len(sessions) >= 2:
            print(f"\n🔍 Session Comparison:")
            comparison = analytics.compare_sessions([s['session_id'] for s in sessions[:2]])
            print(f"  Comparing {len(comparison['sessions'])} sessions")
            for sess in comparison['sessions']:
                print(f"    {sess['session_id']}: {sess['total_turns']} turns")


if __name__ == "__main__":
    main()
