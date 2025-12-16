# Tag 15: Dynamic Agent System - Configuration statt Hardcoding

> **Quick Start**
> ```bash
> # 1. Services starten (OAuth + 3 Tools)
> ./day_15/start_services.sh
>
> # 2. LM Studio mit Gemma starten (Port 1234)
> # Manuell in LM Studio GUI
>
> # 3. Agent System ausführen
> python day_15/dynamic_agent_system.py
>
> # 4. Services stoppen
> ./day_15/stop_services.sh
> ```
> **Wichtig:** Tag 15 benötigt **5 laufende Services** gleichzeitig (OAuth, Calculator, File Reader, Database, LLM)

An Tag 15 wird es Zeit, unser Multi-Agent System erwachsen werden zu lassen. Bisher haben wir vier Agents hart im Code definiert. Planner, Hacker, Safecracker und Mole, alle fest verdrahtet mit ihren jeweiligen Rollen, Tools und Permissions. Das funktioniert, keine Frage. Aber es lässt sich schlecht skalieren, ist nicht flexibel und es macht A/B Testing nicht unbedingt einfacher.

Stell dir vor, du willst einen fünften Agenten hinzufügen. Oder die System Prompts verschiedener Agenten testen. Oder verschiedene Tool-Kombinationen ausprobieren. Mit hardcoded Agents bedeutet das jedes Mal Code-Änderungen, neue Commits, Deployments. Das ist nervig und fehleranfällig.

Noch schlimmer wird es, wenn wir verschiedene Team-Konstellationen testen wollen. Vier Agenten funktionieren gut, aber was ist mit drei? Oder sechs? Welcher Agent sollte Saboteur sein? Der Maulwurf ist offensichtlich, aber was wenn der Hacker sabotiert? Jede Variation braucht wieder Code-Änderungen.

Und dann kommt noch das OAuth-Problem dazu. Jeder Agent braucht seine Permissions, seine Scopes, seine Tools. Willst du die Tool-Verteilung ändern, musst du tief in den Code eingreifen. Das ist nicht mehr agile Entwicklung, das ist Wasserfall.

Die gute Nachricht... Es gibt eine Lösung 😀 **Configuration over Code**. Agents sollten aus einer Konfigurationsdatei geladen werden, nicht im Code definiert. Änderungen am Team sollten eine YAML-Datei editieren erfordern, keinen Code-Commit. Und genau das bauen wir heute.

## Die Idee: Agents as Configuration

Das Konzept ist simpel, bringt aber viele Vorteile. Statt Agents im Code zu definieren, schreiben wir eine YAML-Datei mit allen Agent-Definitionen. Jeder Agent bekommt seine eigene Konfiguration. Zum Beispiel werden Planner und Hacker zu:

```yaml
agents:
  - name: "planner"
    role: "Strategic Heist Planner"
    tools: []
    oauth_scopes: []
    system_prompt: "You are a strategic heist planner..."
    is_saboteur: false

  - name: "hacker"
    role: "Technical Security Expert"
    tools: ["file_reader:use"]
    oauth_scopes: ["simulation:read", "file_reader:use"]
    system_prompt: "You are a technical security expert..."
    is_saboteur: false
```

Das System liest diese Config beim Start und erstellt automatisch alle Agents mit ihren jeweiligen Eigenschaften. Und wenn man einen neuen oder weiteren Agentn möchte, fügt man einfach einen neuen Eintrag hinzu. Und falls man die Tool-Permissions ändern will, ja dann ändert man einfach den entsprechenden Eintrag `tools`. Das gleiche gilt für unterschiedliche System-Prompts usw. usw. 

Das bringt ein paar Vorteile:
* **Flexibilität**: Wir können beliebig viele Agents hinzufügen oder entfernen, ohne Code zu ändern. 
* **A/B Testing**: Verschiedene Config-Dateien für verschiedene Experimente. Wir können z.B. neue Agenten oder Prompts testen, ohne in den Code eingegriffen zu haben.
* **Version Control**: Alle Agent-Änderungen sind in Git nachverfolgbar durch Config-Diffs. Das wäre sie zugegebenermaßen auch, wenn ich sie im Code ändere, aber übersichtlicher wird es dadurch nicht.
* **Environment Separation**: Wir können dynamisch zwischen Entwiklungs-Config mit drei Agents und einer "Produktions"-Config mit dem vollen Team wechseln.

