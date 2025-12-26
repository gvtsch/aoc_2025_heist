"""
Day 22: Sabotage Detector
RAG-powered Mole Detection: Regel-basierte Pattern Analysis + LLM-Reasoning.
Besser als Zufall bei der Identifikation des Moles.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from typing import Dict, List, Tuple, Optional, Any
from collections import defaultdict, Counter
from datetime import datetime
import re
import math
import json
from openai import OpenAI


class SabotageDetector:
    """
    RAG-basierter Mole Detector: Kombiniert regelbasierte Pattern Analysis mit LLM-Reasoning.
    Retrieval: Pattern-basierte Verdachtsmomente
    Augmentation: Strukturierter Context für LLM
    Generation: LLM-basierte finale Analyse
    """

    def __init__(self, use_llm: bool = True, llm_base_url: str = "http://localhost:1234/v1", llm_config: Optional[Dict] = None):
        # Weights for rule-based suspicion score calculation
        self.weights = {
            "tool_usage_anomaly": 0.25,
            "timing_inconsistency": 0.30,
            "message_anomaly": 0.20,
            "information_quality": 0.25
        }

        # RAG settings
        self.use_llm = use_llm
        self.llm_weight = 0.4  # 40% LLM, 60% rules
        self.rule_weight = 0.6

        # LLM configuration (from agents_config.yaml or defaults)
        self.llm_config = llm_config or {
            "model": "local-model",
            "temperature": 0.3,
            "max_tokens": 500
        }

        # LLM client
        if self.use_llm:
            try:
                self.llm_client = OpenAI(
                    base_url=llm_base_url,
                    api_key="not-needed"
                )
            except Exception as e:
                print(f"Warning: LLM client initialization failed: {e}")
                self.use_llm = False

    def analyze_session(
        self,
        session_id: str,
        messages: List[Dict],
        tool_usage: List[Dict],
        agents: List[str]
    ) -> Dict[str, float]:
        """
        RAG-basierte Session-Analyse:
        1. Retrieval: Regelbasierte Pattern Detection
        2. Augmentation: Context-Aufbereitung für LLM
        3. Generation: LLM-basierte finale Scores
        
        Returns:
            Dict[agent_name, suspicion_score] - Score von 0.0 (innocent) bis 1.0 (highly suspicious)
        """
        # STEP 1: RETRIEVAL - Rule-based pattern analysis
        rule_scores = self._get_rule_based_scores(messages, tool_usage, agents)
        
        # STEP 2 & 3: AUGMENTATION + GENERATION - LLM analysis with retrieved context
        if self.use_llm and len(messages) > 0:
            llm_scores = self._get_llm_scores(messages, tool_usage, agents, rule_scores)
            
            # Combine rule-based and LLM scores
            combined_scores = {}
            for agent in agents:
                combined_scores[agent] = (
                    rule_scores.get(agent, 0.0) * self.rule_weight +
                    llm_scores.get(agent, 0.0) * self.llm_weight
                )
            return combined_scores
        else:
            # Fallback to pure rule-based
            return rule_scores
    
    def _get_rule_based_scores(
        self,
        messages: List[Dict],
        tool_usage: List[Dict],
        agents: List[str]
    ) -> Dict[str, float]:
        """Rule-based pattern detection (RETRIEVAL step)."""
        # Initialize scores
        suspicion_scores = {agent: 0.0 for agent in agents}

        # 1. Tool Usage Analysis
        tool_scores = self._analyze_tool_usage(tool_usage, agents)

        # 2. Timing Analysis
        timing_scores = self._analyze_timing_patterns(messages, agents)

        # 3. Message Anomaly Analysis
        message_scores = self._analyze_message_anomalies(messages, agents)

        # 4. Information Quality Analysis
        info_scores = self._analyze_information_quality(messages, agents)

        # Combine scores with weights
        for agent in agents:
            suspicion_scores[agent] = (
                tool_scores.get(agent, 0.0) * self.weights["tool_usage_anomaly"] +
                timing_scores.get(agent, 0.0) * self.weights["timing_inconsistency"] +
                message_scores.get(agent, 0.0) * self.weights["message_anomaly"] +
                info_scores.get(agent, 0.0) * self.weights["information_quality"]
            )

        return suspicion_scores

    def _analyze_tool_usage(
        self,
        tool_usage: List[Dict],
        agents: List[str]
    ) -> Dict[str, float]:
        """
        Analysiere Tool-Usage Patterns.
        Mole nutzt oft falsche Tools oder schlägt sie vor.
        """
        scores = {agent: 0.0 for agent in agents}

        if not tool_usage:
            return scores

        # Count tool usage per agent
        agent_tools = defaultdict(list)
        for usage in tool_usage:
            agent = usage.get("agent")
            tool = usage.get("tool_name")
            success = usage.get("success", True)

            if agent and tool:
                agent_tools[agent].append({
                    "tool": tool,
                    "success": success
                })

        # Calculate average success rate
        avg_success_rate = 0.0
        total_count = 0
        for agent, tools in agent_tools.items():
            if tools:
                successes = sum(1 for t in tools if t["success"])
                avg_success_rate += successes / len(tools)
                total_count += 1

        if total_count > 0:
            avg_success_rate /= total_count

        # Score agents below average
        for agent, tools in agent_tools.items():
            if not tools:
                continue

            successes = sum(1 for t in tools if t["success"])
            agent_success_rate = successes / len(tools)

            # Lower success rate = higher suspicion
            if agent_success_rate < avg_success_rate:
                deviation = (avg_success_rate - agent_success_rate) / avg_success_rate
                scores[agent] = min(deviation * 1.5, 1.0)  # Cap at 1.0

        return scores

    def _analyze_timing_patterns(
        self,
        messages: List[Dict],
        agents: List[str]
    ) -> Dict[str, float]:
        """
        Analysiere Timing-bezogene Keywords in Messages.
        Mole gibt oft falsche Timing-Informationen.
        """
        scores = {agent: 0.0 for agent in agents}

        timing_keywords = [
            "minute", "hour", "second", "time", "timing", "quick", "slow",
            "rush", "wait", "delay", "hurry", "patience", "schedule"
        ]

        contradiction_keywords = [
            "actually", "wait", "no", "wrong", "mistake", "correct",
            "change", "nevermind", "sorry", "my bad"
        ]

        agent_timing_mentions = defaultdict(int)
        agent_contradictions = defaultdict(int)

        for msg in messages:
            agent = msg.get("agent_name")
            content = msg.get("message", "").lower()

            if not agent:
                continue

            # Count timing-related mentions
            timing_count = sum(1 for keyword in timing_keywords if keyword in content)
            agent_timing_mentions[agent] += timing_count

            # Count contradictions
            contradiction_count = sum(1 for keyword in contradiction_keywords if keyword in content)
            agent_contradictions[agent] += contradiction_count

        # Agents with many timing mentions AND contradictions are suspicious
        max_timing = max(agent_timing_mentions.values()) if agent_timing_mentions else 1
        max_contradictions = max(agent_contradictions.values()) if agent_contradictions else 1

        for agent in agents:
            timing_ratio = agent_timing_mentions[agent] / max_timing if max_timing > 0 else 0
            contradiction_ratio = agent_contradictions[agent] / max_contradictions if max_contradictions > 0 else 0

            # High timing mentions + high contradictions = suspicious
            scores[agent] = (timing_ratio * 0.5 + contradiction_ratio * 0.5)

        return scores

    def _analyze_message_anomalies(
        self,
        messages: List[Dict],
        agents: List[str]
    ) -> Dict[str, float]:
        """
        Analysiere Message-Patterns.
        Mole zeigt oft ungewöhnliche Verhaltensmuster.
        """
        scores = {agent: 0.0 for agent in agents}

        # Count messages per agent
        agent_messages = defaultdict(list)
        for msg in messages:
            agent = msg.get("agent_name")
            content = msg.get("message", "")

            if agent:
                agent_messages[agent].append(content)

        # Calculate average message length
        all_lengths = []
        for agent, msgs in agent_messages.items():
            all_lengths.extend([len(msg) for msg in msgs])

        if not all_lengths:
            return scores

        avg_length = sum(all_lengths) / len(all_lengths)
        std_dev = math.sqrt(sum((l - avg_length) ** 2 for l in all_lengths) / len(all_lengths))

        # Analyze each agent
        for agent, msgs in agent_messages.items():
            if not msgs:
                continue

            agent_avg_length = sum(len(msg) for msg in msgs) / len(msgs)

            # Very long or very short messages = suspicious
            if std_dev > 0:
                deviation = abs(agent_avg_length - avg_length) / std_dev
                scores[agent] = min(deviation / 2.0, 1.0)  # Normalize

            # Check for hesitation markers
            hesitation_markers = ["hmm", "uh", "um", "wait", "let me think", "actually"]
            hesitation_count = sum(
                1 for msg in msgs for marker in hesitation_markers if marker in msg.lower()
            )

            if len(msgs) > 0:
                hesitation_ratio = hesitation_count / len(msgs)
                scores[agent] = max(scores[agent], hesitation_ratio)

        return scores

    def _analyze_information_quality(
        self,
        messages: List[Dict],
        agents: List[str]
    ) -> Dict[str, float]:
        """
        Analysiere Informationsqualität.
        Mole gibt oft vage oder falsche Informationen.
        """
        scores = {agent: 0.0 for agent in agents}

        # Keywords that indicate concrete information
        concrete_keywords = [
            "camera", "guard", "vault", "door", "window", "sensor",
            "alarm", "code", "key", "lock", "route", "entrance"
        ]

        # Keywords that indicate vagueness
        vague_keywords = [
            "maybe", "probably", "might", "could be", "not sure",
            "i think", "possibly", "perhaps", "unclear"
        ]

        agent_concrete = defaultdict(int)
        agent_vague = defaultdict(int)

        for msg in messages:
            agent = msg.get("agent_name")
            content = msg.get("message", "").lower()

            if not agent:
                continue

            # Count concrete information
            concrete_count = sum(1 for keyword in concrete_keywords if keyword in content)
            agent_concrete[agent] += concrete_count

            # Count vague language
            vague_count = sum(1 for keyword in vague_keywords if keyword in content)
            agent_vague[agent] += vague_count

        # Calculate suspicion scores
        for agent in agents:
            concrete = agent_concrete[agent]
            vague = agent_vague[agent]
            total = concrete + vague

            if total == 0:
                continue

            # High vagueness ratio = suspicious
            vagueness_ratio = vague / total
            scores[agent] = vagueness_ratio

        return scores

    def get_top_suspects(
        self,
        suspicion_scores: Dict[str, float],
        n: int = 1
    ) -> List[Tuple[str, float]]:
        """
        Hole die Top N verdächtigen Agents.

        Returns:
            List of (agent_name, suspicion_score) sorted by score descending
        """
        sorted_suspects = sorted(
            suspicion_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return sorted_suspects[:n]

    def suggest_mole(
        self,
        suspicion_scores: Dict[str, float]
    ) -> Tuple[str, float]:
        """
        Suggest who the mole is based on suspicion scores.

        Returns:
            (agent_name, confidence) where confidence is the suspicion score
        """
        top_suspect = self.get_top_suspects(suspicion_scores, n=1)[0]

        return top_suspect

    def get_detailed_analysis(
        self,
        session_id: str,
        messages: List[Dict],
        tool_usage: List[Dict],
        agents: List[str]
    ) -> Dict:
        """
        Detaillierte Analyse mit Breakdown aller Komponenten.
        """
        # Calculate individual scores
        tool_scores = self._analyze_tool_usage(tool_usage, agents)
        timing_scores = self._analyze_timing_patterns(messages, agents)
        message_scores = self._analyze_message_anomalies(messages, agents)
        info_scores = self._analyze_information_quality(messages, agents)

        # Calculate combined scores
        combined_scores = self.analyze_session(session_id, messages, tool_usage, agents)

        # Get suggestion
        suggested_mole, confidence = self.suggest_mole(combined_scores)

        return {
            "session_id": session_id,
            "suggested_mole": suggested_mole,
            "confidence": round(confidence, 3),
            "suspicion_scores": {
                agent: round(score, 3)
                for agent, score in combined_scores.items()
            },
            "score_breakdown": {
                agent: {
                    "tool_usage": round(tool_scores.get(agent, 0.0), 3),
                    "timing": round(timing_scores.get(agent, 0.0), 3),
                    "message_anomaly": round(message_scores.get(agent, 0.0), 3),
                    "information_quality": round(info_scores.get(agent, 0.0), 3),
                    "combined": round(combined_scores.get(agent, 0.0), 3)
                }
                for agent in agents
            },
            "analysis_weights": self.weights
        }
    
    def _get_llm_scores(
        self,
        messages: List[Dict],
        tool_usage: List[Dict],
        agents: List[str],
        rule_scores: Dict[str, float]
    ) -> Dict[str, float]:
        """
        LLM-basierte Analyse (AUGMENTATION + GENERATION).
        Nutzt regelbasierte Scores als Retrieved Context.
        """
        # Build context from retrieved patterns
        context = self._build_rag_context(messages, tool_usage, agents, rule_scores)
        
        # Build conversation for LLM
        conversation_text = "\n".join([
            f"{msg.get('agent_name', 'unknown')}: {msg.get('message', '')}"
            for msg in messages[:50]  # Limit to first 50 messages
        ])
        
        # RAG Prompt
        prompt = f"""You are an expert detective analyzing a heist mission for signs of sabotage.

