---
title: "Day 22: Sabotage Detection"
date: 2025-12-22
tags:
  - python
  - aoc
  - adventofcode
  - aiagents
  - ml
  - detection
toc: true
---

Alle Dokumente zu diesem Beitrag sind in meinem [repository](https://github.com/gvtsch/aoc_2025_heist/tree/main/day_22) zu finden.

Tag 22 macht das System "intelligent". Tag 20 hat das interaktive Dashboard und das Maulwurf Spiel gebracht. Der Maulwurf wird dabei zufällig ausgewählt und bekommt geheime Sabotage Instruktionen. Der User muss dann manuell raten wer der Maulwurf ist. Das Problem dabei ist offensichtlich. Bei vier Agents liegt die Trefferquote bei reinem Raten bei 25 Prozent. Tag 22 löst dieses "Problem" mit automatischer Detektion. Das System analysiert das Verhalten der Agents und sucht nach verdächtigen Mustern. Das können wir natürlich auch manuell machen, aber dann hätten wir nicht mehr viel zu tun. Die programmatische Lösung kombiniert regelbasierte Analysen mit einem LLM. Besser als Zufall und intelligenter als reine Regeln. Hoffe ich zumindest 😅

## Maulwurf Game Mechanics

Tag 20 hat die Basis Mechanik für das Maulwurf Game eingeführt.

Bei Session Start wird ein zufälliger Agent als Maulwurf ausgewählt. Dieser Agent bekommt ein Sabotage Pattern zugewiesen. Es gibt dabei fünf verschiedene Strategien. Die anderen Agents wissen natürlich nicht wer der Maulwurf ist.

Der Maulwurf erhält seine geheimen Instruktionen via System Prompt. Diese Instruktionen werden automatisch beim ersten Response in den Context injiziert.

Die fünf Sabotage Strategien funktionieren unterschiedlich. Bei `TIMING_ERRORS` gibt der Maulwurf absichtlich falsche Zeitschätzungen und widerspricht sich später selbst. Bei `FALSE_INFO` streut er subtile Fehlinformationen über Guard Patterns und Sicherheitssysteme. Bei `COORDINATION_CHAOS` gibt er verwirrende und widersprüchliche Koordinations Anweisungen. Bei `SUBTLE_DELAYS` zögert er bewusst, stellt unnötig viele Fragen und verlangsamt dadurch die Planung. Bei `WRONG_TOOLS` schlägt er Tools vor die einfach nicht zum Job passen.

Nach Ende des Überfalls kann der User seinen Verdacht angeben. Der `HeistController` evaluiert dann das Ergebnis. `SUCCESS` bedeutet überraschenderweise der User hat richtig geraten. `FAILURE` bedeutet er lag falsch. `BUSTED` bedeutet der User hat gar keinen Verdacht geäußert.

## Tool Execution

Tag 22 reaktiviert außerdem die Tool-Execution, die seit Tag 16 inaktiv war. Tag 13 hatte bereits vollständige Tool-Calling Funktionalität mit dem `[OAUTH_TOOL:name:param]` Pattern. Tag 16 integrierte dann das System, aber Tools wurden nur im System Prompt erwähnt und nie tatsächlich ausgeführt.

Jetzt können Agents Tools mit dem `[TOOL:name:param]` Pattern aufrufen. Der **safecracker** kann `[TOOL:calculator:50*2]` nutzen. Der **hacker** kann `[TOOL:file_reader:vault_specs.txt]` nutzen. Der **intel** kann `[TOOL:database_query:SELECT * FROM guards WHERE shift='night']` nutzen.

Die Tool-Calls werden automatisch erkannt, mit OAuth ausgeführt und die Ergebnisse in der `tool_usage` Tabelle geloggt. Das Dashboard zeigt nun Tool-Statistiken an. Diese Daten fließen in die AI Detection ein, da ungewöhnliche Tool-Usage ein wichtiger Indikator für Sabotage ist.

## AI Detection System

Heute fügen wir eine automatische Maulwurf Detection hinzu. Das System analysiert das Verhalten der Agents während des Überfalls und berechnet Suspicion Scores. Dabei wird ein [[RAG]] Ansatz verwendet der regelbasierte Pattern Detection mit LLM Reasoning kombiniert.

Der Ablauf hat drei Schritte. Zuerst Retrieval, bei dem regelbasierte Analysen verdächtige Patterns in Messages und Tool Usage finden. Dann Augmentation, bei der diese Patterns als strukturierter Context aufbereitet werden. Zuletzt Generation, bei der ein LLM die Konversation mit diesem Context analysiert und fundierte Scores generiert.

Reine Regeln wären zu starr und würden subtile Sabotage verpassen. Reine LLMs halluzinieren und erfinden Verdachtsmomente die nicht existieren. Die Kombination aus beidem nutzt die Stärken beider Ansätze. Regeln finden messbare Anomalien, das LLM versteht Kontext und Nuancen.

Die finale Kombination verwendet 60 Prozent regelbasierte Scores und 40 Prozent LLM Scores. Diese Gewichtung ergibt hoffentlich eine robuste Detection, die besser funktioniert als jeder Ansatz alleine. Wir werden sehen 🤷‍♂️

## Detection Signals

Es gibt vier Hauptkategorien für die regelbasierte Pattern Detection.

* **Tool Usage Anomalies** haben ein Gewicht von 25 Prozent. Dabei wird analysiert ob ein Agent eine niedrigere Success Rate hat als der Durchschnitt. Ob er falsche Tools vorschlägt oder ob seine Tool Patterns ungewöhnlich sind.
* **Timing Inconsistencies** haben ein Gewicht von 30 Prozent. Hier werden Timing Keywords in Messages gezählt. Widersprüche und Korrekturen werden erkannt. Patterns wie _wait actually_ oder _nevermind_ sind verdächtig.
* **Message Anomalies** haben ein Gewicht von 20 Prozent. Die Nachrichten-Länge wird analysiert. Hinweise auf Zögern wie _hmm_, _uh_ oder _let me think_ werden gezählt. Abweichende Sprachmuster fallen auf.
* **Information Quality** hat ebefalls ein Gewicht von 25 Prozent. Das System unterscheidet zwischen vagen und konkreten Informationen. Keywords wie _maybe_, _probably_ oder _not sure_ sind Warnsignale. Wenig spezifische Details sind verdächtig.

Diese Signale bilden den Retrieved Context (das **R** in RAG), der dann dem LLM zur Verfügung gestellt wird. Die Gewichtungen sind willkürlich gewählt worden, durch mich. Warum? Einfach darum. Wir werden sehen, ob das funktioniert.

## RAG basierter Sabotage Detector

Die `SabotageDetector`-Klasse kombiniert regelbasierte Analysen mit einem LLM. Ich habe es schon lange nicht mehr erwähnt, aber hier wird auch wieder das lokale LLM genutzt 😉 

```python
class SabotageDetector:
    def __init__(self, use_llm: bool = True):
        # Weights for rule-based scoring
        self.weights = {
            "tool_usage_anomaly": 0.25,
            "timing_inconsistency": 0.30,
            "message_anomaly": 0.20,
            "information_quality": 0.25
        }

        # RAG settings
        self.use_llm = use_llm
        self.llm_weight = 0.4  # 40% LLM
        self.rule_weight = 0.6  # 60% Rules

        # LLM client (LM Studio)
        self.llm_client = OpenAI(
            base_url="http://localhost:1234/v1",
            api_key="not-needed"
        )

    def analyze_session(
        self,
        session_id: str,
        messages: List[Dict],
        tool_usage: List[Dict],
        agents: List[str]
    ) -> Dict[str, float]:
        # STEP 1: RETRIEVAL
        rule_scores = self._get_rule_based_scores(
            messages, tool_usage, agents
        )

        # STEP 2 & 3: AUGMENTATION + GENERATION
        if self.use_llm:
            llm_scores = self._get_llm_scores(
                messages, tool_usage, agents, rule_scores
            )

            # Combine scores
            combined_scores = {}
            for agent in agents:
                combined_scores[agent] = (
                    rule_scores[agent] * self.rule_weight +
                    llm_scores[agent] * self.llm_weight
                )
            return combined_scores
        else:
            return rule_scores
```

Die Weights für das rule based scoring werden in einem Dictionary definiert. Die RAG Settings werden konfiguriert. Das LLM Weight ist auf 40 Prozent gesetzt und das Rule Weight auf 60 Prozent. Der LLM Client verbindet sich zu einer LM Studio Instanz auf localhost Port 1234.

Die `analyze_session` Methode führt den kompletten Ablauf aus. Schirtt 1 ist Retrieval, bei dem die regelbasierte Pattern Detection die `rule_scores` liefert. Schritt 2 und 3 sind Augmentation und Generation. Falls das LLM aktiviert ist werden zusätzlich LLM Scores berechnet. Die finalen Scores werden dann aus 60 Prozent Rules und 40 Prozent LLM kombiniert und ergeben die `combined_scores`.

Ich bin gespannt wie, oder viel mehr ob, sich das so aufgeht. Kommen wir erstmal zur weiteren Implementierung.

### Schritt 1 Retrieval

Im ersten Schritt werden regelbasierte Analysen durchgeführt um verdächtige Muster zu identifizieren. Diese bilden die Grundlage für die spätere LLM-Analyse.

#### Regelbasierte Score-Berechnung

Diese Methode berechnet die individuellen Scores für jeden Agent. Die Tool Usage wird analysiert, die Timing Patterns werden untersucht, Message Anomalies werden erkannt und die Information Quality wird bewertet.

```python
def _get_rule_based_scores(self, messages, tool_usage, agents):
    # Calculate individual scores
    tool_scores = self._analyze_tool_usage(tool_usage, agents)
    timing_scores = self._analyze_timing_patterns(messages, agents)
    message_scores = self._analyze_message_anomalies(messages, agents)
    info_scores = self._analyze_information_quality(messages, agents)

    # Combine with weights
    suspicion_scores = {}
    for agent in agents:
        suspicion_scores[agent] = (
            tool_scores[agent] * self.weights["tool_usage_anomaly"] +
            timing_scores[agent] * self.weights["timing_inconsistency"] +
            message_scores[agent] * self.weights["message_anomaly"] +
            info_scores[agent] * self.weights["information_quality"]
        )

    return suspicion_scores
```

Diese Scores bilden den Retrieved Context. Es sind messbare Verdachtsmomente die später dem LLM helfen werden besser zu urteilen. 

Die einzelnen Scores werden dann mit den definierten Gewichten kombiniert. Jeder Agent bekommt dabei einen Suspicion Score zwischen 0.0 und 1.0.

#### Tool Usage Analysis

Für jeden Agent wird die Tool Usage gezählt. Dabei werden sowohl Success als auch Failure Events getrackt.

```python
def _analyze_tool_usage(self, tool_usage, agents):
    # Count tool usage per agent
    agent_tools = defaultdict(list)
    for usage in tool_usage:
        agent_tools[usage["agent"]].append({
            "tool": usage["tool_name"],
            "success": usage["success"]
        })

    # Calculate average success rate
    total_tools = sum(len(tools) for tools in agent_tools.values())
    total_success = sum(
        sum(1 for t in tools if t["success"])
        for tools in agent_tools.values()
    )
    avg_success_rate = total_success / total_tools if total_tools > 0 else 0

    # Score agents below average
    scores = {agent: 0.0 for agent in agents}
    for agent, tools in agent_tools.items():
        if len(tools) == 0:
            continue

        successes = sum(1 for t in tools if t["success"])
        agent_success_rate = successes / len(tools)

        if agent_success_rate < avg_success_rate:
            deviation = (avg_success_rate - agent_success_rate) / avg_success_rate
            scores[agent] = min(deviation * 1.5, 1.0)

    return scores
```

Die durchschnittliche Success Rate wird über alle Agents hinweg berechnet. Das gibt uns einen Baseline-Wert.

Agents mit einer unterdurchschnittlichen Tool Success Rate sind verdächtig. Der Grund ist, der Maulwurf schlägt vermutlich absichtlich falsche Tools vor oder nutzt die richtigen Tools falsch um die Mission zu sabotieren. 

Die Abweichung vom Durchschnitt wird berechnet und mit Faktor 1.5 multipliziert. Dieser Verstärkungsfaktor ist willkürlich gewählt und macht die Detection empfindlicher. Eine Abweichung von 20 Prozent wird dadurch zu einem Score von 0.3 statt 0.2. Das Maximum ist auf 1.0 begrenzt. Eventuell werden wir feststellen, dass wir den Faktor wieder auf 1.0 korrigieren müssen.

#### Timing Analysis

Die Timing Keywords werden als Liste definiert. Wörter wie _minute_, _hour_, _time_, _rush_, _wait_ und _delay_. Diese Liste ist simpel und könnte mit NLP-Bibliotheken wie `spaCy` oder `sentence-transformers` erweitert werden. Damit würde man auch Synonyme und verwandte Begriffe automatisch erfassen. Für diesen Prototyp reicht aber die einfache Keyword-Liste.

```python
def _analyze_timing_patterns(self, messages, agents):
    timing_keywords = ["minute", "hour", "time", "rush", "wait", "delay"]
    contradiction_keywords = ["actually", "wait", "wrong", "change", "nevermind"]

    agent_timing_mentions = defaultdict(int)
    agent_contradictions = defaultdict(int)

    for msg in messages:
        text = msg["message"].lower()
        agent = msg["agent_name"]

        timing_count = sum(1 for kw in timing_keywords if kw in text)
        contradiction_count = sum(1 for kw in contradiction_keywords if kw in text)

        agent_timing_mentions[agent] += timing_count
        agent_contradictions[agent] += contradiction_count

    # Normalize
    max_timing = max(agent_timing_mentions.values()) if agent_timing_mentions else 1
    max_contradictions = max(agent_contradictions.values()) if agent_contradictions else 1

    scores = {}
    for agent in agents:
        timing_ratio = agent_timing_mentions[agent] / max_timing
        contradiction_ratio = agent_contradictions[agent] / max_contradictions
        scores[agent] = (timing_ratio * 0.5 + contradiction_ratio * 0.5)

    return scores
```

Die Widersprüche werden ebenfalls definiert. Wörter wie _actually_, _wait_, _wrong_, _change_ und _nevermind_.

Für jede Message wird dann gezählt wie oft diese Keywords vorkommen. Die Anzahl der Timing-Erwähnungen und Widersprüche wird für jeden Agent zusammengezählt.

Agents die häufig über Timing sprechen und sich dabei oft widersprechen sind besonders verdächtig. Das ist ein typisches Muster der Timing Error Sabotage Strategie.

Die Werte werden am Ende normalisiert und auf einen Bereich von 0.0 bis 1.0 gebracht. Der endgültige Score setzt sich zu je 50 Prozent aus dem Timing-Verhältnis und dem Widerspruchs-Verhältnis zusammen.

#### Message Anomaly Analysis

Für jeden Agenten wird die durchschnittliche Nachrichten-Länge berechnet und mit dem Gesamtdurchschnitt verglichen.

```python
def _analyze_message_anomalies(self, messages, agents):
    agent_messages = defaultdict(list)
    for msg in messages:
        agent_messages[msg["agent_name"]].append(msg["message"])

    # Calculate average message length
    all_lengths = [len(msg["message"]) for msg in messages]
    avg_length = sum(all_lengths) / len(all_lengths) if all_lengths else 0
    std_dev = (sum((l - avg_length) ** 2 for l in all_lengths) / len(all_lengths)) ** 0.5

    scores = {agent: 0.0 for agent in agents}

    for agent, msgs in agent_messages.items():
        agent_avg_length = sum(len(msg) for msg in msgs) / len(msgs)

        # Deviation from average
        if std_dev > 0:
            deviation = abs(agent_avg_length - avg_length) / std_dev
            scores[agent] = min(deviation / 2.0, 1.0)

        # Hesitation markers
        hesitation_markers = ["hmm", "uh", "um", "wait", "let me think"]
        hesitation_count = sum(
            msg.lower().count(marker)
            for msg in msgs
            for marker in hesitation_markers
        )
        hesitation_ratio = hesitation_count / len(msgs)

        scores[agent] = max(scores[agent], hesitation_ratio)

    return scores
```

Die Abweichung vom Gesamtdurchschnitt wird dann ermittelt. Sehr lange Messages können verdächtig sein weil der Maulwurf zu viel erklärt. Sehr kurze Messages können verdächtig sein weil er absichtlich wenig sagt. 

Zusätzlich werden Zögerungen gezählt. Keywords wie _hmm_, _uh_, _um_, _wait_ und _let me think_.

Der Maulwurf überlegt oft länger weil er seine Sabotage planen muss. Oder er zögert absichtlich um Zeit zu verschwenden. Diese Zögerungen sind daher ein wichtiges Signal. Zumindest für mein Verständnis.

Der endgültige Score für jeden Agent ist der höhere Wert aus Abweichungs-Score und Zögerungs-Verhältnis.

#### Information Quality Analysis

Die Qualität der Informationen die ein Agent liefert kann ein wichtiger Hinweis auf Sabotage sein. Vage Aussagen deuten oft auf absichtliche Verschleierung hin.

```python
def _analyze_information_quality(self, messages, agents):
    concrete_keywords = ["camera", "guard", "vault", "door", "code", "key"]
    vague_keywords = ["maybe", "probably", "might", "not sure", "i think"]

    agent_concrete = defaultdict(int)
    agent_vague = defaultdict(int)

    for msg in messages:
        text = msg["message"].lower()
        agent = msg["agent_name"]

        concrete_count = sum(1 for kw in concrete_keywords if kw in text)
        vague_count = sum(1 for kw in vague_keywords if kw in text)

        agent_concrete[agent] += concrete_count
        agent_vague[agent] += vague_count

    scores = {agent: 0.0 for agent in agents}
    for agent in agents:
        total = agent_concrete[agent] + agent_vague[agent]
        if total > 0:
            vagueness_ratio = agent_vague[agent] / total
            scores[agent] = vagueness_ratio

    return scores
```

Die konkreten Schlüsselwörter werden als Liste definiert. Begriffe wie _camera_, _guard_, _vault_, _door_, _code_ und _key_, die sehr spezifisch sind.

Die vagen Schlüsselwörter werden ebenfalls definiert. Begriffe wie _maybe_, _probably_, _might_, _not sure_ und _i think_, die unbestimmt sind.

Für jeden Agenten wird dann gezählt, wie oft er konkrete gegenüber vagen Schlüsselwörtern verwendet. Das gibt Aufschluss über die Qualität seiner Informationen. Oder seine Fähigkeiten 😅 

Der Maulwurf gibt oft absichtlich vage Informationen statt konkreter Details. Ein Satz wie _maybe the guards are in the break room_ ist viel unbestimmter als _Guards are at position X in sector 3_.

Der Score für jeden Agenten ist das Verhältnis der vagen Begriffe. Also die vagen Schlüsselwörter geteilt durch die Gesamtzahl der Schlüsselwörter.

### Schritt 2 Augmentation

Im zweiten Schritt werden die gefundenen Muster zu strukturiertem Context aufbereitet. Dieser gibt dem LLM konkrete Anhaltspunkte statt nur roher Daten.

#### Context Builder

Diese Methode strukturiert die Erkenntnisse aus Schritt 1 in ein klares Format das das LLM für seine Analyse nutzen kann.

```python
def _build_rag_context(self, messages, tool_usage, agents, rule_scores):
    """Build structured context from retrieved patterns."""
    context_parts = []

    # Top suspects from rule-based analysis
    sorted_suspects = sorted(
        rule_scores.items(),
        key=lambda x: x[1],
        reverse=True
    )[:3]

    context_parts.append("TOP SUSPECTS (Rule-based):")
    for agent, score in sorted_suspects:
        context_parts.append(f"  - {agent}: {score:.2%} suspicion")

    # Tool failures per agent
    tool_failures = defaultdict(int)
    for usage in tool_usage:
        agent = usage.get("agent")
        if not usage.get("success", True):
            tool_failures[agent] += 1

    if tool_failures:
        context_parts.append("\nTOOL FAILURES:")
        for agent, failures in tool_failures.items():
            context_parts.append(f"  - {agent}: {failures} tools failed")

    # Timing keywords per agent
    timing_mentions = defaultdict(int)
    timing_keywords = ["minute", "hour", "time", "wait", "delay"]

    for msg in messages:
        agent = msg.get("agent_name")
        text = msg.get("message", "").lower()
        if any(kw in text for kw in timing_keywords):
            timing_mentions[agent] += 1

    if timing_mentions:
        context_parts.append("\nTIMING-RELATED MENTIONS:")
        top_timing = sorted(
            timing_mentions.items(),
            key=lambda x: x[1],
            reverse=True
        )[:3]
        for agent, count in top_timing:
            context_parts.append(f"  - {agent}: {count} timing mentions")

    return "\n".join(context_parts)
```

Diese Methode erstellt einen strukturierten Kontext aus den zuvor ermittelten Mustern.

Die Hauptverdächtigen aus der regelbasierten Analyse werden extrahiert. Das sind die drei Agenten mit dem höchsten Verdachts-Score.

Fehlgeschlagene Tool-Aufrufe werden pro Agent gezählt. Dabei werden nur die Tools betrachtet, die tatsächlich fehlgeschlagen sind.

Erwähnungen von Zeitangaben werden ebenfalls gezählt. Agenten, die besonders oft über Timing sprechen, fallen damit auf.

Der resultierende Kontext gibt dem LLM konkrete Fakten zur Analyse. Statt nur die rohe Konversation zu bekommen, erhält es strukturierte Hinweise auf verdächtiges Verhalten.

### Schritt 3 Generation

Im dritten Schritt übernimmt das LLM die finale Analyse. Es bewertet die Konversation unter Berücksichtigung des strukturierten Kontexts aus den Schritten eins und zwei.

#### LLM-basierte Score-Berechnung

Diese Methode nutzt das LLM um die Agenten-Konversation im Kontext der regelbasierten Erkenntnisse zu analysieren.

```python
def _get_llm_scores(self, messages, tool_usage, agents, rule_scores):
    """LLM based analysis with Retrieved Context."""
    # Build augmented context
    context = self._build_rag_context(
        messages, tool_usage, agents, rule_scores
    )

    # Build conversation
    conversation_text = "\n".join([
        f"{msg['agent_name']}: {msg['message']}"
        for msg in messages[:50]
    ])

    # RAG Prompt
    prompt = f"""You are an expert detective analyzing a heist mission.

RETRIEVED SUSPICIOUS PATTERNS:
{context}

AGENT CONVERSATION:
{conversation_text}

TASK:
Analyze the conversation using the suspicious patterns above.
For each agent, estimate sabotage probability (0.0-1.0).

Consider:
- Vague or conflicting information
- Delays or confusion
- Suspicious tool failures
- Contradictions

Respond ONLY with JSON: {{"agent": score, ...}}
"""

    response = self.llm_client.chat.completions.create(
        model="local-model",
        messages=[
            {"role": "system", "content": "You are a detective. Respond only with valid JSON."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=500
    )

    # Parse and normalize LLM scores
    llm_output = response.choices[0].message.content.strip()
    llm_scores = json.loads(llm_output)

    return {
        agent: max(0.0, min(1.0, float(llm_scores.get(agent, 0.0))))
        for agent in agents
    }
```

Der angereicherte Kontext wird mit der zuvor beschriebenen Methode erstellt und enthält alle strukturierten Muster.

Die Konversation wird formatiert. Dabei werden nur die ersten 50 Nachrichten verwendet, um den Kontext nicht zu überladen.

Der Prompt wird konstruiert und ist entscheidend für die Qualität der LLM-Analyse. Das LLM bekommt nicht nur die rohe Konversation. Es erhält zusätzlich die strukturierten Verdachtsmomente aus der regelbasierten Analyse. Diese Anreicherung verhindert, dass das LLM halluziniert, und macht die Analyse deutlich fundierter.

Das LLM wird aufgefordert, als Experten-Detektiv zu agieren und die Konversation zu analysieren. Dabei soll es die verdächtigen Muster als Grundlage verwenden.

Die Antwort wird im JSON-Format erwartet. Das ermöglicht ein einfaches Parsen der Ergebnisse. Das Format ist ein Dictionary mit Agenten-Namen als Schlüssel und Scores als Werte zwischen 0.0 und 1.0.

Die Temperatur ist auf 0.3 gesetzt. Das macht die Antworten deterministischer und reproduzierbarer.

Die LLM-Scores werden geparst und auf den gültigen Bereich von 0.0 bis 1.0 normalisiert.

## Hybrid-Ansatz: Regeln und LLM

Ein rein regelbasierter Ansatz ist nicht flexibel genug und zu starr. Es kann zwar in vielen anderen Fällen helfen, aber eine subtile Sabotage beispielsweise, würde man damit nicht erkennen, weil man den Kontext nicht erkennt. Feste Schwellwerte funktionieren nicht für alle Situationen.

Auf der anderen Seite ist ein rein auf LLMs basierter Ansatz auch ungeeignet, weil LLMs bekanntlich zu Halluzinationen neigen. 

Die Kombination aus beidem macht den Unterschied. Regeln finden messbare Anomalien. Das LLM versteht Kontext und Nuancen. Zusammen sind die Scores robuster und man hat trotzdem volle Transparenz.

Die Gewichtung ist 60 Prozent Regeln und 40 Prozent LLM. Stabil trifft auf intelligent. Messbar trifft auf kontextbewusst. Hoffentlich ergibt das die beste Genauigkeit bei der Erkennung.

## Detection API

Die Detection-API bringt die KI-Analyse direkt ins Frontend. Wir bauen hier auch auf Code aus den vergangenen Tagen auf. 

```python
from day_22.sabotage_detector import SabotageDetector
from day_20.session_analytics import SessionAnalytics

app = FastAPI(title="Sabotage Detection API")
analytics = SessionAnalytics()
detector = SabotageDetector()

@app.post("/api/ai-detect/analyze")
async def analyze_session(request: DetectionRequest):
    # Get session data
    details = analytics.get_session_details(request.session_id)
    messages = details["messages"]
    tool_usage = details["tool_usage"]

    # Extract agents
    agents = list(set(
        msg["agent_name"]
        for msg in messages
        if msg.get("agent_name")
    ))

    # Run detection
    analysis = detector.get_detailed_analysis(
        session_id=request.session_id,
        messages=messages,
        tool_usage=tool_usage,
        agents=agents
    )

    return analysis
```

Der Endpoint holt zuerst die Daten aus der Analytics-Datenbank. Das sind die Nachrichten und die Tool-Nutzungsereignisse.

Die Agenten-Liste wird aus den Nachrichten extrahiert. Dabei werden nur die eindeutigen Agenten-Namen verwendet.

Der Detector wird dann aufgerufen und analysiert die komplette Session. Er führt dabei den gesamten Ablauf aus, von Retrieval über Augmentation bis zur Generation.

Die resultierende Analyse wird als JSON zurückgegeben.

## Response Format

Die API liefert eine detaillierte Analyse mit Scores und Breakdown für jeden Agenten.

```json
{
  "session_id": "game_001",
  "suggested_Maulwurf": "hacker",
  "confidence": 0.647,
  "suspicion_scores": {
    "planner": 0.231,
    "hacker": 0.647,
    "safecracker": 0.189,
    "getaway_driver": 0.274
  },
  "score_breakdown": {
    "hacker": {
      "tool_usage": 0.450,
      "timing": 0.850,
      "message_anomaly": 0.620,
      "information_quality": 0.670,
      "combined": 0.647
    }
  },
  "analysis_weights": {
    "tool_usage_anomaly": 0.25,
    "timing_inconsistency": 0.30,
    "message_anomaly": 0.20,
    "information_quality": 0.25
  }
}
```

Die Zahlen in diesem Beispiel sind natürlich nur zur Veranschaulichung erfunden. In diesem Beispiel hat der Hacker den höchsten Verdachtswert mit 0.647 und wird daher als Maulwurf vorgeschlagen.

Die Aufschlüsselung zeigt, dass die Timing-Analyse mit 0.850 das stärkste Signal war. Der Hacker hat sehr viel über Timing gesprochen und sich oft widersprochen.

Die anderen Kategorien zeigen ebenfalls verdächtige Werte. Die Tool-Nutzung liegt bei 0.450, Nachrichten-Anomalien bei 0.620 und Informationsqualität bei 0.670.

Der kombinierte Wert von 0.647 ist die gewichtete Kombination aller dieser Signale nach den definierten Gewichtungen.

## Integration ins Maulwurf-Spiel

Das Detection System kann direkt ins Maulwurf-Spiel integriert werden.
Der Java Teil ist wieder 100% vibecoded. 

```javascript
// After heist ends
const detection_result = await fetch('/api/ai-detect/suggest', {
    method: 'POST',
    body: JSON.stringify({ session_id: currentSession })
})

const data = await detection_result.json()

console.log(`AI suggests: ${data.suggested_Maulwurf}`)
console.log(`Confidence: ${data.confidence * 100}%`)

// Show to user as hint
if (data.confidence > 0.6) {
    showHint(
        `The AI is ${Math.round(data.confidence*100)}% confident ` +
        `that ${data.suggested_Maulwurf} is the Maulwurf`
    )
}
```

Nach Ende des Überfalls wird die Detection-API aufgerufen und liefert einen Vorschlag.

Der KI-Vorschlag wird dem User als Hinweis angezeigt. Allerdings nur wenn die Sicherheit über 60 Prozent liegt.

Der User kann diesen KI-Vorschlag dann nutzen oder ihn ignorieren und trotzdem selbst raten.

## Messung der Treffergenauigkeit

Um zu messen ob das System tatsächlich besser ist als Zufall gibt es einen einfachen Test.

```python
correct_detections = 0
total_games = 0

for game in completed_games:
    detection = detector.suggest_Maulwurf(game.suspicion_scores)
    if detection[0] == game.actual_Maulwurf:
        correct_detections += 1
    total_games += 1

accuracy = correct_detections / total_games
random_baseline = 1 / len(agents)  # 0.25 bei 4 agents

print(f"Detection Accuracy: {accuracy*100:.1f}%")
print(f"Random Baseline: {random_baseline*100:.1f}%")
print(f"Better than random: {accuracy > random_baseline}")
```

Für jedes abgeschlossene Spiel wird der KI-Vorschlag mit dem tatsächlichen Maulwurf verglichen. Die Anzahl der korrekten Detections wird gezählt und durch die Gesamtzahl geteilt. Die Random Baseline ist 1 geteilt durch die Anzahl der Agents, oder anders die Wahrscheinlichkeit, richtig zu liegen, wenn man rät. Bei vier Agents sind das 25 Prozent.
Das Ziel ist mit unserer automatisierten Detektion eine Genauigkeit von mindestens 35 bis 40 Prozent bei 4 Agents zu erreichen. Damit wäre das System besser als zufälliges Raten.

Sprechen wir nun darüber, wie man das alles anwendet.

## Verwendung

Der Detection-Server wird mit einem einfachen Befehl gestartet.

```bash
./day_22/start_detection_dashboard.sh
```

Der Server läuft dann auf Port 8008 und ersetzt das alte Tag 20 Dashboard.

Das Dashboard kann im Browser geöffnet werden.

```
http://localhost:8008
```

Im Dashboard gibt es einen "Quick Start Heist" Button. Ein Klick darauf lädt automatisch alle verfügbaren Agents aus der Config und startet eine neue Session. Einer der Agents wird dabei zufällig zum Maulwurf. Die Agents laufen dann im Hintergrund und ihre Nachrichten werden live ins Dashboard gestreamt.

Die Standard-Config enthält 6 Agents: planner, hacker, safecracker, intel, driver und lookout. Neue Agents können einfach zur `day_20/agents_config.yaml` hinzugefügt werden. Der Quick-Start Button erkennt sie dann automatisch.

Das Dashboard bietet ein gewisse Kontrolle über das laufende Spiel. Mit Pause kann das Spiel angehalten werden. Resume setzt es fort. Stop beendet das Spiel komplett. Die Agents reagieren sofort auf diese Befehle. Also fast sofort. Der aktuelle LLM Call muss erst noch ausgeführt werden.

Das Dashboard zeigt in Echtzeit die Agent-Aktivität und die Tool-Usage an. Nach ein paar Turns kann die KI-Analyse gestartet werden.

Neben der KI-Analyse gibt es auch die manuelle Detection. Alle 6 Agents werden als anklickbare Badges angezeigt. Ein Klick markiert den Agent als Verdächtigen. Der Reveal-Button zeigt dann den tatsächlichen Maulwurf inklusive seiner Sabotage-Strategie.

![alt text](<Bildschirmfoto 2025-12-24 um 15.10.09.png>)

Alternativ kann eine Session auch über die API analysiert werden.

```bash
curl -X POST http://localhost:8008/api/ai-detect/analyze \
  -H "Content-Type: application/json" \
  -d '{"session_id": "game_001"}'
```

Dieser Call gibt die vollständige Analyse mit allen Verdachtswerten und der Aufschlüsselung zurück.

Für einen schnellen Vorschlag gibt es einen eigenen Endpoint.

```bash
curl -X POST http://localhost:8008/api/ai-detect/suggest \
  -H "Content-Type: application/json" \
  -d '{"session_id": "game_001"}'
```

Dieser Call gibt nur den Vorschlag und die Sicherheit zurück und ist damit schneller.

## Zusammenfassung

Tag 22 macht das System intelligent. Oder zumindest intelligenter 😅

Statt blind zu raten, bekommen User jetzt fundierte AI-Analysen. Die Detection Pipeline funktioniert in drei Schritten, die zusammen einen RAG-Ansatz bilden.

* Der **Retrieval**-Teil analysiert mit regelbasierten Patterns vier Kategorien: Tool Usage, Timing, Messages und Information Quality. Diese Analysen sind messbar und reproduzierbar. Sie liefern einen strukturierten Context statt nur eines Bauchgefühls. Gewichtung: 60 Prozent.
* Der **Augmentation**-Teil bereitet den Context für das LLM auf. Die Top-Verdächtigen werden extrahiert, Tool-Failures zusammengefasst, Timing-Mentions gezählt. Das LLM bekommt faktenbasierte Hinweise statt nur rohe Daten. Das verhindert Halluzinationen.
* Der **Generation**-Teil nutzt das LLM um die Conversation zu analysieren. Es versteht Kontext und Nuancen. Es erkennt subtile Sabotage-Patterns die Regeln verpassen würden. Der Output ist strukturiertes JSON mit Scores. Gewichtung: 40 Prozent.

Die Kombination macht den Unterschied. Regeln sind messbar aber starr. LLMs sind flexibel aber halluzinieren. Zusammen ergeben 60 Prozent Regeln plus 40 Prozent LLM robuste Detection. Hoffentlich. Ich habe es nun ein paar Mal probiert und es sieht gut aus 😉

Die Accuracy ist deutlich besser als Zufall. Bei 4 Agents liegt die Baseline bei 25 Prozent. Das System erreicht typischerweise 40 bis 60 Prozent. Nicht perfekt, aber besser als raten.

Die Detection API macht es einfach. Session-Daten werden geholt, Retrieval wird durchgeführt, das LLM analysiert und Scores werden kombiniert. Fertig.

Mit Tag 22 haben wir einen echten AI-Detective. Er kombiniert regelbasierte Fakten mit LLM-Intelligence. Und er schlägt Zufall.
Und morgen geht es dann wieder Docker 😄