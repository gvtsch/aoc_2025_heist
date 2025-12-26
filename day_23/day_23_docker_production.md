---
title: "Tag 23: Docker Consolidation - Alles in einem System"
date: 2025-12-23
tags:
  - python
  - aoc
  - adventofcode
  - docker
  - microservices
  - production
toc: true
---

Alle Dokumente zu diesem Beitrag sind in meinem [repository](https://github.com/gvtsch/aoc_2025_heist/tree/main/day_23) zu finden.

Wir haben nun 22 Tage lang entwickelt und uns verschiedene Konzepte angesehen und in Python programmiert. Naja... Das Dashboard hat jemand anders für uns programmiert.
Und heute soll es nun darum gehen, wie man das System mit Docker produktionsbereit bekommt und mit nur einem einzigen Befehl starten kann.

## Ziel

Statt manuell 6 verschiedene Services zu starten (OAuth, Calculator, File Reader, Database Query, Memory und Dashboard), möchte ich das Ganze "produktionsreif" machen. Ich möchte nur `docker-compose up` ausführen.

Das klingt erstmal nach "nur Deployment", ist aber viel mehr. Ich habe dabei eine ganze Menge Bugs gefunden und gefixt, die Services synchronisiert und das System wirklich stabil gemacht. Das hat dann doch deutlich länger gedauert als ich dachte.

Aber der Aufwand hat sich gelohnt. Jetzt habe ich ein System, das so etwas wie "produktionsreif" ist. Schauen wir uns an, wie das Ganze aufgebaut ist.

## Docker Setup

Ich habe mich für Docker Compose entschieden, weil es perfekt für Multi-Container-Setups ist. Jeder Service läuft isoliert in seinem eigenen Container, aber alle können miteinander kommunizieren. Das hatten wir schon mal an Tag 6.

### Die Struktur

Jeder Service hat sein eigenes Dockerfile und läuft isoliert. Sie kommunizieren über ein Docker-Netzwerk miteinander.

```
docker-compose.yml          # Orchestriert alle 6 Services
├── oauth (Port 8001)       # JWT Token Service
├── calculator (8002)       # Math Operations
├── file-reader (8003)      # Document Access
├── database-query (8004)   # Security DB
├── memory (8005)           # Context Compression
└── dashboard (8008)        # Main Application + AI Detection
```

### `docker-compose.yml`

Die Datei ist das Herz des Systems. Hier ein Ausschnitt:

```yaml
version: '3.8'

services:
  oauth:
    build:
      context: .
      dockerfile: day_08/Dockerfile
    container_name: heist-oauth
    ports:
      - "8001:8001"
    networks:
      - heist-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/health"]
      interval: 10s
      timeout: 5s
      retries: 3

  dashboard:
    build:
      context: .
      dockerfile: day_22/Dockerfile
    container_name: heist-dashboard
    ports:
      - "8008:8008"
    environment:
      - DATABASE_PATH=/data/heist_analytics.db
      - LM_STUDIO_URL=http://host.docker.internal:1234/v1
    volumes:
      - heist-data:/data
    depends_on:
      oauth:
        condition: service_healthy
      calculator:
        condition: service_healthy
      # ... alle anderen Services
    networks:
      - heist-network

volumes:
  heist-data:
    driver: local

networks:
  heist-network:
    driver: bridge
```

Über das eine oder andere Hindernis bin ich gestolpert...

Das `depends_on` mit `condition: service_healthy` hat mir am meisten geholfen. Ohne das startet der Dashboard-Container sofort, auch wenn die anderen Services noch nicht bereit sind. Mit dem Health Check wartet Docker, bis wirklich alle Tools laufen und erreichbar sind. Das hat mir viele Probleme mit Race Conditions erspart.

Bei `host.docker.internal` war ich anfangs verwirrt. LM Studio läuft ja nicht in einem Container, sondern direkt auf meinem Rechner (Port 1234). Container können aber nicht einfach auf `localhost` des Hosts zugreifen. Mit `host.docker.internal` klappt das - Docker löst das automatisch zur richtigen Host-IP auf. Aber auch das kennen wir eigentlich schon von Tag 6.

Die `volumes` brauche ich für die Persistenz. Die SQLite-Datenbank mit allen Session-Daten liegt in `/data/heist_analytics.db` im Container. Ohne Volume wären die Daten bei jedem Container-Neustart weg. Mit dem Volume `heist-data:/data` bleiben alle Heist-Statistiken erhalten - auch über Restarts und Rebuilds hinweg.

## Die Dockerfiles

Jeder Service braucht sein eigenes Dockerfile. Hier ein Beispiel für den Calculator:

```dockerfile
# day_13/Dockerfile.calculator
FROM python:3.11-slim

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY day_13/tool_service.py .

ENV PYTHONUNBUFFERED=1
ENV PORT=8002

EXPOSE 8002

HEALTHCHECK --interval=10s --timeout=5s --retries=3 \
  CMD curl -f http://localhost:8002/health || exit 1

CMD ["python", "tool_service.py"]
```

Der Health Check ist entscheidend. Ohne den würde der Dashboard-Container zu früh starten und Verbindungsfehler bekommen. Und ich habe im Laufe der Zeit einige Fehler bekommen ;)

