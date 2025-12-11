
An Tag elf kommt etwas zum tragen, was vor allem auch bei lokal gehosteten LLMs wichtig werden dürfte. Wie bekomme ich meine gesamte Konversation in das Kontextfenster? Das mag in unserem aktuellen Projekt noch kein großes Problem sein, aber im professionellen Umfeld wächst der Kontext rasant an und man muss ihn auf irgendeine Art und Weise sinnvoll und verlässlich komprimieren. Das ist eine Disziplin, wie für LLMs gemacht ;)

Kurz ausgeholt: Unsere Hardware und auch die verwendeten Modell erlauben nur eine gewisse Größe Kontext, angegeben in Token. Nachdem das Modell häufig schon einen beträchtlichen Teil Speicher der GPU (oder unified RAM bei Apple Silicon) in Anspruch nimmt, können wir maximal so viele Token übergeben, wie noch in den Speicher passen. Oder so viele, wie das LLM erlaubt, denn die haben auch Limits, was die Anzahl der zu verarbeitenden Token angeht.

Ziel heute ist demnach, die Anzahl der Token zu reduzieren. Man könnte einfach alte Nachrichten wegwerfen (Token-Windowing) oder mit einem Sliding Window (Behalten der letzten X Nachrichten) arbeiten. Beide Varianten sorgen aber dafür, dass Daten verloren gehen. Deswegen versuchen wir es hierarchisch: Die alten Nachrichten werden zusammengefasst, die neuen bleiben vollständig. 

Kommen wir zur Implementierung!
Ich habe zwei Konversationen erzeugen lassen. Das was die Agenten besprechen habe ich nicht selber formuliert, sondern ein LLM texten lassen. Eine kurze Konversation, für die wir den Inhalt auch nachvollziehen können und eine längere, bei der es am Ende nur um Statistiken geht. Die kürzere Konversation besteht aus zehn Sätzen, die in einem Dict abgelegt sind:

