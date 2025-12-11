Day ten. Still some missing. Information Curation.

Heute geht es darum, wie der Hacker-Agent exklusive Bankdaten holt und diese mit dem Team teilt, aber eben nicht einfach alles, sondern gezielt und kuratiert. Wie kann er Informationen weitergeben, ohne alle Details zu „dumpen“? Hier kommt Information Curation ins Spiel.
Die anderen Agenten müssen ihm vertrauen, weil sie selbst keinen Zugriff auf die Bankdaten haben. Das erzeugt später eine spannende Informationsasymmetrie und Teamdynamik.

Einiges kommt uns schon bekannt vor. Deswegen verweise ich wieder auf mein Repository.

Wir definieren z.B. Service URLs und Credentials:
```python
# Service URLs
OAUTH_SERVICE = "http://localhost:8001"
SIMULATION_SERVICE = "http://localhost:8003"

# Hacker's OAuth Credentials
HACKER_CLIENT_ID = "hacker-client"
HACKER_SECRET = "hacker-secret-123"
```


Das bedeutet, du musst die beiden Services von Tag acht (OAuth Service) und Tag neun (Simulation Service) starten.


Den Teil mit dem lokalen LLM und dem Token holen überspringe ich hier. Viel spannender ist das Kuratieren der Informationen: Nachdem wir die Bankdaten erhalten haben, bereiten wir sie für das LLM auf, z.B. als Prompt mit Variablen wie Floors, Vault Rating etc. Wir geben eine maximale Wortzahl vor und könnten an dieser Stelle auch gezielt Informationen weglassen, verändern oder hervorheben. So entsteht ein kuratierter Informations-String, den wir samt Persona an das LLM übergeben und als Antwort eine kompakte Analyse in natürlicher Sprache bekommen.

Warum ist das wichtig? In echten Teams (und KI-Projekten) ist es oft entscheidend, Informationen nicht einfach ungefiltert weiterzugeben, sondern sie gezielt zu verdichten, zu bewerten und für die Zielgruppe aufzubereiten. Das schafft Vertrauen, verhindert Informationsüberflutung und fördert Zusammenarbeit.


```python
    def analyze_and_share(self) -> str:
        if not self.bank_data:
            return "No data available to analyze."

        print("\n🤖 Step 3: Analyzing Data with LLM...")

        data_summary = f"""
You have exclusive access to bank security data:
- Bank: {self.bank_data['data']['name']}
- Floors: {self.bank_data['data']['floors']}
- Vault Rating: {self.bank_data['data']['vault_rating']}
- Security Systems: {', '.join(self.bank_data['data']['security_systems'])}
- Guards: {self.bank_data['data']['guard_count']}

Provide a brief security analysis. What are the main challenges?
Keep it under 75 words.
"""

        response = client.chat.completions.create(
            model="google/gemma-3n-e4b",
            messages=[
                {"role": "system", "content": "You are a security expert. Be concise."},
                {"role": "user", "content": data_summary}
            ],
            max_tokens=100
        )

        analysis = response.choices[0].message.content
        print("   ✅ Analysis complete!")
        return analysis
```

Der Output, den der Hacker ursprünglich erhalten hat, sieht so aus:
```bash
📂 Retrieved Bank Data:
{'data': {'name': 'First National Bank', 'address': '123 Main Street', 'floors': 3, 'vault_rating': 'TL-30', 'security_systems': ['CCTV', 'Motion Sensors', 'Alarm'], 'guard_count': 4}, 'access_granted_to': 'hacker-client', 'scope': 'simulation:read'}
```

Nach dem Kuratieren der Informationen bekommen wir eine in natürlicher Sprache lesbare, kompakte Response:
```bash
📊 Security Analysis:
------------------------------------------------------------
## First National Bank Security Analysis:

**Strengths:** Robust physical security with TL-30 vault, layered defenses (CCTV, motion, alarms), and dedicated guards.

**Challenges:**  Limited information on guard training/response protocols & system redundancy. Potential vulnerabilities exist in human element (guard reliability) and reliance on standard systems.  Insider threat assessment is missing. Further risk assessment needed for comprehensive security posture.
```


Und das ist im Grunde auch schon alles zum heutigen Türchen.


## Zusammenfassung

Was bleibt heute hängen? Der Hacker kommt an die Bankdaten, aber er entscheidet, was das Team wirklich erfährt. Nicht alles wird einfach rausgehauen, sondern gezielt kuratiert, verdichtet und aufbereitet. Die anderen müssen ihm vertrauen, und das macht die Dynamik spannend (zumindest dann später im fertigen Projekt ;)): Wer teilt was, wie viel, und wie ehrlich? Information Curation ist nicht nur ein Buzzword, sondern der Schlüssel für gute Zusammenarbeit, egal ob im KI-Projekt oder echten Team. Weniger ist manchmal eben doch mehr...