RETRIEVED SUSPICIOUS PATTERNS:
{context}

AGENT CONVERSATION:
{conversation_text}

TASK:
Analyze the conversation and the suspicious patterns above. For each agent, estimate their sabotage probability (0.0 = innocent, 1.0 = definitely sabotaging).

Consider:
- Do they give vague or conflicting information?
- Do they cause delays or confusion?
- Are their tool failures suspicious?
- Do they contradict others or themselves?

Respond ONLY with a JSON object mapping agent names to scores:
{{"agent_name": score, ...}}

Example: {{"planner": 0.2, "hacker": 0.8, "safecracker": 0.3}}
"""
        
        try:
            response = self.llm_client.chat.completions.create(
                model=self.llm_config['model'],
                messages=[
                    {"role": "system", "content": "You are a detective analyzing agent behavior for sabotage. Respond only with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.llm_config.get('temperature', 0.3),
                max_tokens=self.llm_config.get('max_tokens', 500)
            )
            
            # Parse LLM response
            llm_output = response.choices[0].message.content.strip()
            
            # Extract JSON from response (handle markdown code blocks)
            if "```json" in llm_output:
                llm_output = llm_output.split("```json")[1].split("```")[0].strip()
            elif "```" in llm_output:
                llm_output = llm_output.split("```")[1].split("```")[0].strip()
            
            llm_scores = json.loads(llm_output)
            
            # Normalize scores to 0-1 range
            normalized_scores = {}
            for agent in agents:
                score = llm_scores.get(agent, 0.0)
                normalized_scores[agent] = max(0.0, min(1.0, float(score)))
            
            return normalized_scores
            
        except Exception as e:
            print(f"Warning: LLM analysis failed: {e}")
            # Fallback to rule-based scores
            return rule_scores
    
    def _build_rag_context(
        self,
        messages: List[Dict],
        tool_usage: List[Dict],
        agents: List[str],
        rule_scores: Dict[str, float]
    ) -> str:
        """Build structured context from retrieved patterns for LLM."""
        context_parts = []
        
        # Top suspects from rule-based analysis
        sorted_suspects = sorted(rule_scores.items(), key=lambda x: x[1], reverse=True)[:3]
        context_parts.append("TOP SUSPECTS (Rule-based):")
        for agent, score in sorted_suspects:
            context_parts.append(f"  - {agent}: {score:.2%} suspicion")
        
        # Tool failures per agent
        tool_failures = defaultdict(int)
        tool_total = defaultdict(int)
        for usage in tool_usage:
            agent = usage.get("agent", "unknown")
            tool_total[agent] += 1
            if not usage.get("success", True):
                tool_failures[agent] += 1
        
        if tool_failures:
            context_parts.append("\nTOOL FAILURES:")
            for agent, failures in tool_failures.items():
                total = tool_total[agent]
                context_parts.append(f"  - {agent}: {failures}/{total} tools failed")
        
        # Timing keywords per agent
        timing_keywords = ["minute", "hour", "time", "rush", "wait", "delay", "timing"]
        timing_mentions = defaultdict(int)
        for msg in messages:
            agent = msg.get("agent_name", "unknown")
            message = msg.get("message", "").lower()
            timing_mentions[agent] += sum(1 for kw in timing_keywords if kw in message)
        
        if any(timing_mentions.values()):
            context_parts.append("\nTIMING-RELATED MENTIONS:")
            for agent, count in sorted(timing_mentions.items(), key=lambda x: x[1], reverse=True)[:3]:
                if count > 0:
                    context_parts.append(f"  - {agent}: {count} timing mentions")
        
        return "\n".join(context_parts)


# Demo
if __name__ == "__main__":
    detector = SabotageDetector()

    print("=" * 80)
    print("Day 22: Sabotage Detector Demo")
    print("=" * 80)

    # Mock data
    agents = ["planner", "hacker", "safecracker", "getaway_driver"]

    messages = [
        {"agent_name": "planner", "message": "We need to disable camera 3 at the entrance"},
        {"agent_name": "hacker", "message": "Actually, I think the timing might be off, maybe wait 5 more minutes"},
        {"agent_name": "safecracker", "message": "I'll work on the vault combination"},
        {"agent_name": "hacker", "message": "Hmm, not sure about the guard schedule, might be different"},
        {"agent_name": "getaway_driver", "message": "Car is ready at the north exit"},
        {"agent_name": "hacker", "message": "Wait, let me think about this timing again"},
    ]

    tool_usage = [
        {"agent": "planner", "tool_name": "calculator", "success": True},
        {"agent": "hacker", "tool_name": "file_reader", "success": False},
        {"agent": "hacker", "tool_name": "database_query", "success": False},
        {"agent": "safecracker", "tool_name": "calculator", "success": True},
        {"agent": "getaway_driver", "tool_name": "file_reader", "success": True},
    ]

    # Analyze
    analysis = detector.get_detailed_analysis(
        "demo_session",
        messages,
        tool_usage,
        agents
    )

    print(f"\n🎯 Suggested Mole: {analysis['suggested_mole']}")
    print(f"   Confidence: {analysis['confidence']*100:.1f}%")

    print(f"\n📊 Suspicion Scores:")
    for agent, score in analysis['suspicion_scores'].items():
        bar = "█" * int(score * 20)
        print(f"   {agent:20s} {score:.3f} {bar}")

    print(f"\n🔍 Detailed Breakdown for {analysis['suggested_mole']}:")
    breakdown = analysis['score_breakdown'][analysis['suggested_mole']]
    for component, score in breakdown.items():
        if component != 'combined':
            print(f"   {component:25s} {score:.3f}")

    print(f"\n⚖️  Analysis Weights:")
    for component, weight in analysis['analysis_weights'].items():
        print(f"   {component:25s} {weight:.2f}")