```python
LONG_CONVERSATION = [
    {"turn_id": 1, "agent": "planner", "message": "We should target First National Bank. It has lower security than expected."},
    {"turn_id": 2, "agent": "hacker", "message": "I've analyzed their systems. They use an outdated alarm system from 2015."},
    {"turn_id": 3, "agent": "safecracker", "message": "The vault is a TL-30 model. I need 45 minutes minimum to crack it."},
    {"turn_id": 4, "agent": "mole", "message": "Actually, I think we need more time. Maybe 90 minutes to be safe?"},  # Sabotage!
    {"turn_id": 5, "agent": "planner", "message": "90 minutes is too long. Let's stick with 60 minutes as buffer."},
    {"turn_id": 6, "agent": "hacker", "message": "I can loop the security cameras for exactly 15 minutes before they notice."},
    {"turn_id": 7, "agent": "safecracker", "message": "That's cutting it close. I need backup tools in case the drill jams."},
    {"turn_id": 8, "agent": "mole", "message": "I can get you a keycard for the staff entrance. Less suspicious than breaking in."},
    {"turn_id": 9, "agent": "planner", "message": "Good. We go in at 2 AM when the night shift is smallest."},
    {"turn_id": 10, "agent": "hacker", "message": "I'll monitor police frequencies. If they get a call, we abort immediately."},
]
````

Die längere Konversation mit 100 Sätzen kannst du dir gerne auch antun, ich lasse es 😉 Du findest die Konversation im Repo.

Es folgen nun zwei Funktionen. Zunächst jene zum komprimieren der Daten.

```python
def compress_memory(turns: list, max_summary_tokens: int = 200) -> str:

    conversation_text = "\n".join([
        f"Turn {t['turn_id']} ({t['agent']}): {t['message']}"
        for t in turns
    ])

    prompt = f"""Summarize this heist planning conversation in max {max_summary_tokens} tokens.

Focus on:
- Key decisions made
- Important facts discovered
- Conflicts or disagreements
- Timeline agreed upon

Conversation:
{conversation_text}

Summary:"""

    response = client.chat.completions.create(
        model="google/gemma-3n-e4b",
        messages=[
            {"role": "system", "content": "You are a concise summarizer. Extract only essential information."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=max_summary_tokens
    )

    return response.choices[0].message.content
```

Das Spielchen kennen wir mittlerweile. Wir definieren einen Prompt, reichern ihn mit Inhalten an und übergeben ihn zusammen mit der System-Nachricht an das lokal gehostete LLM. Wir übergeben in diesem Fall im Prompt auch als Variable die maximale Anzahl von Token für die Response/Zusammenfassung und natürlich die Konversation, die wir zuvor zusammengesetzt haben.

Diese Funktion wird von der nun folgenden Funktion für das hierarchische Gedächtnis aufgerufen. Die ist im Grunde dem Menschen nachempfunden. Wir erinneren uns an die Kernthemen und -Entscheidungen des letzten Meetings, aber nicht an jeden gesagten Satz. 

Und das können wir vielfach einsetzen. Immer dann wenn die Gespräche länger werden. Ein Nachteil ist natürlich, dass es einen expliziten LLM-Call braucht. Und manchmal gehen dennoch wichtige Informationen verloren. Coding-Assistenten unterstützen solche Memory Compression Techniken übrigens auch häufig.

```python
def hierarchical_memory(all_turns: list, recent_count: int = 5):
    """
    Hierarchical memory:
    - Old messages: Compressed to summary
    - Recent messages: Kept in full
    """
    if len(all_turns) <= recent_count:
        return {
            "compressed_memory": "",
            "recent_messages": all_turns,
            "total_size": "small"
        }

    # Split: old vs recent
    old_turns = all_turns[:-recent_count]
    recent_turns = all_turns[-recent_count:]

    # Compress old turns
    compressed = compress_memory(old_turns, max_summary_tokens=150)

    return {
        "compressed_memory": compressed,
        "recent_messages": recent_turns,
        "total_size": f"{len(compressed)} chars summary + {len(recent_turns)} recent"
    }
```

Kommen wir nun zum Ergebnis. Für die kürzere Unterhaltung gibt es folgende Ausgabe:

```bash
============================================================
DAY 11: MEMORY COMPRESSION
============================================================

📊 Short Conversation: 10 Turns
   Uncompressed: ~693 chars

📝 Original Messages:
------------------------------------------------------------
  Turn 1 (planner): We should target First National Bank. It has lower security than expected.
  Turn 2 (hacker): I've analyzed their systems. They use an outdated alarm system from 2015.
  Turn 3 (safecracker): The vault is a TL-30 model. I need 45 minutes minimum to crack it.
  Turn 4 (mole): Actually, I think we need more time. Maybe 90 minutes to be safe?
  Turn 5 (planner): 90 minutes is too long. Let's stick with 60 minutes as buffer.
  Turn 6 (hacker): I can loop the security cameras for exactly 15 minutes before they notice.
  Turn 7 (safecracker): That's cutting it close. I need backup tools in case the drill jams.
  Turn 8 (mole): I can get you a keycard for the staff entrance. Less suspicious than breaking in.
  Turn 9 (planner): Good. We go in at 2 AM when the night shift is smallest.
  Turn 10 (hacker): I'll monitor police frequencies. If they get a call, we abort immediately.

🧠 Compressing old messages...

✅ Compressed Memory:
------------------------------------------------------------
Heist target: First National Bank (low security). Vault: TL-30 (45 min crack). Timeline: 60 min (buffer, compromise). Hacker can loop cameras (15 min). Mole offers staff keycard for less suspicious entry. Safecracker needs backup tools. Disagreement on time: 45 min (safecracker) vs. 90 min (mole), settled on 60 min.


📝 Recent Messages (kept in full):
------------------------------------------------------------
  Turn 9 (planner): Good. We go in at 2 AM when the night shift is smallest.
  Turn 10 (hacker): I'll monitor police frequencies. If they get a call, we abort immediately.

📦 Total Size: 318 chars summary + 2 recent
```

Aus etwa 700 Zeichen wurden schlanke 318 Wörter plus die zwei letzten Sätze. Zählt man das alles zusammen, hat man noch nicht besonders viel gewonnen, aber zum demonstrieren, wie es arbeitet sollte es passen und ist noch nachvollziehbar. Um aber zu zeigen, dass dieser Ansatz gut funktioniert, vor allem bei größerem Kontext, haben wir ja die noch längere Konversation. Und die ergibt sich zu:

```bash
============================================================
📊 EXTRA LONG Conversation: 100 Turns
   Uncompressed: ~4359 chars

🧠 Compressing old messages...

✅ Compressed Memory:
------------------------------------------------------------
A team plans a bank heist at First National Bank, targeting a vault with a potentially time-sensitive lock. The plan involves the hacker disabling alarms (10 min), the safecracker opening the vault (40+ min), and the mole providing inside access & distraction.  The team aims for a 2 AM entry, with a 20-minute window before police response.  They have backup plans for various contingencies, including abort signals ("midnight"), and a 2-day rehearsal schedule.  Escape involves a van two blocks away, with the hacker preparing for traffic manipulation and digital cleanup.


📝 Recent Messages (kept in full):
------------------------------------------------------------
  Turn 96 (mole): I'll bring the uniforms and keycards.
  Turn 97 (planner): Let's do a final walk-through tonight.
  Turn 98 (hacker): I'll check the alarm system one last time.
  Turn 99 (safecracker): I'll double-check my tools and bag.
  Turn 100 (mole): I'll make sure the coast is clear at 2am.

📦 Total Size: 575 chars summary + 5 recent
```

In diesem Fall wurden aus über 4000 Zeichen knapp 600 plus die 5 Sätze. Es ist also deutlich weniger Kontext, den ich zukünftig mitschleppen muss. Gerade bei lokalen LLMs wichtig. Und letztlich ähnelt es auch irgendwo dem menschlichen Verhalten.

## Zusammenfassung

Wir haben eine Art hierarchisches Gedächtnis zur Information Compression programmiert. Dieses Gedächtnis ähnelt in gewisser Weise unserem menschlichen Gehirn. Alte Sachen werden unscharf oder ganz vergessen, während die wichtigen und aktuellsten weiter im Gedächtnis bestehen bleiben. Für lange Gespräche mit LLMs ist das wirklich Gold wert. Man spart langfristig Token, Zeit und Geld, ohne den roten Faden zu verlieren.

Auf der anderen Seite kostet jede Komprimierung anfangs natürlich erstmal je einen LLM-Call. Langfristig wird es effizienter. Und für lokale LLMs mit wenig Speicher ist das oft die einzige Möglichkeit, längere Kontexte zu verarbeiten.

Konkret heißt das für unsere Agenten, sie könnten stundenlang planen, ohne dass das LLM überfordert wird oder wichtige Entscheidungen vergisst.

## Ausblick: Wo geht die Reise hin?

Was wir heute gebaut haben ist erst der Anfang. Memory Compression ist ein mächtiges Werkzeug, aber da geht noch mehr:

**Persistente Erinnerungen:** Die komprimierten Summaries gehören natürlich in die Datenbank! Wir haben ja schon gezeigt, wie wir Konversationen in SQLite speichern. Jetzt kommt einfach eine neue Tabelle für `compressed_memories` dazu, mit Timestamps und Session-IDs. Dann überlebt unser Agent-Gedächtnis auch Server-Neustarts und wir können sogar historische Trends analysieren.

**Semantische Komprimierung:** Statt nur zeitlich zu komprimieren, könnten wir auch thematisch clustern. Alle Diskussionen über "Sicherheitssysteme" in einen Block, "Zeitpläne" in einen anderen. So wird das Gedächtnis nicht nur kleiner, sondern auch strukturierter.

**Adaptive Komprimierung:** Je nach Wichtigkeit unterschiedlich stark komprimieren. Kritische Entscheidungen bleiben detailliert, Smalltalk wird aggressiv gekürzt. Das LLM könnte sogar selbst bewerten, was wichtig ist.

**Multi-Level Hierarchien:** Warum nur eine Ebene? Stunden-Summaries werden zu Tages-Summaries, die wiederum zu Wochen-Summaries. Wie unser Gehirn, das auch in verschiedenen Zeitebenen arbeitet.

**Fehlertoleranz:** Was passiert, wenn die Komprimierung mal daneben geht? Backup-Strategien, Validierung der Summaries, vielleicht sogar mehrere LLMs zur Qualitätskontrolle.

Das Schöne: All das lässt sich mit dem, was wir heute gebaut haben, erweitern. Unser hierarchisches Gedächtnis ist das Fundament für richtig clevere AI-Systeme. Systeme, die nicht nach ein paar Stunden "vergessen" haben, worum es überhaupt ging.