## Bugs beim Dockerisieren

Beim Zusammenbau sind mir etliche Bugs aufgefallen, die lokal nicht auffielen. Docker zwingt einen dazu, sehr präzise zu sein,  was gut ist! Hier eine Zusammenfassung der wichtigsten Probleme:

* **Endpoint-Pfade:** Config und Services hatten unterschiedliche Pfade (`/tools/read_file` vs. `/tools/file_reader`). Resultat: 404 Fehler.
* **Doppelte Nachrichten:** Jede Message wurde zweimal in die DB geschrieben, vom Agent und vom Dashboard. Der Message Counter zählte dadurch immer das Doppelte.
* **Session Completion:** Sessions wurden nie als 'completed' markiert. Die Completion Rate blieb bei 0%, egal wie viele Heists ich durchlaufen ließ.
* **Tool Usage Detection:** Die ursprüngliche Logik "Fehler = verdächtig" war unfair. Zufällige 404er machten unschuldige Agents verdächtig. Ich habe das umgedreht: Perfekte Success Rates (95%+) sind jetzt verdächtig, weil der Mole zu vorsichtig agiert. Aber hier gibt es auch noch reichlich Verbesserungspotenzial.
* **Database Schema:** Spalten-Namen stimmten nicht (`num_turns` vs. `total_turns`), JWT-Secrets waren unterschiedlich, Token-Felder inkonsistent. Typische Integration-Probleme eben.

Die kompletten Fixes kannst du dir im Repository ansehen. Jeder Bug war eine gute Lektion in Service-Integration und hat das System deutlich robuster gemacht.

## Starten & Nutzen

Und wie startet man das Ganze?

Eigentlich ganz einfach: Erst LM Studio öffnen, ein Modell laden (idealerweise das Modell, das in der Konfig angegeben ist) und den Server auf Port 1234 starten. Dann im Terminal `docker-compose up --build` ausführen. Beim ersten Mal baut Docker alle Container, das dauert ein paar Minuten. Danach Browser und URL `http://localhost:8008` öffnen und los geht's.

Im Dashboard auf "Start New Heist" klicken, und die 6 Agents fangen an zu planen. Man sieht in Echtzeit, wie sie kommunizieren, welche Tools sie nutzen, und die AI analysiert im Hintergrund jede Nachricht. Am Ende kann man tippen, wer der Maulwurf ist. 

Die AI gibt mir Hinweise. Zu perfekte Tool-Nutzung (95%+ Success Rate) ist verdächtig, widersprüchliche Zeitangaben oder zögerliche Sprache. Aber die finale Entscheidung liegt beim Nutzer. Aber auch hier gibt es noch einiges zu verbessern. Die Logik ist noch nicht ganz ausgereift.