Letztlich ist das der Unterschied zwischen einem einfachen, starren Prototypen und einer flexiblen Palltform.

## Implementation

Die Umsetzung besteht aus mehreren Schichten. Zuerst brauchen wir einen **ConfigLoader**, der YAML parst und in saubere Python-Objekte umwandelt. Dann einen **DynamicAgent**, der komplett aus der Config erstellt wird. Und schließlich ein **DynamicAgentSystem**, das alles orchestriert.

Fangen wir mit den Datenstrukturen an. Wir nutzen Python's `dataclasses` für saubere, typsichere Konfiguration. `Dataclasses` ermöglichen eine klare Trennung von Daten und Logik, was die Dynamik der Agent-Erstellung aus YAML-Konfigurationen erleichtert. Es gibt sogar automatisch erzeugte Methoden wie `init`, `repr`und `eq` und andere Standardmethoden. Diese Methoden muss ich nun nicht mehr fehlerfrei selber implementieren 😄


```python
@dataclass
class AgentConfig:
    name: str
    role: str
    tools: List[str]
    oauth_scopes: List[str]
    system_prompt: str
    is_saboteur: bool

@dataclass
class SystemConfig:
    agents: List[AgentConfig]
    oauth_service: Dict[str, Any]
    tool_services: Dict[str, Dict[str, Any]]
    llm: Dict[str, Any]
    memory_service: Dict[str, Any]
    session: Dict[str, Any]
```

Der `ConfigLoader` liest das YAML-File und erstellt diese Strukturen.

```python
class ConfigLoader:
    @staticmethod
    def load_config(config_path: str) -> SystemConfig:
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)

        agents = []
        for agent_data in config_data['agents']:
            agent = AgentConfig(
                name=agent_data['name'],
                role=agent_data['role'],
                tools=agent_data.get('tools', []),
                oauth_scopes=agent_data.get('oauth_scopes', []),
                system_prompt=agent_data['system_prompt'],
                is_saboteur=agent_data.get('is_saboteur', False)
            )
            agents.append(agent)

        return SystemConfig(
            agents=agents,
            oauth_service=config_data['oauth_service'],
            tool_services=config_data['tool_services'],
            llm=config_data['llm'],
            memory_service=config_data['memory_service'],
            session=config_data['session']
        )
```

Das sieht aufwendiger als es eigentlich ist und ist nur Biolerplate-Code. Einer der ganz großen Vorteile: Wir validieren die Config schon beim Laden. Fehlerhafte YAML-Dateien werden sofort erkannt, nicht erst zur Laufzeit wenn ein Agent das erste Mal antworten soll.

## Dynamic Agents

Der interessante Teil kommt bei der Agent-Erstellung. Ein `DynamicAgent` wird komplett aus seiner `AgentConfig` gebaut. Und hier kommt dann eine selbst programmierte Klasse zum Einsatz.

```python
class DynamicAgent:
    def __init__(
        self,
        config: AgentConfig,
        llm_client: OpenAI,
        oauth_client: OAuthClient,
        tool_client: ToolClient
    ):
        self.config = config
        self.llm_client = llm_client
        self.oauth_client = oauth_client
        self.tool_client = tool_client
        self.conversation_history: List[Dict[str, str]] = []
        self.oauth_token: Optional[str] = None

        # Get OAuth token if scopes are configured
        if self.config.oauth_scopes:
            self.oauth_token = self.oauth_client.get_token(
                self.config.name,
                self.config.oauth_scopes
            )
```

Der Agent bekommt seine Config ergänzt um drei Clients: LLM, OAuth und Tools. Wenn die Config OAuth Scopes definiert, holt sich der Agent automatisch ein Token. Kein manuelles Auth-Management mehr, alles passiert transparent basierend auf der Konfiguration.

Die `respond()` Methode ist Teil der `DynamicAgent`-Klasse und nutzt die Config für System Prompts und Tool-Information:

