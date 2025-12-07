Das siebte Türchen birgt eine Multi-Agenten-Konversation. Ich lasse mehrere Agenten miteinander sprechen. Ziel ist es, ein kleines Multi-Agenten-System, in dem drei verschiedene Rollen/Persona/Agenten gemeinsem den Banküberfall planen bzw. sich unterhalten.

Eine Anmerkung vorweg: Ich nutze häufig defn Begriff Agent in diesem Projekt. Im engeren Sinne sind unsere Agenten allerdings keine. Es sind eher Rollen, die jeweils vom LLM simuliert werden. Jeder "Agent" bekommt bekommt eine eigene Persona und reagiert auf den Gesprächskontext, aber alle Antworten kommen letztlich vom gleichen Sprachmodell. Für echte Multi-Agenten-System bräuchte jeder Agent eine eigene Logik, Speicher und vielleicht sogar eigene Ziele.

Das initialisieren des lokalen LLMs erspare ich uns und beginne direkt mit der MultiAgentSystem-Klasse.
Heute kommen dann auch schon manche Konzepte der letzten Tage zum Tragen. Zum Beispiel die Personas oder der Conversation Memory.

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

Die drei Personas sind denke ich selbsterklärend: Planner, Hacker und Safecracker. Das hatten wir schon. 

```python
AGENTS = {
    "planner": "You are the Planner. Be strategic and coordinate the team.",
    "hacker": "You are the Hacker. Focus on technical security aspects.",
    "safecracker": "You are the Safecracker. Expert in physical security."
}
```

Die Konversation wird ebenfalls wie gehabt gespeichert. Neu hier ist, dass der Kontext, den wir dem LLM übergeben einzig aus den letzten 3 Nachrichten besteht. Eine Art Mini-Gedächtnis, sodass jeder Agent weiß, was aktuell diskutiert wird.

```python
# Build context: recent 3 messages
recent = self.conversation[-3:] if self.conversation else []
context = "\n".join([
    f"{msg['agent']}: {msg['message']}"
    for msg in recent
])
``` 

Das Konzept der Unterhaltung ist aktuell noch ein einfaches: Es ist rundenbasiert und jeder kommt der Reihe nach dran. Obwohl es so vergleichsweise starr ist, entsteht dennoch eine Team-Dynamik, weil die Agenten aufeinander reagieren und einen Plan entwickeln.

In der ersten Runde gibt es einen speziellen Start-Prompt, um die Konverastion einzuleiten. Danach bekommen dann wie gesagt die Agenten mit ihrem Mini-Gedächtnis den Gesprächsverlauf als Kontext und sollen darauf reagieren. 

Und dann wird wie üblich das LLM mit einem Prompt kontaktiert und die Response im Memory gespeichert. 

Das zieht sich dann Runde für Runde hin, so lange man neue Runden anstößt. Bei einer neuen Runde muss man allerdings den start_turn übergeben, sonst beginnt die Konversation von vorne.

Das habe ich natürlich auch getestet:

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

Das Ergebnis ist dann nun etwas länger. Ich füge es dennoch ein:

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

Es fällt vermutlich direkt auf, dass die Responses abgeschnitten sind. Das liegt schlicht daran, dass nur 120 Token als Antwort erlaube. Sonst wird es für die einfachen Testzwecke viel zu lang.
Man sieht meiner Meinung auch schön, wie sich die Konversation entwickelt und aufeinander aufbaut. Sie greifen Vorschläge der anderen auf, ergänzen sie und entwickeln gemeinsam eine Strategie, ohne einer zentralen Steuerung. Wenn du das in der Form nicht nachvollziehen kannst, dann erlaube deiner Reponse mal testweise weitere Tokens.

## Zusammenfassung
Heute haben wir ein kleines Multi-Agenten-System gebaut, bei dem drei Agenten rundenbasiert miteinander sprechen und gemeinsam einen Plan entwickeln. Jeder bringt seine Perspektive ein und das Gespräch baut aufeinander auf. 

## Ausblick
Ein professioneller Ausblick für so ein System wäre zum Beispiel die Simulation von Krisenmanagement: Mehrere KI-Agenten übernehmen verschiedene Rollen (Leitung, Kommunikation, Technik, Sicherheit) und entwickeln gemeinsam Strategien, um auf Notfälle oder komplexe Situationen zu reagieren. So kann man Teamdynamik, Entscheidungsfindung und Koordination in virtuellen Szenarien testen und verbessern – etwa für Trainings, Forschung oder die Entwicklung von Assistenzsystemen.