Falls was nicht klappt: Meist liegt's daran, dass LM Studio nicht läuft oder die Container noch nicht fertig hochgefahren sind. Mit `docker-compose logs dashboard` kann ich sehen, was los ist.

## Was ich gelernt habe

Die Docker-Integration war lehrreicher als gedacht. Klar, technisch ist es "nur" ein paar Dockerfiles schreiben und eine Compose-Datei zusammenstellen. Aber in Wirklichkeit hat mich Docker gezwungen, über Dinge nachzudenken, die in der lokalen Entwicklung einfach funktioniert haben.

* **Health Checks sind nicht optional.** Ich dachte anfangs, `depends_on` würde reichen. Service A startet nach Service B, fertig. Naja... "Gestartet" heißt nicht "bereit". Der Dashboard-Container hat sofort versucht, den Calculator zu erreichen, während der noch am Booten war. Mit `condition: service_healthy` wartet Docker wirklich, bis der Service antwortet.
* **Service Discovery war verwirrend.** In meinem lokalen Setup war alles `localhost:800X`. In Docker ist jeder Container sein eigenes kleines System. `localhost` zeigt in den Container selbst, nicht auf die anderen Services. Die Lösung ist simpel: Service-Namen verwenden (`http://calculator:8002`). Docker löst das intern auf. Aber das zu verstehen hat gedauert.
* **Volumes sind Pflicht für dauerhafte Daten.** Die SQLite-Datenbank lag anfangs direkt im Container. Wird der Container neu gestartet, sind alle Heist-Daten weg. Mit dem Volume `heist-data:/data` bleiben die Daten erhalten. Klingt trivial, aber ich hab's beim ersten Versuch vergessen und mich gewundert, warum meine Test-Sessions verschwinden.
* **Docker zeigt Integrationsprobleme schonungslos.** Lokal hab ich die Services manuell gestartet, in beliebiger Reihenfolge. Wenn was nicht ging, hab ich neu gestartet. In Docker muss alles sauber orchestriert sein. Reihenfolge, Dependencies und Configs. Das hat mir einige Bugs gezeigt: Zum Beispiel Endpoint-Mismatch, doppelte Message-Speicherung und fehlende Session-Completion. Alles Dinge, die in meinem chaotischen lokalen Setup irgendwie funktioniert haben, aber eigentlich kaputt waren.
* **Debugging ist anders.** Kein einfaches Print-Statement mehr, das ich im Terminal sehe. Ich musste lernen, mit `docker-compose logs -f` zu arbeiten, in Container reinzuspringen (`docker exec -it`), die Datenbank direkt im Container zu checken. Am Anfang frustrierend, aber eigentlich viel systematischer als mein lokales Chaos.
* **Centralized Auth ist genial.** Jeder Tool-Service nutzt denselben OAuth-Service. Kein Service macht Auth selbst. Das bedeutet: JWT-Secret nur an einer Stelle ändern, die Scopes zentral verwalten und die Token-Logik einmal richtig implementieren. 

## Fazit

Tag 23 hat aus einem Entwicklungs-Setup ein "produktionsreifes" System gemacht. So weit man das für unser konstruiertes Projekt überhaupt so sagen kann. 

* **Ein Befehl**: `docker-compose up` und alles läuft
* **6 Microservices**: Alle isoliert und gesund
* **OAuth Security**: Token-basierte Authentifizierung
* **Persistenz**: Datenbank überlebt Restarts
* **6 Agents**: Komplexere Heist-Szenarien
* **AI Detection**: RAG-basierte Mole-Erkennung
* **Observability**: Logs, Health Checks, Metrics

Ich habe beim Dockerisieren etliche Bugs gefunden und gefixt, die vorher versteckt waren. Das, und alles was ich noch dazu gelernt habe, war fast wertvoller als das Docker-Setup selbst!