```python
def respond(self, context: List[Dict[str, str]]) -> str:
    messages = [{"role": "system", "content": self.config.system_prompt}]

    for msg in context:
        messages.append({
            "role": "user",
            "content": f"[{msg['agent']}]: {msg['message']}"
        })

    if self.config.tools:
        tool_info = f"\n\nAvailable tools: {', '.join(self.config.tools)}"
        messages.append({"role": "system", "content": tool_info})

    response = self.llm_client.chat.completions.create(
        model="google/gemma-3n-e4b",
        messages=messages,
        temperature=0.7,
        max_tokens=500
    )

    return response.choices[0].message.content
```

Der Agent ist dumm im besten Sinne. Er weiß nichts über seine Rolle, seine Tools oder seine Permissions. Er liest alles aus der Config. Das macht ihn extrem flexibel, weil dieselbe Agenten-Klasse jeden beliebigen Agenten repräsentieren kann.

Falls du über die `messages`-Liste gestolpert bist, nachdem wir ja bereits einen gemeinsamen Nachrichten-Speicher implementiert hatten... Die `messages`-Liste ist nur eine temporäre Formatierung für den LLM-API-Call, keine persistente Speicherung. Der Agent selbst hat keine eigene Conversation History – die zentrale History liegt im `DynamicAgentSystem` mit Information Compression (letzte 5 Nachrichten).

## System Orchestration

Das `DynamicAgentSystem` bringt schließlich alles zusammen. Es lädt die Config, initialisiert die Clients und erstellt alle Agents:

```python
class DynamicAgentSystem:
    def __init__(self, config_path: str):
        self.config = ConfigLoader.load_config(config_path)

        # Initialize LLM client
        self.llm_client = OpenAI(
            base_url=self.config.llm['base_url'],
            api_key=self.config.llm['api_key']
        )

        # Initialize OAuth and Tool clients
        self.oauth_client = OAuthClient(self.config.oauth_service)
        self.tool_client = ToolClient(self.config.tool_services)

        # Create agents dynamically
        self.agents: Dict[str, DynamicAgent] = {}
        for agent_config in self.config.agents:
            agent = DynamicAgent(
                agent_config,
                self.llm_client,
                self.oauth_client,
                self.tool_client
            )
            self.agents[agent_config.name] = agent

        self.conversation_history: List[Dict[str, str]] = []
```

Die Conversation Logic bleibt identisch zu vorher. Agents antworten nacheinander, die Messages werden geloggt, die History wird gespeichert. Der einzige Unterschied: Die Agents kommen jetzt aus der Config statt hart gecodet zu sein.

```python
def run_conversation(self, num_turns: int = None):
    if num_turns is None:
        num_turns = self.config.session['max_turns']

    turn_order = self.config.session['turn_order']

    for turn in range(num_turns):
        for agent_name in turn_order:
            agent = self.agents[agent_name]
            context = self.conversation_history[-5:]
            response = agent.respond(context)

            message = {
                "turn": turn + 1,
                "agent": agent_name,
                "role": agent.config.role,
                "message": response
            }
            self.conversation_history.append(message)
```

## Was macht es so vorteilhaft?

Einer der wahren Vorteile liegt in den Möglichkeiten, die sich durch die Configuration eröffnen. Hier sind konkrete Szenarien, die jetzt trivial werden.

### Scenario 1: A/B Testing von System Prompts

Wenn du zum Beispiel herausfinden willst, zu welchem Ergebnisse unterschiedlich konfigurierte Agenten führen, kannst du einfach zwei Konfig-Dateien anlegen:

```yaml
# config_aggressive.yaml
- name: "planner"
  system_prompt: "Be aggressive and take calculated risks..."

# config_conservative.yaml
- name: "planner"
  system_prompt: "Be extremely cautious and risk-averse..."
```

Dann einfach beide durchlaufen lassen und die Ergebnisse vergleichen. Kein Code-Change, nur ein Config-Switch.

### Scenario 2: Tool Permission Experiments

Was passiert, wenn der Hacker alle Tools hat versus spezialisierte Rollen?

```yaml
# config_hacker_all_tools.yaml
- name: "hacker"
  tools: ["file_reader:use", "calculator:use", "database_query:use"]

# config_specialized.yaml
- name: "hacker"
  tools: ["file_reader:use"]
- name: "safecracker"
  tools: ["calculator:use"]
```

Führt eine zentrale Tool-Konzentration zu besseren Plänen oder zu schlechterer Koordination? Und wieder: Einfach durchlaufen lassen und testen.

### Scenario 3: Variable Team Sizes

Mein Lieblinsbeispiel. Du möchtest zum Team noch weitere Agenten hinzufügen? Du kannst einfach weitere in der Config definieren, ohne im eigentlichen Code etwas verändern zu müssen.

```yaml
# minimal_team.yaml - Nur Planner + Hacker
agents:
  - name: "planner"
    # ...
  - name: "hacker"
    # ...

# full_team.yaml - Alle vier Agents
agents:
  - name: "planner"
  - name: "hacker"
  - name: "safecracker"
  - name: "mole"
```

### Scenario 4: Saboteur Variations

Oder konkrekt auf unser Beispiel bezogen: Welcher Agent als Saboteur macht den Überfall am wahrscheinlichsten kaputt?

```yaml
# mole_saboteur.yaml
- name: "mole"
  is_saboteur: true

# hacker_saboteur.yaml
- name: "hacker"
  is_saboteur: true
```

Ist der offensichtliche Insider (Mole) leichter zu erkennen als ein technischer Experte (Hacker)?

All diese Experimente sind jetzt Config-Änderungen, keine Code-Änderungen. Das birgt viel weniger Arbeit und ist auch deutlich weniger fehleranfüllig.

## Vorteile im professionellen Umfeld: Environment Separation

In professionellen Setups braucht man verschiedene Configs für verschiedene Environments. Das geht jetzt elegant:

```bash
agents_config_dev.yaml      # Kleines Team, schnelle Iteration
agents_config_staging.yaml  # Vollständiges Team, Pre-Prod Tests
agents_config_prod.yaml     # Production Setup mit allen Features
```

Und das Deployment wird zu:

```python
# Development
system = DynamicAgentSystem("agents_config_dev.yaml")

# Production
system = DynamicAgentSystem("agents_config_prod.yaml")
```

Es din keine Code-Branches mehr für verschiedene Environments nötig. Eine Codebase mit verschiedenen Configs. Und alle Config-Änderungen sind in Git nachverfolgbar:

```bash
$ git diff agents_config.yaml
- system_prompt: "Be aggressive and take risks..."
+ system_prompt: "Be cautious and thorough..."
```

Du siehst sofort, was sich geändert hat. Code Reviews werden einfacher, weil Agent-Änderungen von Logik-Änderungen getrennt sind.

## Integration

Das Dynamic Agent System ist kein isoliertes Feature. In den vergangenen Tagen haben wir schon einige Features implementiert. Leicht abgewandelt, findet sich nun vieles wieder:

**Tag 8-9 (OAuth):** Die Scopes kommen jetzt aus der Config. Jeder Agent bekommt automatisch sein Token basierend auf `oauth_scopes`.

**Tag 13 (Agent Tools):** Die Tools werden aus der `tools`-Liste geladen. Kein manuelles Tool-Assignment mehr.

**Tag 14 (OAuth Tools):** Die Tool Permissions werden durch `oauth_scopes` erzwungen. Sicherheit schon in der Config.

**Tag 12 (Memory Service):** Die Memory Service URL kommt aus der `memory_service`-Config. Verschiedene Environments können verschiedene Services nutzen.

Das ist nun der Punkt wo einzelne Features zu einem kohärenten System werden. Nicht durch mehr Code, sondern durch bessere Architektur.

## Service-Architektur

Ein wichtiger Unterschied zu den letzten Tagen ist die Tatsache, dass das Dynamic Agent System mehrere gleichzeitig laufende Services benötigt. Zuvor hatten wir meist einzelne Services, jetzt handelt es sich bereits um eine Microservice-Architektur.

```
Dynamic Agent System
├── OAuth Service (8001)    → Token-Verwaltung für alle Agents
├── Calculator (8002)       → Tool für Safecracker
├── File Reader (8003)      → Tool für Hacker
├── Database Query (8004)   → Tool für Mole
└── LLM Studio (1234)       → Gemma Model
```

Durch die Aufteilung hat jeder Sercive eine klare Verantwortung (**Separation of Concerns**). Sie können beliebig und unabhängig voneinander skaliert werden. Jeder Service kann einzeln aktualisiert werden und Probleme können isoliert auf einzelne Services betrachtet werden.

Und weil es nun ein paar Schritte zum Starten aller benötigten Services sind, habe ich auch ein Skript, welches das automatisiert übernimmt.

## Helfer-Skripte

Um das Starten und Stoppen zu vereinfachen, gibt es jetzt Helfer-Skripte:

```bash
# Alle Services starten
./day_15/start_services.sh

# Agent System ausführen
python day_15/dynamic_agent_system.py

# Alle Services stoppen
./day_15/stop_services.sh
```

Das `start_services.sh` Skript räumt zunächst alte Prozesse auf den Ports auf. Dann startet es im Hintergrund die vier Services, zeigt PIDs und Status und leitet Logs in den Ordner `/tmp`um.

Das `stop_services.sh` Skript findet alle Prozesse auf den Ports 8001-8004 und beendet sie mit `kill -9`.

Im Gegensatz zu früheren Tagen, wo wir nur einen Service-Prozess starten mussten, brauchen wir jetzt **mindestens 5 laufende Prozesse** gleichzeitig (OAuth, die drei Tools und LLM Studio). Das ist realistischer für professionelle Umgebungen, aber auch komplexer zu managen.

Die Service-URLs und Ports sind alle in der `agents_config.yaml` definiert:

```yaml
oauth_service:
  base_url: "http://localhost:8001"

tool_services:
  calculator:
    host: "localhost"
    port: 8002
    endpoint: "/tools/calculator"
  # ... weitere Tools
```

Verschiedene Environments (Dev/Staging/Prod) können unterschiedliche Service-URLs nutzen, ohne Code-Änderungen.

## Ausblick

Das Dynamic Agent System ist das Fundament für die nächsten Tage. Morgen kommt **Service Integration** dran, wo wir alle Services (OAuth, Tools, Memory, SQLite) zusammenführen. Dann wird die Config noch wichtiger, weil wir Service-URLs, Credentials und Connection-Settings zentral verwalten.

Danach kommt **Session Management** mit session-übergreifender State-Verwaltung. Die Session-Config in unserem YAML wird dann zum zentralen Steuerungsinstrument.

Und am Ende haben wir ein System, wo man durch reine Config-Änderungen komplexe Multi-Agent Szenarien orchestrieren kann. Ohne Code-Änderungen, ohne Deployments, ohne Risiko.

## Zusammenfassung

Heute haben wir unser Multi-Agent System von hardcoded zu configuration-driven umgestellt. Das klingt nach einem kleinen Schritt, ist aber fundamental.

**Was haben wir gewonnen?**
- Beliebig viele Agents ohne Code-Änderung
- A/B Testing durch Config-Switching
- Environment Separation (Dev/Staging/Prod)
- Git-basiertes Change Tracking
- Von 4 zu N Agents ohne Refactoring

**Was kostet es?**
- Etwas mehr Boilerplate beim Setup
- YAML-Syntax statt Python (aber das ist ein Feature)
- Ein paar zusätzliche Abstraktions-Layer
- **Mehrere Services gleichzeitig**: Statt einem Service-Prozess brauchen wir jetzt 5 (OAuth, drei Tools und LLM)
- Service-Management: Starten, Stoppen, Monitoring von mehreren Prozessen

Das Kosten-Nutzen-Verhältnis ist trotzdem eindeutig. Die Flexibilität und die realistische Microservice-Architektur sind die zusätzliche Komplexität wert. Die Helfer-Skripte (`start_services.sh`, `stop_services.sh`) machen das Management handhabbar.

**Die wichtigste Erkenntnis:** Ein gutes Config-System macht aus einem starren Prototyp eine flexible Plattform. Nicht durch mehr Features, sondern durch bessere Architektur.

Morgen bauen wir darauf auf und integrieren alle Services. Aber das Fundament steht jetzt.

## Verwendung

1. `./start_services.sh` - Startet OAuth + 3 Tool Services
2. LM Studio manuell starten (Port 1234)
3. `python dynamic_agent_system.py` - Führt Agent Conversation aus
4. `./stop_services.sh` - Stoppt alle Services

**Service Logs:** `/tmp/*_service.log`
